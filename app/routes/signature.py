from flask import Blueprint, request, jsonify
from app.utils.sign_token import sign_token
from app.utils.verify_token import verify_token
from flask_login import login_required, current_user
import base64
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

# Blueprint untuk signature
signature_bp = Blueprint('signature', __name__)

# Endpoint untuk membuat tanda tangan (sign)
from flask_login import current_user

@signature_bp.route('/sign', methods=['POST'])
def save_signature():
    if not current_user.is_authenticated:
        # Kembalikan JSON jika pengguna tidak terautentikasi
        return jsonify({"error": "Pengguna tidak terautentikasi"}), 401

    try:
        data = request.json.get('data')
        doc_id = request.json.get('doc_id')

        if not data or not doc_id:
            return jsonify({"error": "Data atau ID dokumen tidak valid"}), 400


        token = sign_token(data)
        return jsonify({"message": "Tanda tangan berhasil dibuat", "token": token}), 200
    except Exception as e:
        return jsonify({"error": f"Terjadi kesalahan: {e}"}), 500


# Endpoint untuk memverifikasi tanda tangan (verify)
@signature_bp.route('/verify', methods=['POST'])
def verify_signature():
    try:
        # Ambil data dari request
        token = request.json.get('token')
        message = request.json.get('message')

        # Validasi data
        if not token or not message:
            logging.error("Token atau pesan tidak valid")
            return jsonify({"error": "Token atau pesan tidak valid"}), 400

        # Verifikasi tanda tangan
        is_valid = verify_token(token, message)
        if is_valid:
            logging.info("Tanda tangan valid")
            return jsonify({"message": "Tanda tangan valid"}), 200
        else:
            logging.warning("Tanda tangan tidak valid")
            return jsonify({"error": "Tanda tangan tidak valid"}), 400
    except Exception as e:
        logging.error(f"Terjadi kesalahan saat memverifikasi tanda tangan: {e}")
        return jsonify({"error": f"Terjadi kesalahan: {e}"}), 500

