import pytest
from io import BytesIO

def test_upload_document(client, login_user):
    """Test untuk mengunggah dokumen dengan jenis file yang diperbolehkan."""
    data = {
        'file': (BytesIO(b'This is a test document.'), 'test_document.pdf')
    }
    response = client.post('/documents/upload', data=data, content_type='multipart/form-data')
    assert response.status_code == 302  # Redirect setelah berhasil


def test_upload_invalid_file_type(client, login_user):
    """Test untuk mengunggah dokumen dengan jenis file yang tidak diperbolehkan."""
    data = {
        'file': (BytesIO(b'This is a test document.'), 'test_document.exe')
    }
    response = client.post('/documents/upload', data=data, content_type='multipart/form-data', follow_redirects=True)

    # Validasi bahwa pesan flash muncul
    assert b"Jenis file tidak diperbolehkan atau file tidak ditemukan." in response.data



def test_upload_duplicate_document(client, login_user, create_dummy_document):
    """Test untuk mencegah duplikasi dokumen."""
    file_content = b"This is a test document."
    data = {
        'file': (BytesIO(file_content), 'test_document.pdf')
    }
    response = client.post('/documents/upload', data=data, content_type='multipart/form-data', follow_redirects=True)
    assert b"Dokumen dengan isi yang sama sudah diunggah." in response.data

def test_delete_document(client, login_user, create_dummy_document):
    doc_id = create_dummy_document.id
    response = client.post(f'/documents/delete/{doc_id}', follow_redirects=True)
    assert response.status_code == 200
    assert b'Dokumen berhasil dihapus.' in response.data

def test_add_signature(client, login_user, create_dummy_document):
    data = {
        'doc_id': create_dummy_document.id,
        'signature': 'data:image/png;base64,...',  
        'position': {'x': 50, 'y': 50}
    }
    response = client.post('/documents/add-signature', json=data)
    assert response.status_code == 200
    assert b'Tanda tangan berhasil ditambahkan.' in response.data






