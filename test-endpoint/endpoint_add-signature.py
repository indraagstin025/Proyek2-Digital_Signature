import requests

# URL endpoint
url = "http://127.0.0.1:5000/signature/add-signature"

# Header (pastikan Anda telah login jika menggunakan Flask-Login)
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer <your_auth_token>"  # Tambahkan token jika diperlukan
}

# Data JSON untuk dikirimkan
data = {
    "doc_id": 13,
    "signature": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAA..."
}

# Kirim POST request
response = requests.post(url, json=data, headers=headers)

# Periksa respons
print(f"Status Code: {response.status_code}")
print(f"Response JSON: {response.json()}")
