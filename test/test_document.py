import os
import pytest
import time
from flask import url_for
from app import create_app, db
from app.models import Document, User
from io import BytesIO
from datetime import datetime
from pytest_mock import mocker




UPLOAD_FOLDER = os.path.join('app', 'static', 'uploads')


@pytest.fixture(scope='module')
def test_client():
    """Setup Flask test client."""
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
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


def test_list_documents(test_client, login_test_user, mocker):
    """
    Test untuk memastikan endpoint /documents menampilkan daftar dokumen yang benar.
    """
    # Mock pengguna saat ini
    mock_user_id = 1
    mocker.patch('flask_login.utils._get_user', return_value=mock_user(mock_user_id))

    # Mock data dokumen
    mock_documents = [
        Document(
            id=1,
            user_id=mock_user_id,
            filename="document1.pdf",
            filepath="/path/to/document1.pdf",
            file_hash="hash1",
            uploaded_at=datetime(2025, 1, 5, 14, 30, 45),
            status="pending",
        ),
        Document(
            id=2,
            user_id=mock_user_id,
            filename="document2.docx",
            filepath="/path/to/document2.docx",
            file_hash="hash2",
            uploaded_at=datetime(2025, 1, 5, 14, 0, 0),
            status="approved",
        ),
    ]

    # Mock query database
    with test_client.application.app_context():  # Pastikan berada dalam konteks aplikasi
        mocker.patch.object(Document.query, 'filter_by', return_value=mocker.Mock(
            order_by=mocker.Mock(return_value=mocker.Mock(all=lambda: mock_documents))
        ))

        # Hit endpoint
        response = test_client.get('/documents')

        # Pastikan status response 200
        assert response.status_code == 200

        # Periksa apakah dokumen tampil di template
        response_data = response.data.decode('utf-8')
        assert "document1.pdf" in response_data
        assert "document2.docx" in response_data
        assert "05-01-2025 14:30:45" in response_data
        assert "05-01-2025 14:00:00" in response_data
        assert "pending" in response_data
        assert "approved" in response_data



