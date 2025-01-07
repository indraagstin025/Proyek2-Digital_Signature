import os
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
from dotenv import load_dotenv

# Muat variabel lingkungan dari file .env
load_dotenv()

def verify_signature(message, signature):
    # Ambil path public key dari .env
    public_key_path = os.getenv("PUBLIC_KEY_PATH")
    
    if not public_key_path or not os.path.exists(public_key_path):
        raise FileNotFoundError("Public key file tidak ditemukan. Pastikan path benar.")
    
    with open(public_key_path, "rb") as public_file:
        public_key_bytes = public_file.read()
    
    verify_key = VerifyKey(public_key_bytes)

    try:
        # Verifikasi tanda tangan
        verify_key.verify(message.encode("utf-8"), bytes.fromhex(signature))
        print("Tanda tangan valid.")
        return True
    except BadSignatureError:
        print("Tanda tangan tidak valid!")
        return False
    except Exception as e:
        raise RuntimeError(f"Terjadi kesalahan saat memverifikasi tanda tangan: {e}")
