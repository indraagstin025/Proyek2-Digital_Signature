from flask import Blueprint, request, jsonify, send_file
from app.utils.sign_token import sign_token
from app.utils.verify_token import verify_token
from app.utils.qr_utils import generate_qr_code
from app.utils.add_signature_to_pdf import add_signature_to_pdf
from flask_login import login_required, current_user
from app.models import Signature, Document
from app.extensions import db
from PIL import Image
from io import BytesIO
import base64
import os
import logging

logging.basicConfig(level=logging.INFO)

signature_bp = Blueprint('signature', __name__)

SIGNATURE_FOLDER = os.path.abspath("app/static/signatures")

if not os.path.exists(SIGNATURE_FOLDER):
    os.makedirs(SIGNATURE_FOLDER, exist_ok=True)
    logging.info(f"Folder signature berhasil dibuat di {SIGNATURE_FOLDER}")

def save_signature_image(signature_data, document_hash):
    try:
        if not signature_data.startswith("data:image/"):
            raise ValueError("Format Base64 tidak valid atau tidak sesuai untuk gambar.")

        base64_data = signature_data.split(",")[1]
        missing_padding = len(base64_data) % 4
        if missing_padding:
            base64_data += "=" * (4 - missing_padding)

        img_data = base64.b64decode(base64_data)
        img = Image.open(BytesIO(img_data))

        signature_filename = f"{document_hash}_signature.png"
        signature_path = os.path.join(SIGNATURE_FOLDER, signature_filename)

        img.save(signature_path)
        logging.info(f"Tanda tangan disimpan di: {signature_path}")
        return signature_path
    except Exception as e:
        logging.error(f"Gagal menyimpan tanda tangan: {e}")
        raise Exception(f"Terjadi kesalahan saat menyimpan tanda tangan: {e}")

def validate_request_data(data, required_fields):
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return False, f"Missing fields: {', '.join(missing_fields)}"
    return True, None

@signature_bp.route('/add-signature', methods=['POST'])
@login_required
def add_signature():
    try:
        data = request.json
        document_hash = data.get("document_hash")
        signature_data = data.get("signature")

        if not document_hash or not signature_data:
            return jsonify({"error": "Data tidak lengkap. Diperlukan document_hash dan signature."}), 400

        document = Document.query.filter_by(doc_hash=document_hash).first_or_404()
        if document.user_id != current_user.id:
            return jsonify({"error": "Anda tidak memiliki izin untuk dokumen ini."}), 403

        # Simpan tanda tangan sebagai file gambar
        signature_path = save_signature_image(signature_data, document_hash)

        # Generate token untuk tanda tangan
        message_to_sign = f"Tanda tangan untuk dokumen: {document.filename}, oleh {current_user.email}"
        token = sign_token(message_to_sign)

        # Generate QR Code
        qr_code_path = os.path.join(SIGNATURE_FOLDER, f"{document_hash}_qr.png")
        generate_qr_code(token, qr_code_path)

        # Simpan tanda tangan ke database
        signature = Signature.create_signature(
            document_hash=document_hash,
            user_id=current_user.id,
            token=token,
            signer_email=current_user.email,
            document_name=document.filename
        )

        # Simpan path QR Code ke database
        signature.qr_code_path = qr_code_path
        db.session.commit()

        return jsonify({
            "message": "Tanda tangan berhasil ditambahkan.",
            "signature_path": signature_path,
            "qr_code_path": qr_code_path,
            "token": token  # Kembalikan token yang dihasilkan
        }), 201

    except Exception as e:
        logging.error(f"Terjadi kesalahan: {e}")
        return jsonify({"error": f"Terjadi kesalahan: {str(e)}"}), 500


@signature_bp.route('/create', methods=['POST'])
def create_signature():
    try:
        data = request.json
        is_valid, error_message = validate_request_data(data, ["doc_hash"])
        if not is_valid:
            return jsonify({"error": error_message}), 400

        document_hash = data["doc_hash"]

        # Ambil dokumen dari database
        document = Document.query.filter_by(doc_hash=document_hash).first_or_404()

        # Format pesan untuk ditandatangani
        message_to_sign = f"Tanda tangan untuk dokumen: {document.filename}, oleh {current_user.email}"

        # Generate token
        token = sign_token(message_to_sign)

        # Simpan token di database
        signature = Signature.create_signature(
            document_hash=document_hash,
            user_id=current_user.id,
            token=token,
            signer_email=current_user.email,
            document_name=document.filename
        )

        return jsonify({"message": "Tanda tangan berhasil dibuat", "token": token}), 201

    except Exception as e:
        logging.error(f"Terjadi kesalahan saat membuat tanda tangan: {e}")
        return jsonify({"error": f"Terjadi kesalahan: {str(e)}"}), 500


@signature_bp.route('/check', methods=['POST'])
def check_signature():
    try:
        data = request.json
        is_valid, error_message = validate_request_data(data, ["token"])
        if not is_valid:
            return jsonify({"error": error_message}), 400

        # Ambil token dari permintaan
        token = data["token"]
        signature = Signature.query.filter_by(token=token).first()

        if not signature:
            logging.warning(f"Token tidak ditemukan di database: {token}")
            return jsonify({"error": "Token tidak ditemukan"}), 404

        # Pesan yang diharapkan
        expected_message = f"Tanda tangan untuk dokumen: {signature.document_name}, oleh {signature.signer_email}"
        logging.info(f"Memverifikasi token: {token} untuk pesan: {expected_message}")

        # Verifikasi token
        if verify_token(token, expected_message):
            return jsonify({
                "message": "Tanda tangan valid",
                "document_name": signature.document_name,
                "signed_by": signature.signer_email,
                "timestamp": str(signature.timestamp)
            }), 200
        else:
            logging.warning("Tanda tangan tidak valid.")
            return jsonify({"error": "Tanda tangan tidak valid"}), 400

    except Exception as e:
        logging.error(f"Kesalahan saat memverifikasi tanda tangan: {e}")
        return jsonify({"error": f"Terjadi kesalahan: {str(e)}"}), 500



