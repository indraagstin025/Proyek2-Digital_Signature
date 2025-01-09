from flask import Blueprint, request, jsonify, send_file
from app.utils.sign_token import sign_token
from app.utils.verify_token import verify_token
from app.utils.qr_utils import generate_qr_code
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


def save_signature_image(signature_data, doc_id):
    """
    Menyimpan tanda tangan dari canvas (base64) menjadi file gambar.
    """
    try:
        # Validasi awal untuk memastikan format Base64
        if not signature_data.startswith("data:image/"):
            raise ValueError("Format Base64 tidak valid atau tidak sesuai untuk gambar.")

        # Decode Base64 data menjadi gambar
        base64_data = signature_data.split(",")[1]

        # Tambahkan padding jika diperlukan
        missing_padding = len(base64_data) % 4
        if missing_padding:
            base64_data += "=" * (4 - missing_padding)

        img_data = base64.b64decode(base64_data)
        img = Image.open(BytesIO(img_data))

        # Tentukan lokasi file untuk menyimpan gambar tanda tangan
        signature_filename = f"{doc_id}_signature.png"
        signature_path = os.path.join(SIGNATURE_FOLDER, signature_filename)

        # Simpan gambar tanda tangan
        img.save(signature_path)
        logging.info(f"Tanda tangan disimpan di: {signature_path}")
        return signature_path
    except Exception as e:
        logging.error(f"Gagal menyimpan tanda tangan: {e}")
        raise Exception(f"Terjadi kesalahan saat menyimpan tanda tangan: {e}")




def validate_request_data(data, required_fields):
    """
    Validates request data against a list of required fields.
    """
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return False, f"Missing fields: {', '.join(missing_fields)}"
    return True, None


@signature_bp.route('/add-signature', methods=['POST'])
@login_required  # Tetap menggunakan dekorator login_required
def add_signature():
    try:
        data = request.json
        print(f"DEBUG: Data diterima - {data}")
        doc_id = data.get("doc_id")
        signature_data = data.get("signature")

        if not doc_id or not signature_data:
            return jsonify({"error": "Data tidak lengkap. Diperlukan doc_id dan signature."}), 400

        # Validasi dokumen
        document = Document.query.get_or_404(doc_id)
        if document.user_id != current_user.id:  # Periksa sesi pengguna
            return jsonify({"error": "Anda tidak memiliki izin untuk dokumen ini."}), 403

        # Simpan tanda tangan
        signature_path = save_signature_image(signature_data, doc_id)

        # Simpan ke database
        new_signature = Signature(
            document_id=doc_id,
            user_id=current_user.id,
            token="",  # Token dapat ditambahkan jika diperlukan
            status="signed"
        )
        new_signature.qr_code_path = signature_path
        db.session.add(new_signature)
        db.session.commit()

        return jsonify({"message": "Tanda tangan berhasil ditambahkan.", "signature_path": signature_path}), 201
    except Exception as e:
        print(f"DEBUG: Terjadi kesalahan - {e}")
        return jsonify({"error": f"Terjadi kesalahan: {str(e)}"}), 500





@signature_bp.route('/create', methods=['POST'])
def create_signature():
    try:
        data = request.json
        is_valid, error_message = validate_request_data(data, ["data", "doc_id"])
        
        if not is_valid:
            return jsonify({"error": error_message}), 400

        # Proses pembuatan tanda tangan
        token = sign_token(data["data"])
        logging.info(f"Tanda tangan berhasil dibuat untuk doc_id {data['doc_id']}")
        return jsonify({"message": "Tanda tangan berhasil dibuat", "token": token}), 201
    except Exception as e:
        logging.error(f"Terjadi kesalahan: {e}")
        return jsonify({"error": f"Terjadi kesalahan: {e}"}), 500


@signature_bp.route('/check', methods=['POST'])
def check_signature():
    try:
        data = request.json
        is_valid, error_message = validate_request_data(data, ["token", "message"])
        
        if not is_valid:
            logging.error(error_message)
            return jsonify({"error": error_message}), 400

        # Proses verifikasi tanda tangan
        if verify_token(data["token"], data["message"]):
            logging.info("Tanda tangan valid")
            return jsonify({"message": "Tanda tangan valid"}), 200
        else:
            logging.warning("Tanda tangan tidak valid")
            return jsonify({"error": "Tanda tangan tidak valid"}), 400
    except Exception as e:
        logging.error(f"Terjadi kesalahan saat memverifikasi tanda tangan: {e}")
        return jsonify({"error": f"Terjadi kesalahan: {e}"}), 500


@signature_bp.route('/view-qr/<int:signature_id>', methods=['GET'])
@login_required  # Hanya validasi sesi pengguna
def view_qr_code(signature_id):
    signature = Signature.query.get_or_404(signature_id)

    if signature.user_id != current_user.id:  # Validasi akses berdasarkan sesi
        return jsonify({"error": "Anda tidak memiliki izin untuk QR Code ini."}), 403

    if not signature.qr_code_path or not os.path.exists(signature.qr_code_path):
        return jsonify({"error": "QR Code tidak ditemukan"}), 404

    return send_file(signature.qr_code_path, mimetype='image/png')


@signature_bp.route('/get-token/<int:doc_id>', methods=['GET'])
@login_required
def get_token(doc_id):
    """
    Endpoint untuk mengambil token berdasarkan doc_id.
    """
    try:
        document = Document.query.get_or_404(doc_id)
        if document.user_id != current_user.id:
            return jsonify({"error": "Anda tidak memiliki izin untuk dokumen ini."}), 403

        signature = Signature.query.filter_by(document_id=doc_id).first()
        if not signature:
            return jsonify({"error": "Token tidak ditemukan untuk dokumen ini."}), 404

        return jsonify({"token": signature.token}), 200
    except Exception as e:
        logging.error(f"Kesalahan saat mengambil token: {e}")
        return jsonify({"error": f"Terjadi kesalahan: {str(e)}"}), 500

