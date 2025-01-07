from pyseto import Key, Paseto
import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import base64

def verify_token(token, message):
    # Pastikan message adalah string
    if not isinstance(message, str):
        message = str(message)  # Ubah menjadi string jika bukan string
    
    print(f"Message type: {type(message)}")  # Debugging untuk memeriksa tipe message
    print(f"Message to verify: {message}")  # Debugging pesan yang akan diverifikasi

    # Menambahkan padding jika panjang token tidak kelipatan 4
    padding = len(token) % 4
    if padding != 0:
        # Menambahkan padding '=' dalam bentuk bytes, bukan string
        token += b"=" * (4 - padding)  # Padding dalam bentuk bytes

    # Mengonversi token dari Base64 ke bytes
    try:
        token_bytes = base64.b64decode(token)
    except Exception as e:
        print(f"Error decoding base64 token: {e}")
        return False

    public_key_path = os.getenv("PUBLIC_KEY_PATH")

    # Membaca kunci publik ECDSA
    with open(public_key_path, "rb") as f:
        public_key_pem = f.read()

    # Memuat kunci publik
    public_key = serialization.load_pem_public_key(public_key_pem)

    try:
        # Menggunakan Paseto tanpa argumen version dan purpose
        paseto = Paseto.new()

        # Decode token menggunakan kunci publik
        decoded_message = paseto.decode(public_key, token_bytes)  # Decode token using the public key

        # Mengambil signature dari token Paseto
        signature = decoded_message  # signature adalah byte yang sudah terverifikasi
        print(f"Decoded signature: {signature}")

        # Memverifikasi tanda tangan menggunakan kunci publik ECDSA
        message_bytes = message.encode('utf-8')  # Konversi message ke bytes sebelum verifikasi

        # Verifikasi tanda tangan dengan ECDSA dan SHA256
        public_key.verify(
            signature,  # Tanda tangan sudah dalam bentuk byte
            message_bytes,  # Pesan juga harus dalam bentuk byte
            ec.ECDSA(hashes.SHA256())
        )
        return True

    except Exception as e:
        print(f"Error verifying signature: {e}")
        return False
