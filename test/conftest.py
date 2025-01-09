import pytest
from app import create_app, db
from io import BytesIO

@pytest.fixture(scope='module')
def test_app():
    """Fixture untuk membuat aplikasi dengan konfigurasi testing."""
    app = create_app(config_name='testing')
    with app.app_context():
        yield app


@pytest.fixture(scope='module')
def client(test_app):
    """Fixture untuk client test Flask."""
    with test_app.test_client() as client:
        with test_app.app_context():
            db.create_all()  # Buat semua tabel
            
            # Tambahkan pengguna dummy
            from app.models import User
            user = User(username='testuser', email='testuser@example.com')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()

            # Debugging untuk memastikan pengguna dibuat
            created_user = User.query.filter_by(email='testuser@example.com').first()
            print(f"Created User: {created_user.email}")  # Debugging

        yield client

        with test_app.app_context():
            db.drop_all()  # Hapus semua tabel setelah selesai


@pytest.fixture(scope='function')
def login_user(client):
    """Fixture untuk login user."""
    response = client.post('/auth/login', data={
        'email': 'testuser@example.com',
        'password': 'password123'
    }, follow_redirects=True)  # Ikuti redirect ke halaman dashboard

    # Debugging respons
    print(f"Response Data: {response.data.decode('utf-8')}")

    # Validasi bahwa pengguna diarahkan ke dashboard
    assert response.status_code == 200
    assert b"Platform Tanda Tangan Digital" in response.data  # Validasi berdasarkan teks unik halaman dashboard

@pytest.fixture(scope='function')
def create_dummy_document(client, login_user):
    """Fixture untuk membuat dokumen dummy."""
    file_content = b"This is a test document."
    data = {
        'file': (BytesIO(file_content), 'test_document.pdf')
    }
    response = client.post('/documents/upload', data=data, content_type='multipart/form-data', follow_redirects=True)

    # Ambil dokumen dari database
    from app.models import Document
    with client.application.app_context():
        document = Document.query.first()  # Ambil dokumen pertama
        assert document is not None

    return document