@signature_bp.route('/view-qr/<string:document_hash>', methods=['GET'])
@login_required
def view_qr_code(document_hash):
    try:
        logging.info(f"Menerima permintaan QR Code untuk dokumen dengan hash: {document_hash}")

        # Ambil tanda tangan berdasarkan hash dokumen
        signature = Signature.query.filter_by(document_hash=document_hash).first_or_404()

        logging.info(f"Tanda tangan ditemukan: {signature}")

        # Validasi izin pengguna
        if signature.user_id != current_user.id:
            logging.warning(f"User {current_user.id} tidak memiliki izin untuk QR Code dokumen {document_hash}")
            return jsonify({"error": "Anda tidak memiliki izin untuk QR Code ini."}), 403

        # Cek path QR Code
        if not signature.qr_code_path:
            logging.error("Path QR Code kosong di database.")
            return jsonify({"error": "QR Code tidak ditemukan di database."}), 404
        if not os.path.exists(signature.qr_code_path):
            logging.error(f"QR Code tidak ditemukan di path: {signature.qr_code_path}")
            return jsonify({"error": "QR Code tidak ditemukan"}), 404

        logging.info(f"QR Code ditemukan di path: {signature.qr_code_path}")

        # Kirim file QR Code
        return send_file(signature.qr_code_path, mimetype='image/png')

    except Exception as e:
        logging.error(f"Terjadi kesalahan saat mengakses QR Code untuk dokumen {document_hash}: {e}")
        return jsonify({"error": f"Terjadi kesalahan: {str(e)}"}), 500


@signature_bp.route('/get-token/<string:document_hash>', methods=['GET'])
@login_required
def get_token(document_hash):
    try:
        logging.info(f"Menerima permintaan token untuk dokumen dengan hash: {document_hash}")

        # Validasi dokumen berdasarkan hash
        document = Document.query.filter_by(doc_hash=document_hash).first_or_404()
        logging.info(f"Dokumen ditemukan: {document.filename}")

        if document.user_id != current_user.id:
            logging.warning(f"User {current_user.id} tidak memiliki izin untuk dokumen {document_hash}")
            return jsonify({"error": "Anda tidak memiliki izin untuk dokumen ini."}), 403

        # Ambil tanda tangan berdasarkan hash dokumen
        signature = Signature.query.filter_by(document_hash=document_hash).first()
        if not signature:
            logging.warning(f"Tanda tangan tidak ditemukan untuk dokumen {document_hash}")
            return jsonify({"error": "Token tidak ditemukan untuk dokumen ini."}), 404

        # Validasi token
        if not signature.token:
            logging.error("Token kosong ditemukan di database.")
            return jsonify({"error": "Token belum dihasilkan untuk dokumen ini."}), 404

        logging.info(f"Token ditemukan untuk dokumen {document_hash}: {signature.token}")

        # Kembalikan respons
        return jsonify({
            "token": signature.token,
            "document_name": signature.document_name,
            "signed_by": signature.signer_email,
            "timestamp": str(signature.timestamp)
        }), 200

    except Exception as e:
        logging.error(f"Kesalahan saat mengambil token untuk dokumen {document_hash}: {e}")
        return jsonify({"error": f"Terjadi kesalahan: {str(e)}"}), 500


@signature_bp.route('/generate-signed-doc/<string:document_hash>', methods=['GET'])
@login_required
def generate_signed_doc(document_hash):
    try:
        document = Document.query.filter_by(doc_hash=document_hash).first_or_404()
        signature = Signature.query.filter_by(document_hash=document_hash).first()

        if not signature:
            return jsonify({"error": "Tanda tangan tidak ditemukan"}), 404

        if document.user_id != current_user.id:
            return jsonify({"error": "Anda tidak memiliki izin untuk dokumen ini."}), 403

        pdf_path = document.filepath
        qr_code_path = signature.qr_code_path
        output_path = os.path.join(SIGNATURE_FOLDER, f"{document_hash}_signed.pdf")

        add_signature_to_pdf(pdf_path, qr_code_path, output_path)

        return send_file(output_path, as_attachment=True)

    except Exception as e:
        logging.error(f"Terjadi kesalahan saat membuat dokumen bertanda tangan: {e}")
        return jsonify({"error": f"Terjadi kesalahan: {str(e)}"}), 500

@signature_bp.route('/delete-signatures', methods=['POST'])
@login_required
def delete_signatures():
    try:
        signatures = Signature.query.all()
        for signature in signatures:
            if signature.qr_code_path and os.path.exists(signature.qr_code_path):
                os.remove(signature.qr_code_path)

        Signature.query.delete()
        db.session.commit()

        db.session.execute("ALTER TABLE signature AUTO_INCREMENT = 1")
        db.session.commit()

        return jsonify({"message": "Semua tanda tangan berhasil dihapus dan AUTO_INCREMENT direset."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Terjadi kesalahan: {str(e)}"}), 500
