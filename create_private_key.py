from pyseto import Key, Paseto

private_key_path = "keys/private_key.pem"

with open(private_key_path, "rb") as f:
    private_key_pem = f.read()

key = Key.new(3, "public", private_key_pem)
paseto = Paseto()

payload = {"message": "Pesan yang ingin ditandatangani"}

try:
    signed_token = paseto.encode(key, payload)
    print(f"Token: {signed_token}")
except Exception as e:
    print(f"Gagal membuat token: {e}")
