import pytest
from app import create_app
from app.extensions import db
from app.models import User
from sqlalchemy import inspect

@pytest.fixture
def app():
    """Fixture untuk membuat aplikasi Flask dengan konfigurasi testing."""
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',  
        'SECRET_KEY': 'test_secret',
        'WTF_CSRF_ENABLED': False,  
    })
        
    with app.app_context():
        db.create_all()  
        print("Tabel dibuat: ", inspect(db.engine).get_table_names())
        yield app
        db.session.remove()
        db.drop_all()  

@pytest.fixture
def client(app):
    """Fixture untuk membuat client pengujian."""
    return app.test_client()

@pytest.fixture
def create_user():
    """Fixture untuk membuat pengguna."""
    def _create_user(username, email, password):
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user
    return _create_user

def test_register(client):
    """Menguji proses pendaftaran."""
    response = client.post('/auth/register', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Registration successful!' in response.data

def test_login(client, create_user):
    """Menguji proses login dengan kredensial valid."""
    create_user('testuser', 'test@example.com', 'password123')
    response = client.post('/auth/login', data={
        'email': 'test@example.com',
        'password': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Login successful!' in response.data

def test_invalid_login(client, create_user):
    """Menguji proses login dengan kredensial tidak valid."""
    create_user('testuser', 'test@example.com', 'password123')
    response = client.post('/auth/login', data={
        'email': 'test@example.com',
        'password': 'wrongpassword'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Invalid email or password.' in response.data

def test_logout(client, create_user):
    """Menguji proses logout."""
    create_user('testuser', 'test@example.com', 'password123')
    client.post('/auth/login', data={
        'email': 'test@example.com',
        'password': 'password123'
    }, follow_redirects=True)
    response = client.get('/auth/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'You have been logged out.' in response.data
