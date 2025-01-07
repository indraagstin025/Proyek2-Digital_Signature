import os

private_key_path = "keys/private_key.pem"
public_key_path = "keys/public_key.pem"

print("Ukuran private_key.pem:", os.path.getsize(private_key_path), "byte")
print("Ukuran public_key.pem:", os.path.getsize(public_key_path), "byte")
