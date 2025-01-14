import os
import pytest
from flask import url_for
from werkzeug.datastructures import FileStorage
from app import create_app, db
from app.models import User, Document
from io import BytesIO

# Fixture setup
@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app('testing')  # Ensure testing configuration is set up in your app factory
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()

@pytest.fixture
def db_session(app):
    """Provide a transactional database session."""
    with app.app_context():
        yield db.session

@pytest.fixture
def init_user(db_session):
    """Create a test user and add to the database."""
    user = User(username='testuser', email='testuser@example.com', password='password')
    db_session.add(user)
    db_session.commit()
    return user

# Utility to generate a test file
def generate_test_file(content=b"Dummy file content", filename="testfile.pdf"):
    """Generate a dummy file for testing."""
    test_file = BytesIO(content)
    test_file.name = filename
    return test_file

# Test for uploading a document
def test_upload_document(client, init_user):
    """Test the document upload functionality."""
    # Simulate a logged-in user
    with client.session_transaction() as session:
        session["_user_id"] = init_user.id

    # Generate a test file
    test_file = generate_test_file()

    # Perform a POST request to upload the document
    response = client.post(
        url_for('document.upload_document'),
        data={"file": (test_file, test_file.name)},
        content_type="multipart/form-data",
        follow_redirects=True
    )

    # Assertions
    assert response.status_code == 200
    assert b"Document uploaded successfully" in response.data

# Test for uploading a duplicate document
def test_upload_duplicate_document(client, init_user):
    """Test duplicate document upload detection."""
    # Simulate a logged-in user
    with client.session_transaction() as session:
        session["_user_id"] = init_user.id

    # Generate a test file
    test_file = generate_test_file()

    # Upload the file for the first time
    client.post(
        url_for('document.upload_document'),
        data={"file": (test_file, test_file.name)},
        content_type="multipart/form-data",
        follow_redirects=True
    )

    # Upload the same file again
    test_file = generate_test_file()  # Create a new file object with the same content
    response = client.post(
        url_for('document.upload_document'),
        data={"file": (test_file, test_file.name)},
        content_type="multipart/form-data",
        follow_redirects=True
    )

    # Assertions
    assert response.status_code == 200
    assert b"A document with the same content already exists." in response.data

def test_view_document(client, init_user, db_session):
    """Test viewing a document."""
    # Simulate a logged-in user
    with client.session_transaction() as session:
        session["_user_id"] = init_user.id

    # Create a test document in the database
    document = Document.create_document(
        user_id=init_user.id,
        filename="testfile.pdf",
        filepath="path/to/testfile.pdf",
        file_hash="dummyhash123"
    )
    db_session.commit()

    # Perform a GET request to view the document
    response = client.get(url_for('document.view_document', doc_hash=document.doc_hash), follow_redirects=True)

    # Assertions
    assert response.status_code == 200
    assert b"testfile.pdf" in response.data

# Test for deleting a document
def test_delete_document(client, init_user, db_session):
    """Test deleting a document."""
    # Simulate a logged-in user
    with client.session_transaction() as session:
        session["_user_id"] = init_user.id

    # Create a test document in the database
    document = Document.create_document(
        user_id=init_user.id,
        filename="testfile.pdf",
        filepath="path/to/testfile.pdf",
        file_hash="dummyhash123"
    )
    db_session.commit()

    # Perform a POST request to delete the document
    response = client.post(
        url_for('document.delete_document', doc_hash=document.doc_hash),
        follow_redirects=True
    )

    # Assertions
    assert response.status_code == 200
    assert b"Document deleted successfully." in response.data

# Test for trying to view a non-existent document
def test_view_non_existent_document(client, init_user):
    """Test viewing a non-existent document."""
    # Simulate a logged-in user
    with client.session_transaction() as session:
        session["_user_id"] = init_user.id

    # Perform a GET request for a non-existent document
    response = client.get(url_for('document.view_document', doc_hash="nonexistenthash"))

    # Assertions
    assert response.status_code == 404

# Test for trying to delete a non-existent document
def test_delete_non_existent_document(client, init_user):
    """Test deleting a non-existent document."""
    # Simulate a logged-in user
    with client.session_transaction() as session:
        session["_user_id"] = init_user.id

    # Perform a POST request for a non-existent document
    response = client.post(
        url_for('document.delete_document', doc_hash="nonexistenthash"),
        follow_redirects=True
    )

    # Assertions
    assert response.status_code == 404
