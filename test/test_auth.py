import pytest
from app import create_app
from app.extensions import db
from app.models import User
from flask_login import current_user
from sqlalchemy import inspect

@pytest.fixture
def app():
    """Fixture untuk membuat aplikasi Flask dengan konfigurasi testing."""
    app = create_app(config_name='testing')
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SECRET_KEY': 'test_secret',
        'PASSWORD_RESET_SALT': 'test_salt',
        'PASSWORD_RESET_MAX_AGE': 3600,
        'WTF_CSRF_ENABLED': False,
    })
    
    with app.app_context():
        db.create_all()
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
        'username': 'testuser123',
        'email': 'test@example.com',
        'password': 'password123'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Registration successful! Please login.' in response.data

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

def test_forgot_password(client, create_user):
    """Menguji proses lupa password."""
    create_user('testuser', 'test@example.com', 'password123')
    response = client.post('/auth/forgot-password', data={
        'email': 'test@example.com'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'An email has been sent with instructions to reset your password.' in response.data

def test_reset_password(client, create_user, app):
    """Menguji proses reset password."""
    user = create_user('testuser', 'test@example.com', 'password123')


    with app.app_context():
        from itsdangerous import URLSafeTimedSerializer
        serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        token = serializer.dumps(user.email, salt=app.config['PASSWORD_RESET_SALT'])

    response = client.post(f'/auth/reset-password/{token}', data={
        'password': 'newpassword123'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Your password has been updated. You can now log in.' in response.data


    login_response = client.post('/auth/login', data={
        'email': 'test@example.com',
        'password': 'newpassword123'
    }, follow_redirects=True)
    assert login_response.status_code == 200
    assert b'Login successful!' in login_response.data

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
