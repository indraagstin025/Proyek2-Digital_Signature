from pyseto import Key, Paseto
import os
import logging

def sign_token(message):
    if not isinstance(message, str):
        raise TypeError("Pesan harus berupa string")

    # Memuat kunci privat dari file
    private_key_path = os.getenv("PRIVATE_KEY_PATH")
    if not os.path.exists(private_key_path):
        raise FileNotFoundError(f"Kunci privat tidak ditemukan: {private_key_path}")

    with open(private_key_path, "rb") as f:
        private_key_pem = f.read()

    # Membuat objek kunci privat
    private_key = Key.new(version=4, purpose="public", key=private_key_pem)

    # Membuat payload
    payload = {"message": message}
    logging.info(f"Payload yang akan ditandatangani: {payload}")

    # Membuat token
    paseto = Paseto()
    token = paseto.encode(private_key, payload)

    # Konversi token ke string jika masih berupa bytes
    if isinstance(token, bytes):
        token = token.decode("utf-8")

    logging.info(f"Token yang dihasilkan: {token}")
    return token
