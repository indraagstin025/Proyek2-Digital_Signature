import pytest
from app.utils.sign_token import sign_token
from app.utils.verify_token import verify_token

def test_create_signature(client):
    """Test untuk endpoint /signature/create."""
    # Pesan untuk ditandatangani
    message = 'Test Message'
    doc_id = 1

    # Simulasi permintaan ke endpoint
    response = client.post('/signature/create', json={
        'data': message,
        'doc_id': doc_id
    })

    # Periksa respons sukses
    assert response.status_code == 201
    json_data = response.get_json()
    assert 'token' in json_data
    assert json_data['message'] == 'Tanda tangan berhasil dibuat'

    # Simpan token untuk digunakan dalam pengujian berikutnya
    global created_token  # Gunakan variabel global untuk menyimpan token
    created_token = json_data['token']


def test_check_signature(client):
    """Test untuk endpoint /signature/check."""
    global created_token  # Gunakan token yang dibuat sebelumnya
    message = 'Test Message'

    # Verifikasi token yang dibuat di pengujian sebelumnya
    response = client.post('/signature/check', json={
        'token': created_token,
        'message': message
    })

    # Periksa respons sukses
    assert response.status_code == 200
    assert response.get_json()['message'] == 'Tanda tangan valid'

def test_create_signature_missing_data(client):
    """Test untuk endpoint /signature/create dengan data tidak lengkap."""
    response = client.post('/signature/create', json={
        'doc_id': 1  # Field "data" hilang
    })

    assert response.status_code == 400
    assert "Missing fields: data" in response.get_json().get('error', '')



def test_check_signature_invalid_token(client):
    """Test untuk endpoint /signature/check dengan token tidak valid."""
    invalid_token = "v4.public.invalid_token_example"
    message = 'Test Message'

    response = client.post('/signature/check', json={
        'token': invalid_token,
        'message': message
    })

    assert response.status_code == 400
    assert "Tanda tangan tidak valid" in response.get_json().get('error', '')
