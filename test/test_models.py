import pytest
from app import create_app, db
from app.models import User
from sqlalchemy.exc import IntegrityError

# Fixture untuk membuat aplikasi dengan konfigurasi pengujian
@pytest.fixture(scope='module')
def app():
    app = create_app(config_name='testing')  # Pilih konfigurasi testing
    yield app

# Fixture untuk inisialisasi database
@pytest.fixture(scope='module')
def init_db(app):
    with app.app_context():
        db.create_all()  # Membuat semua tabel di database untuk pengujian
        yield db  # Mengembalikan objek db untuk digunakan dalam pengujian
        db.session.remove()  # Menutup sesi database setelah pengujian selesai
        db.drop_all()  # Menghapus tabel setelah pengujian selesai

def test_user_creation(init_db):
    # Membuat user baru untuk pengujian dengan username yang valid
    user = User(username='testuser123', email='test@example.com', password='password123')
    # Simpan user ke database
    init_db.session.add(user)
    init_db.session.commit()
    
    # Periksa apakah user sudah berhasil disimpan
    user_from_db = User.query.filter_by(username='testuser123').first()
    assert user_from_db is not None
    assert user_from_db.username == 'testuser123'
    assert user_from_db.email == 'test@example.com'

def test_invalid_username(init_db):
    # Coba buat user dengan username yang tidak valid (tidak mengandung angka)
    invalid_user = User(username='testuser', email='test2@example.com', password='password123')

    # Validasi username sebelum disimpan
    if User.is_valid_username(invalid_user.username):
        pytest.fail("Harusnya username tidak valid karena tidak mengandung angka.")

        pass  # Mengharapkan ValueError karena username tidak valid

def test_invalid_password(init_db):
    # Coba buat user dengan password yang tidak valid (kurang dari 8 karakter)
    user = User(username='testuser123', email='test3@example.com', password='short')
    try:
        user.set_password('short')  # Password yang tidak valid (kurang dari 8 karakter)
        init_db.session.add(user)
        init_db.session.commit()
        pytest.fail("Harusnya password invalid karena kurang dari 8 karakter.")
    except ValueError:
        pass  # Mengharapkan ValueError karena password tidak valid

def test_unique_username(init_db):
    # Coba buat dua user dengan username yang sama
    user1 = User(username='uniqueuser1', email='user1@example.com', password='password123')
    init_db.session.add(user1)
    init_db.session.commit()

    # Coba buat user kedua dengan username yang sama
    user2 = User(username='uniqueuser1', email='user2@example.com', password='password123')

    # Validasi username sebelum commit untuk memastikan duplikasi username tidak diizinkan
    if User.is_valid_username(user2.username):
        pytest.fail("Harusnya username tidak boleh duplikat.")

    # Simpan user kedua
    try:
        init_db.session.add(user2)
        init_db.session.commit()
        pytest.fail("Harusnya username tidak boleh duplikat.")
    except IntegrityError:
        pass  # Mengharapkan IntegrityError karena username sudah ada
