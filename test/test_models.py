import pytest
from app import create_app, db
from app.models import User, Document
from io import BytesIO
from sqlalchemy.exc import IntegrityError


@pytest.fixture(scope='module')
def app():
    app = create_app(config_name='testing')
    yield app


@pytest.fixture(scope='module')
def init_db(app):
    with app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()


@pytest.fixture(autouse=True)
def cleanup(init_db):
    yield
    init_db.session.query(Document).delete()
    init_db.session.query(User).delete()
    init_db.session.commit()


@pytest.fixture
def test_user(init_db):
    """Create a test user."""
    user = User.create_user(username='testuser123', email='test@example.com', password='password123')
    return user


@pytest.fixture
def test_file():
    """Create a sample file to be used in tests."""
    file_content = b"Sample file content."
    file = BytesIO(file_content)
    file.filename = "testfile.txt"
    return file


def test_user_creation(init_db):
    """Test creating a valid user."""
    user = User.create_user(username='testuser123', email='test@example.com', password='password123')

    user_from_db = User.query.filter_by(username='testuser123').first()
    assert user_from_db is not None
    assert user_from_db.username == 'testuser123'
    assert user_from_db.email == 'test@example.com'


def test_invalid_username(init_db):
    """Test creating a user with an invalid username."""
    with pytest.raises(ValueError, match="Username tidak valid"):
        User.create_user(username='invaliduser', email='test2@example.com', password='password123')


def test_invalid_password(init_db):
    """Test creating a user with an invalid password."""
    with pytest.raises(ValueError, match="Password tidak valid"):
        User.create_user(username='validuser1', email='test3@example.com', password='short')


def test_duplicate_username(init_db):
    """Test creating two users with the same username."""
    User.create_user(username='duplicateuser1', email='unique1@example.com', password='password123')

    with pytest.raises(ValueError, match="Username sudah terdaftar"):
        User.create_user(username='duplicateuser1', email='unique2@example.com', password='password123')


def test_duplicate_email(init_db):
    """Test creating two users with the same email."""
    User.create_user(username='uniqueuser1', email='duplicate@example.com', password='password123')

    with pytest.raises(ValueError, match="Email sudah terdaftar"):
        User.create_user(username='uniqueuser2', email='duplicate@example.com', password='password123')


def test_document_creation(init_db, test_user, test_file):
    """Test creating a new document."""
    document = Document.create_document(user_id=test_user.id, file=test_file, upload_folder="/tmp")

    document_from_db = Document.query.filter_by(file_hash=document.file_hash).first()
    assert document_from_db is not None
    assert document_from_db.filename == test_file.filename
    assert document_from_db.user_id == test_user.id


def test_duplicate_document(init_db, test_user, test_file):
    """Test preventing duplicate document uploads."""
    Document.create_document(user_id=test_user.id, file=test_file, upload_folder="/tmp")

    with pytest.raises(ValueError, match="Dokumen dengan isi yang sama sudah diunggah sebelumnya"):
        Document.create_document(user_id=test_user.id, file=test_file, upload_folder="/tmp")


def test_document_with_different_content(init_db, test_user):
    """Test uploading documents with different content."""
    file1 = BytesIO(b"Content of file 1.")
    file1.filename = "file1.txt"

    file2 = BytesIO(b"Content of file 2.")
    file2.filename = "file2.txt"

    doc1 = Document.create_document(user_id=test_user.id, file=file1, upload_folder="/tmp")
    doc2 = Document.create_document(user_id=test_user.id, file=file2, upload_folder="/tmp")

    assert doc1.file_hash != doc2.file_hash
    assert doc1.filename == "file1.txt"
    assert doc2.filename == "file2.txt"


def test_invalid_filename(init_db, test_user):
    """Test uploading a document with an invalid filename."""
    invalid_file = BytesIO(b"Invalid content")
    invalid_file.filename = "../../malicious.txt"  

    with pytest.raises(ValueError, match="Nama file tidak valid atau berbahaya"):
        Document.create_document(user_id=test_user.id, file=invalid_file, upload_folder="/tmp")

    invalid_file.filename = "C:\\malicious.txt" 
    with pytest.raises(ValueError, match="Nama file tidak valid atau berbahaya"):
        Document.create_document(user_id=test_user.id, file=invalid_file, upload_folder="/tmp")

    invalid_file.filename = "/tmp/malicious.txt"  
    with pytest.raises(ValueError, match="Nama file tidak valid atau berbahaya"):
        Document.create_document(user_id=test_user.id, file=invalid_file, upload_folder="/tmp")

