from pyseto import Key, Paseto
import os
import logging
import json

def verify_token(token, message=None):
    """
    Verifikasi token menggunakan kunci publik.
    :param token: Token PASETO yang akan diverifikasi.
    :param message: Pesan yang diharapkan (opsional).
    :return: Payload jika token valid, atau None jika tidak valid.
    """
    # Memastikan PUBLIC_KEY_PATH ada
    public_key_path = os.getenv("PUBLIC_KEY_PATH")
    if not os.path.exists(public_key_path):
        raise FileNotFoundError(f"Kunci publik tidak ditemukan: {public_key_path}")

    # Membaca kunci publik dari file
    with open(public_key_path, "rb") as f:
        public_key_pem = f.read()

    # Membuat objek kunci publik
    public_key = Key.new(version=4, purpose="public", key=public_key_pem)

    # Inisialisasi PASETO
    paseto = Paseto()

    try:
        # Verifikasi dan dekode token
        decoded_token = paseto.decode(public_key, token)
        logging.info(f"Payload yang didekode: {decoded_token}")

        # Mengakses payload dari objek Token
        payload_bytes = decoded_token.payload
        logging.info(f"Payload setelah akses: {payload_bytes}")

        # Parsing payload dari bytes ke dictionary
        payload = json.loads(payload_bytes.decode("utf-8"))
        logging.info(f"Payload setelah parsing: {payload}")

        # Jika pesan diberikan, cocokkan dengan payload
        if message is not None:
            if payload.get("message") != message:
                logging.error("Pesan tidak cocok dengan payload.")
                return None  # Pesan tidak cocok

        # Jika valid, kembalikan payload
        return payload

    except Exception as e:
        logging.error(f"Gagal mendekode token: {e}")
        return None
