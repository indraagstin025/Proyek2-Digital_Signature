from flask import Blueprint, request, jsonify
from app.utils.sign_data import sign_data  # Import fungsi sign_data
from app.utils.verify_signature import verify_signature  # Import fungsi verify_signature

signature_bp = Blueprint("signature", __name__)

@signature_bp.route("/api/sign", methods=["POST"])
def sign():
    data = request.json.get("data", "")
    if not data:
        return jsonify({"error": "Data tidak boleh kosong"}), 400
    
    signed_message = sign_data(data)  # Menandatangani data
    return jsonify({
        "data": data,
        "signature": signed_message.signature.hex(),
        "message_with_signature": signed_message.hex()
    })

@signature_bp.route("/api/verify", methods=["POST"])
def verify():
    data = request.json.get("data", "")
    signature = request.json.get("signature", "")
    if not data or not signature:
        return jsonify({"error": "Data dan tanda tangan tidak boleh kosong"}), 400

    verification_result = verify_signature(data, signature)  # Memverifikasi tanda tangan
    if verification_result:
        return jsonify({"message": "Tanda tangan valid"})
    else:
        return jsonify({"message": "Tanda tangan tidak valid!"}), 400

