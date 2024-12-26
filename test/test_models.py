import pytest
from app import create_app, db
from app.models import User

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
    # Membuat user baru untuk pengujian
    user = User(username='testuser', email='test@example.com')
    user.set_password('password')
    
    # Simpan user ke database
    with init_db.session.begin():
        init_db.session.add(user)
        init_db.session.commit()
    
    # Periksa apakah user sudah berhasil disimpan
    user_from_db = User.query.filter_by(username='testuser').first()
    assert user_from_db is not None
    assert user_from_db.username == 'testuser'
    assert user_from_db.email == 'test@example.com'
