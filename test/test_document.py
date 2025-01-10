import os
import pytest
from app import create_app, db
from app.models import Document, Signature, User
from flask import url_for
from werkzeug.datastructures import FileStorage
from io import BytesIO
import hashlib

@pytest.fixture
def app():
    """Set up Flask app for testing."""
    app = create_app('testing')  # Pastikan mode 'testing' menggunakan TestingConfig
    app_context = app.app_context()
    app_context.push()
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()
    app_context.pop()


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()

@pytest.fixture
def init_user(app):
    """Create a test user."""
    user = User.create_user(username="testuser1", email="test@example.com", password="password123")
    return user

def generate_test_file(content="Test file content"):
    """Generate a test file."""
    return FileStorage(
        stream=BytesIO(content.encode('utf-8')),
        filename="testfile.pdf",
        content_type="application/pdf"
    )

def test_upload_document(client, init_user):
    """Test the document upload functionality."""
    with client.session_transaction() as session:
        session["_user_id"] = init_user.id  # Simulate logged-in user

    test_file = generate_test_file()  # Buat file dummy
    response = client.post(
        url_for('document.upload_document', _external=True),  # Tambahkan _external=True
        data={"file": test_file},
        content_type="multipart/form-data"
    )
    assert response.status_code == 302
    assert b'Document uploaded and signed successfully!' in response.data


def test_upload_duplicate_document(client, init_user, app):
    """Test duplicate document upload detection."""
    with client.session_transaction() as session:
        session["_user_id"] = init_user.id  # Simulate logged-in user

    # Upload the first document
    test_file = generate_test_file()
    client.post(
        url_for('document.upload_document'),
        data={"file": test_file},
        content_type="multipart/form-data"
    )

    # Try uploading the same document again
    duplicate_response = client.post(
        url_for('document.upload_document'),
        data={"file": test_file},
        content_type="multipart/form-data"
    )
    assert b'A document with the same content already exists.' in duplicate_response.data

def test_verify_document(client, init_user, app):
    """Test the document signature verification."""
    with client.session_transaction() as session:
        session["_user_id"] = init_user.id  # Simulate logged-in user

    # Upload a document
    test_file = generate_test_file()
    upload_response = client.post(
        url_for('document.upload_document'),
        data={"file": test_file},
        content_type="multipart/form-data"
    )
    assert upload_response.status_code == 302

    # Fetch the uploaded document
    document = Document.query.first()
    assert document is not None

    # Verify the document
    verify_response = client.post(url_for('document.verify_document_signature', doc_id=document.id))
    assert verify_response.status_code == 200
    assert b'Signature is valid.' in verify_response.data

def test_delete_document(client, init_user, app):
    """Test document deletion."""
    with client.session_transaction() as session:
        session["_user_id"] = init_user.id  # Simulate logged-in user

    # Upload a document
    test_file = generate_test_file()
    client.post(
        url_for('document.upload_document'),
        data={"file": test_file},
        content_type="multipart/form-data"
    )

    # Delete the document
    document = Document.query.first()
    assert document is not None

    delete_response = client.post(url_for('document.delete_document', doc_id=document.id))
    assert delete_response.status_code == 302
    assert b'Document deleted successfully.' in delete_response.data

    # Ensure the document is deleted from the database
    assert Document.query.get(document.id) is None
