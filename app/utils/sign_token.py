from pyseto import Key, Paseto
import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import base64

def sign_token(message):
    # Pastikan message adalah tipe string atau integer
    if isinstance(message, int):
        message = str(message)  # Konversi integer ke string
    elif not isinstance(message, str):
        raise TypeError("Pesan harus berupa string atau integer")  # Validasi jika bukan str atau int

    # Membaca kunci privat ECDSA dalam format PEM
    private_key_path = os.getenv("PRIVATE_KEY_PATH")
    if not os.path.exists(private_key_path):
        raise FileNotFoundError(f"Kunci privat tidak ditemukan di path: {private_key_path}")

    with open(private_key_path, "rb") as f:
        private_key_pem = f.read()

    # Memuat kunci privat dari format PEM
    private_key = serialization.load_pem_private_key(private_key_pem, password=None)

    try:
        # Pastikan pesan yang diberikan sudah dalam bentuk string dan encode menjadi byte
        signature = private_key.sign(
            message.encode(),  # Pesan harus diencode menjadi bytes
            ec.ECDSA(hashes.SHA256())
        )
        print("Pesan berhasil ditandatangani.")
    except Exception as e:
        print(f"Error during signing: {e}")
        raise RuntimeError(f"Terjadi kesalahan saat menandatangani pesan: {e}")

    # Menggunakan kunci privat dalam format PEM untuk Paseto
    key = Key.new(version=3, purpose="public", key=private_key_pem)  # Memasukkan kunci PEM untuk Paseto

    # Membuat token Paseto
    token = Paseto.new()
    signed_token = token.encode(key, signature)  # Tanda tangan (signature) sudah berupa byte

    return signed_token
