from nacl.signing import SigningKey

def generate_keys():
    # Membuat pasangan kunci
    private_key = SigningKey.generate()
    private_key_bytes = private_key.encode()
    public_key_bytes = private_key.verify_key.encode()

    # Simpan ke file
    with open("keys/private_key.pem", "wb") as private_file:
        private_file.write(private_key_bytes)

    with open("keys/public_key.pem", "wb") as public_file:
        public_file.write(public_key_bytes)

    print("Kunci berhasil dibuat!")
    print(f"Private Key: keys/private_key.pem")
    print(f"Public Key: keys/public_key.pem")

if __name__ == "__main__":
    generate_keys()
