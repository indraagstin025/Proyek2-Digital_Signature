import pytest
from app.models import User, Document, Signature
from app.extensions import db
from werkzeug.security import check_password_hash
from datetime import datetime, timezone

def test_user_creation(app):
    with app.app_context():
        username = "user123"
        email = "user@example.com"
        password = "password123"

        user = User.create_user(username, email, password)

        assert user.username == username
        assert user.email == email
        assert check_password_hash(user.password, password)
        assert user.created_at is not None
        assert user.updated_at is not None


def test_user_duplicate_username(app):
    with app.app_context():
        username = "user123"
        email1 = "user1@example.com"
        email2 = "user2@example.com"
        password = "password123"

        User.create_user(username, email1, password)

        with pytest.raises(ValueError, match="Username sudah terdaftar."):
            User.create_user(username, email2, password)


def test_user_duplicate_email(app):
    with app.app_context():
        username1 = "user123"
        username2 = "user456"
        email = "user@example.com"
        password = "password123"

        User.create_user(username1, email, password)

        with pytest.raises(ValueError, match="Email sudah terdaftar."):
            User.create_user(username2, email, password)


def test_document_creation(app):
    with app.app_context():
        user = User.create_user("docuser123", "docuser@example.com", "password123")
        filename = "test_document.pdf"
        filepath = "/path/to/test_document.pdf"
        file_hash = "d41d8cd98f00b204e9800998ecf8427e"

        document = Document.create_document(user.id, filename, filepath, file_hash)

        assert document.filename == filename
        assert document.filepath == filepath
        assert document.file_hash == file_hash
        assert document.user_id == user.id
        assert document.uploaded_at is not None
        assert document.doc_hash is not None


def test_document_duplicate(app):
    with app.app_context():
        user = User.create_user("docuser456", "docuser2@example.com", "password123")
        filename = "duplicate_document.pdf"
        filepath = "/path/to/duplicate_document.pdf"
        file_hash = "d41d8cd98f00b204e9800998ecf8427e"

        Document.create_document(user.id, filename, filepath, file_hash)

        with pytest.raises(ValueError, match="Dokumen dengan isi yang sama sudah diunggah sebelumnya."):
            Document.create_document(user.id, filename, filepath, file_hash)


def test_signature_creation(app):
    with app.app_context():
        user = User.create_user("siguser123", "siguser@example.com", "password123")
        filename = "signed_document.pdf"
        filepath = "/path/to/signed_document.pdf"
        file_hash = "d41d8cd98f00b204e9800998ecf8427e"

        document = Document.create_document(user.id, filename, filepath, file_hash)

        token = "sample_token"
        signer_email = "signer@example.com"
        document_name = filename

        signature = Signature.create_signature(document.doc_hash, user.id, token, signer_email, document_name)

        assert signature.document_hash == document.doc_hash
        assert signature.user_id == user.id
        assert signature.token == token
        assert signature.signer_email == signer_email
        assert signature.document_name == document_name
        assert signature.timestamp is not None
        assert signature.status == "pending"


@pytest.fixture
def app():
    from app import create_app
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
