import os
from nacl.signing import SigningKey
from dotenv import load_dotenv

# Muat variabel lingkungan dari file .env
load_dotenv()

def sign_data(message):
    # Ambil path private key dari .env
    private_key_path = os.getenv("PRIVATE_KEY_PATH")
    
    if not private_key_path or not os.path.exists(private_key_path):
        raise FileNotFoundError("Private key file tidak ditemukan. Pastikan path benar.")
    
    with open(private_key_path, "rb") as private_file:
        private_key_bytes = private_file.read()
    
    private_key = SigningKey(private_key_bytes)

    # Tanda tangani data
    try:
        signed_message = private_key.sign(message.encode("utf-8"))
        print("Data berhasil ditandatangani.")
        return signed_message
    except Exception as e:
        raise RuntimeError(f"Terjadi kesalahan saat menandatangani data: {e}")
