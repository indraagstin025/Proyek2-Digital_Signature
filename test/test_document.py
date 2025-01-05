import os
import pytest
import time
from flask import url_for
from app import create_app, db
from app.models import Document, User
from io import BytesIO
from datetime import datetime, timezone
import uuid

UPLOAD_FOLDER = os.path.join('app', 'static', 'uploads')


@pytest.fixture
def create_user():
    """Fixture untuk membuat pengguna."""
    def _create_user(username, email, password):
        existing_user = db.session.get(User, username)
        if existing_user:
            return existing_user

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    return _create_user

@pytest.fixture(scope='module')
def test_client():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    app.config.update({
        'SERVER_NAME': 'localhost',
        'APPLICATION_ROOT': '/',
        'PREFERRED_URL_SCHEME': 'http',
    })
    client = app.test_client()

    with app.app_context():
        db.create_all()

        user = User(username='testuser', email='test@example.com')
        user.set_password('Password123')
        db.session.add(user)
        db.session.commit()

    yield client

    with app.app_context():
        db.drop_all()

@pytest.fixture(scope='function')
def login_test_user(test_client):
    response = test_client.post('/auth/login', data={'email': 'test@example.com', 'password': 'Password123'})
    assert response.status_code == 302
    yield
    test_client.get('/auth/logout')

@pytest.fixture(scope='function')
def cleanup_upload_folder():
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    yield
    for file in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, file)
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"[DEBUG] Could not delete file: {file_path}, Error: {e}")

def test_allowed_file():
    from app.routes.document import allowed_file

    assert allowed_file('test.pdf') is True
    assert allowed_file('test.docx') is True
    assert allowed_file('test.exe') is False
    assert allowed_file('test') is False

def test_file_size_valid():
    from app.routes.document import file_size_valid

    small_file = BytesIO(b"a" * 1024 * 1024 * 10)
    large_file = BytesIO(b"a" * 1024 * 1024 * 20)

    assert file_size_valid(small_file) is True
    assert file_size_valid(large_file) is False

def test_upload_document(test_client, login_test_user, cleanup_upload_folder):
    file_data = {'file': (BytesIO(b"This is a test file"), 'test.pdf')}
    response = test_client.post('/documents/upload', data=file_data, content_type='multipart/form-data')

    assert response.status_code == 302

    uploaded_file_path = os.path.join(UPLOAD_FOLDER, 'test.pdf')
    assert os.path.exists(uploaded_file_path)

    with test_client.application.app_context():
        document = Document.query.filter_by(filename='test.pdf').first()
        assert document is not None

def test_view_document(test_client, login_test_user, cleanup_upload_folder):
    file_data = {'file': (BytesIO(b"This is a test file for viewing"), 'test.pdf')}
    upload_response = test_client.post('/documents/upload', data=file_data, content_type='multipart/form-data')

    assert upload_response.status_code == 302

    uploaded_file_path = os.path.join(UPLOAD_FOLDER, 'test.pdf')
    assert os.path.exists(uploaded_file_path)

    with test_client.application.app_context():
        document = Document.query.filter_by(filename='test.pdf').first()
        assert document is not None

        view_response = test_client.get(f'/documents/document/{document.id}')
        assert view_response.status_code == 200
        assert b"This is a test file for viewing" in view_response.data

def test_list_documents(test_client, create_user):
    """Test list documents endpoint."""
    with test_client.application.app_context():
        # Buat pengguna unik
        unique_username = f"testuser_{uuid.uuid4()}"
        unique_email = f"{unique_username}@example.com"
        test_user = create_user(unique_username, unique_email, 'password123')

        # Login pengguna
        login_response = test_client.post('/auth/login', data={'email': unique_email, 'password': 'password123'})
        assert login_response.status_code == 302, "Failed to login test user."

        # Tambahkan dokumen
        document1 = Document(
            user_id=test_user.id,
            filename="test_document1.pdf",
            filepath="/path/to/test_document1.pdf",
            file_hash="hash1",
            uploaded_at=datetime(2025, 1, 6, 10, 0, 0),
        )
        document2 = Document(
            user_id=test_user.id,
            filename="test_document2.docx",
            filepath="/path/to/test_document2.docx",
            file_hash="hash2",
            uploaded_at=datetime(2025, 1, 6, 9, 0, 0),
        )
        db.session.add_all([document1, document2])
        db.session.commit()

        # Hit endpoint
        response = test_client.get(url_for('document.list_documents'))

        # Validasi response
        assert response.status_code == 200, "Expected status code 200, but got {response.status_code}"
        response_data = response.data.decode('utf-8')
        assert "test_document1.pdf" in response_data
        assert "test_document2.docx" in response_data
        assert "06 January 2025, 10:00" in response_data
        assert "06 January 2025, 09:00" in response_data

def test_delete_document(test_client, create_user, cleanup_upload_folder):
    """Test untuk menghapus dokumen."""
    with test_client.application.app_context():
        # Buat pengguna uji
        unique_username = f"testuser_{uuid.uuid4()}"
        unique_email = f"{unique_username}@example.com"
        test_user = create_user(unique_username, unique_email, 'password123')

        # Login sebagai pengguna yang baru dibuat
        response = test_client.post(
            '/auth/login', data={'email': unique_email, 'password': 'password123'}, follow_redirects=True
        )
        assert response.status_code == 200, "Login gagal"

        # Verifikasi pengguna yang login
        current_user = db.session.get(User, int(test_user.id))
        print(f"[DEBUG] Current user ID: {current_user.id}")
        assert current_user.id == test_user.id, "Pengguna login tidak sesuai dengan pemilik dokumen."

        # Membuat dokumen uji
        mock_file_path = os.path.join(UPLOAD_FOLDER, 'test_document.pdf')
        with open(mock_file_path, 'w') as f:
            f.write("Test document.")

        document = Document(
            user_id=test_user.id,  # pastikan user_id adalah milik test_user
            filename="test_document.pdf",
            filepath=mock_file_path,
            file_hash="dummy_hash",
            uploaded_at=datetime.now(timezone.utc),
        )
        db.session.add(document)
        db.session.commit()

        # Debugging: Verifikasi bahwa dokumen telah dibuat dengan benar
        print(f"[DEBUG] Created document ID: {document.id}, User ID: {document.user_id}")

        # Menghapus dokumen
        response = test_client.post(url_for('document.delete_document', doc_id=document.id), follow_redirects=True)
        assert response.status_code == 200, "Penghapusan dokumen gagal"

        # Verifikasi bahwa dokumen sudah dihapus
        deleted_document = Document.query.filter_by(id=document.id).first()
        assert deleted_document is None, "Dokumen masih ada setelah dihapus."

        # Verifikasi bahwa file juga dihapus dari sistem file
        assert not os.path.exists(mock_file_path), "File tidak dihapus dari sistem file."
