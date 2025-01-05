import os
import pytest
import time
import random
from flask import url_for
from app import create_app, db
from app.models import Document, User
from io import BytesIO
from datetime import datetime
from pytest_mock import mocker




UPLOAD_FOLDER = os.path.join('app', 'static', 'uploads')

@pytest.fixture
def create_user():
    """Fixture untuk membuat pengguna."""
    def _create_user(username, email, password):
        # Tambahkan pengecekan untuk memastikan pengguna unik
        existing_user = User.query.filter_by(username=username).first()
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

        # Create a test user
        user = User(username='testuser', email='test@example.com')
        user.set_password('Password123')
        db.session.add(user)
        db.session.commit()

    yield client

    with app.app_context():
        db.drop_all()


@pytest.fixture(scope='function')
def login_test_user(test_client):
    """Log in the test user."""
    response = test_client.post('/auth/login', data={'email': 'test@example.com', 'password': 'Password123'})
    assert response.status_code == 302  # Pastikan login berhasil
    yield
    test_client.get('/auth/logout')


@pytest.fixture(scope='function')
def cleanup_upload_folder():
    """Ensure upload folder exists and clean up after each test."""
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    yield
    time.sleep(1)  # Tambahkan waktu tunggu untuk memastikan file tidak sedang digunakan
    for file in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, file)
        try:
            os.remove(file_path)
        except PermissionError:
            print(f"[DEBUG] File still in use, cannot delete: {file_path}")


# Test cases
def test_allowed_file():
    from app.routes.document import allowed_file

    assert allowed_file('test.pdf') is True
    assert allowed_file('test.docx') is True
    assert allowed_file('test.exe') is False
    assert allowed_file('test') is False


def test_file_size_valid():
    from app.routes.document import file_size_valid

    small_file = BytesIO(b"a" * 1024 * 1024 * 10)  # 10MB
    large_file = BytesIO(b"a" * 1024 * 1024 * 20)  # 20MB

    assert file_size_valid(small_file) is True
    assert file_size_valid(large_file) is False


def test_upload_document(test_client, login_test_user, cleanup_upload_folder):
    """Test uploading a valid document."""
    file_data = {'file': (BytesIO(b"This is a test file"), 'test.pdf')}
    response = test_client.post('/documents/upload', data=file_data, content_type='multipart/form-data')

    # Pastikan respons statusnya redirect (302)
    assert response.status_code == 302, f"Unexpected status code: {response.status_code}"

    # Cek apakah file ada di direktori upload
    uploaded_file_path = os.path.join(UPLOAD_FOLDER, 'test.pdf')
    print(f"[DEBUG] Checking for file at: {uploaded_file_path}")
    assert os.path.exists(uploaded_file_path), "Uploaded file not found in UPLOAD_FOLDER"

    # Cek apakah dokumen terdaftar di database
    with test_client.application.app_context():
        document = Document.query.filter_by(filename='test.pdf').first()
        assert document is not None, "Document not found in database"



def test_view_document(test_client, login_test_user, cleanup_upload_folder):
    """Test viewing an uploaded document."""
    # Upload dokumen
    file_data = {'file': (BytesIO(b"This is a test file for viewing"), 'test.pdf')}
    upload_response = test_client.post('/documents/upload', data=file_data, content_type='multipart/form-data')

    # Pastikan upload berhasil
    assert upload_response.status_code == 302, f"Unexpected status code: {upload_response.status_code}"

    # Cek apakah file ada di folder upload
    uploaded_file_path = os.path.join(UPLOAD_FOLDER, 'test.pdf')
    print(f"[DEBUG] Checking for file at: {uploaded_file_path}")
    assert os.path.exists(uploaded_file_path), "Uploaded file not found in UPLOAD_FOLDER"

    # Akses dokumen di database
    with test_client.application.app_context():
        document = Document.query.filter_by(filename='test.pdf').first()
        assert document is not None, "Document not found in database"

        # Akses endpoint untuk melihat dokumen
        view_response = test_client.get(f'/documents/document/{document.id}')
        assert view_response.status_code == 200, f"Unexpected status code: {view_response.status_code}"
        assert b"This is a test file for viewing" in view_response.data
          
class MockUser:
    """Mock class for user."""
    def __init__(self, id):
        self.id = id

def mock_user(user_id):
    """Return a mock user."""
    return MockUser(user_id)


def test_list_documents(test_client, create_user, mocker):
    """
    Test untuk memastikan endpoint /documents menampilkan daftar dokumen pengguna dengan benar.
    """
    with test_client.application.app_context():
        # Buat pengguna uji dengan username unik
        test_user = create_user(f'testuser_{datetime.now().timestamp()}', f'testuser_{datetime.now().timestamp()}@example.com', 'password123')

        # Mock pengguna yang sedang login
        mocker.patch('flask_login.utils._get_user', return_value=test_user)

        # Tambahkan dokumen ke database
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

        # Pastikan status response 200
        assert response.status_code == 200

        # Periksa apakah nama dokumen muncul di data respons HTML
        response_data = response.data.decode('utf-8')
        assert "test_document1.pdf" in response_data
        assert "test_document2.docx" in response_data

        # Periksa apakah tanggal upload ditampilkan dengan format yang benar
        assert "06 January 2025, 10:00" in response_data
        assert "06 January 2025, 09:00" in response_data

        # Periksa apakah tombol untuk melihat dan menghapus dokumen ada di respons
        assert url_for('document.view_document', doc_id=document1.id) in response_data
        assert url_for('document.delete_document', doc_id=document1.id) in response_data
        assert url_for('document.view_document', doc_id=document2.id) in response_data
        assert url_for('document.delete_document', doc_id=document2.id) in response_data








