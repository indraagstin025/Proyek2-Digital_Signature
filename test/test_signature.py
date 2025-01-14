import pytest
from flask import Flask
from app import create_app, db
from app.models import User, Document, Signature

@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_headers(app):
    # Buat pengguna untuk autentikasi
    user = User(email="test@example.com", password="password")
    db.session.add(user)
    db.session.commit()

    # Login untuk mendapatkan header autentikasi
    client = app.test_client()
    response = client.post("/login", json={"email": "test@example.com", "password": "password"})
    token = response.json["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_add_signature(client, auth_headers):
    # Buat dokumen dummy
    document = Document(doc_hash="dummyhash", filename="test.pdf", user_id=1)
    db.session.add(document)
    db.session.commit()

    # Data request
    data = {
        "document_hash": "dummyhash",
        "signature": "data:image/png;base64,iVBORw0..."  # Isi dengan base64 valid
    }

    response = client.post("/signature/add-signature", json=data, headers=auth_headers)

    assert response.status_code == 201
    assert "message" in response.json
    assert "signature_path" in response.json
    assert "qr_code_path" in response.json


def test_check_signature(client, auth_headers):
    # Buat tanda tangan dummy
    signature = Signature(
        document_hash="dummyhash",
        user_id=1,
        token="dummytoken",
        signer_email="test@example.com",
        document_name="test.pdf",
    )
    db.session.add(signature)
    db.session.commit()

    # Data request
    data = {"token": "dummytoken"}

    response = client.post("/signature/check", json=data, headers=auth_headers)

    assert response.status_code == 200
    assert response.json["message"] == "Tanda tangan valid"


def test_validate_qr(client):
    # Buat tanda tangan dummy
    signature = Signature(
        document_hash="dummyhash",
        user_id=1,
        token="dummytoken",
        signer_email="test@example.com",
        document_name="test.pdf",
    )
    db.session.add(signature)
    db.session.commit()

    response = client.get(f"/signature/validate?token=dummytoken")

    assert response.status_code == 200
    assert b"signature_validation.html" in response.data


def test_generate_signed_doc(client, auth_headers):
    # Buat dokumen dan tanda tangan dummy
    document = Document(doc_hash="dummyhash", filename="test.pdf", filepath="test_files/test.pdf", user_id=1)
    signature = Signature(
        document_hash="dummyhash",
        user_id=1,
        qr_code_path="test_files/dummy_qr.png",
        qr_position_x=10,
        qr_position_y=10,
        qr_width=100,
        qr_height=100,
        target_page=1
    )
    db.session.add_all([document, signature])
    db.session.commit()

    response = client.get("/signature/generate-signed-doc/dummyhash", headers=auth_headers)

    assert response.status_code == 200
    assert response.content_type == "application/pdf"
