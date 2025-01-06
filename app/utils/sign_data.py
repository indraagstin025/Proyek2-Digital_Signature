import os
from nacl.signing import SigningKey
from dotenv import load_dotenv

# Muat variabel lingkungan dari file .env
load_dotenv()

def sign_data(message):
    # Ambil path private key dari .env
    private_key_path = os.getenv("PRIVATE_KEY_PATH")
    
    with open(private_key_path, "rb") as private_file:
        private_key_bytes = private_file.read()
    
    private_key = SigningKey(private_key_bytes)

    # Tanda tangani data
    signed_message = private_key.sign(message.encode("utf-8"))
    print("Data berhasil ditandatangani.")
    return signed_message

if __name__ == "__main__":
    data = input("Masukkan data yang ingin ditandatangani: ")
    signed_message = sign_data(data)
    print(f"Tanda tangan: {signed_message.signature.hex()}")
    print(f"Pesan + Tanda tangan: {signed_message.hex()}")
