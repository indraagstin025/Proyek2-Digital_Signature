from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
import os

def generate_private_key():
    # Membuat kunci privat RSA
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    
    # Menyimpan kunci privat ke dalam file PEM
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # Path untuk menyimpan kunci privat
    private_key_path = os.path.join("keys", "private_key.pem")
    with open(private_key_path, "wb") as private_file:
        private_file.write(private_pem)
    
    print(f"Kunci privat disimpan di: {private_key_path}")
    
    return private_key


def generate_public_key(private_key):
    # Mendapatkan kunci publik dari kunci privat
    public_key = private_key.public_key()

    # Menyimpan kunci publik ke dalam file PEM
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    # Path untuk menyimpan kunci publik
    public_key_path = os.path.join("keys", "public_key.pem")
    with open(public_key_path, "wb") as public_file:
        public_file.write(public_pem)
    
    print(f"Kunci publik disimpan di: {public_key_path}")
    return public_key

if __name__ == "__main__":
    private_key = generate_private_key()
    generate_public_key(private_key)
