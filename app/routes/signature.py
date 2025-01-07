from flask import Blueprint, request, jsonify
from app.utils.sign_token import sign_token
from app.utils.verify_token import verify_token
import base64
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

# Blueprint untuk signature
signature_bp = Blueprint('signature', __name__)

# Endpoint untuk membuat tanda tangan (sign)


@signature_bp.route('/sign', methods=['POST'])
def save_signature():
    """
    Endpoint untuk membuat tanda tangan (token) berdasarkan data yang diterima.
    """
    try:
        data = request.json.get('data')
        doc_id = request.json.get('doc_id')

        logging.info(f"Data yang diterima: {data}")
        logging.info(f"Document ID: {doc_id}")

        if not data or not doc_id:
            return jsonify({"error": "Data atau ID dokumen tidak valid"}), 400

        # Memastikan bahwa 'data' adalah string
        if isinstance(data, int):
            data = str(data)  # Konversi integer ke string jika perlu

        logging.info(f"Data yang akan ditandatangani: {data}")

        # Buat token Paseto
        token = sign_token(data)

        # Mengonversi token ke dalam format Base64 untuk serialisasi JSON
        token_base64 = base64.b64encode(token).decode('utf-8')  # Mengonversi bytes menjadi string

        logging.info(f"Token berhasil dibuat untuk dokumen ID {doc_id}")

        return jsonify({"message": "Tanda tangan berhasil dibuat", "token": token_base64}), 200

    except FileNotFoundError as e:
        logging.error(f"File tidak ditemukan: {e}")
        return jsonify({"error": "File tidak ditemukan"}), 500






# Endpoint untuk memverifikasi tanda tangan (verify)
@signature_bp.route('/verify', methods=['POST'])
def verify_signature():
    """
    Endpoint untuk memverifikasi tanda tangan (token) yang diterima.
    """
    try:
        # Ambil token dan pesan dari request JSON
        token_base64 = request.json.get('token')
        message = request.json.get('message')

        if not token_base64 or not message:
            return jsonify({"error": "Token atau pesan tidak valid"}), 400

        # Menambahkan padding jika panjang token tidak kelipatan 4
        padding = len(token_base64) % 4
        if padding != 0:
            token_base64 += "=" * (4 - padding)  # Menambahkan padding '=' dalam bentuk string

        # Mengonversi token dari Base64 ke bytes
        try:
            token = base64.b64decode(token_base64)
        except Exception as e:
            logging.error(f"Error decoding base64 token: {e}")
            return jsonify({"error": f"Invalid base64 token: {e}"}), 400

        # Verifikasi token
        is_valid = verify_token(token, message)
        if is_valid:
            logging.info("Tanda tangan valid")
            return jsonify({"message": "Tanda tangan valid"}), 200
        else:
            logging.warning("Tanda tangan tidak valid")
            return jsonify({"error": "Tanda tangan tidak valid"}), 400

    except FileNotFoundError as e:
        logging.error(f"Kunci tidak ditemukan: {e}")
        return jsonify({"error": f"Kunci tidak ditemukan: {e}"}), 500

    except Exception as e:
        logging.error(f"Terjadi kesalahan saat memverifikasi tanda tangan: {e}")
        return jsonify({"error": f"Terjadi kesalahan: {e}"}), 500
