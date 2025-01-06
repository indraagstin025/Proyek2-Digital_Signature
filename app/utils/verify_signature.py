import os
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
from dotenv import load_dotenv

# Muat variabel lingkungan dari file .env
load_dotenv()

def verify_signature(message, signature):
    # Ambil path public key dari .env
    public_key_path = os.getenv("PUBLIC_KEY_PATH")
    
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

if __name__ == "__main__":
    message = input("Masukkan pesan yang ingin diverifikasi: ")
    signature = input("Masukkan tanda tangan (hex): ")
    is_valid = verify_signature(message, signature)
    if is_valid:
        print("Tanda tangan valid.")
    else:
        print("Tanda tangan tidak valid!")
