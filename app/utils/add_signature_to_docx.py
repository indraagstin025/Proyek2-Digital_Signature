from flask import Flask, request, jsonify, send_file
from app.utils.verify_signature import verify_signature
from app.utils.add_signature_to_docx import add_signature_to_docx  
from PyPDF2 import PdfReader, PdfWriter

app = Flask(__name__)

@app.route('/add_signature_docx', methods=['POST'])
def add_signature_docx():
    # Ambil data dari request
    message = request.json.get('message')
    signature = request.json.get('signature')
    docx_path = request.json.get('docx_path')  # Path ke dokumen DOCX asli
    output_docx = "signed_document.docx"  # Path untuk menyimpan dokumen yang sudah ditandatangani

    # Verifikasi tanda tangan
    if not message or not signature:
        return jsonify({"error": "Message and signature are required"}), 400

    if not verify_signature(message, signature):
        return jsonify({"error": "Invalid signature"}), 400

    # Menambahkan tanda tangan ke dokumen DOCX
    add_signature_to_docx(docx_path, signature, output_docx)

    # Mengirimkan file DOCX hasil yang sudah ditandatangani
    return send_file(output_docx, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
