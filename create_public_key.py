from pyseto import Key, Paseto

# Path ke public key
public_key_path = "keys/public_key.pem"

# Token yang dihasilkan oleh private key
token = "v3.public.eyJtZXNzYWdlIjogIlBlc2FuIHlhbmcgaW5naW4gZGl0YW5kYXRhbmdhbmkifRPhCg3qRf2qiHA9orSwoz3F6AO5dxRJY_YoVLPuvuL4OSbge_opm000ebZ0rvEyvpVRRvpEv_Ld12rl49Btwfw"

# Memuat public key
with open(public_key_path, "rb") as f:
    public_key_pem = f.read()

# Buat kunci publik untuk verifikasi
key = Key.new(3, "public", public_key_pem)

# Inisialisasi Paseto
paseto = Paseto()

try:
    # Verifikasi dan decode payload
    decoded_payload = paseto.decode(key, token)
    print(f"Payload decoded: {decoded_payload}")
except Exception as e:
    print(f"Gagal mendekode token: {e}")
