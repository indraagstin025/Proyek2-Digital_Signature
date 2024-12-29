import pytest
from app import create_app, db
from app.models import User
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
    init_db.session.query(User).delete()
    init_db.session.commit()
    
    
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

    user1 = User.create_user(username='duplicateuser1', email='unique1@example.com', password='password123')

   
    with pytest.raises(ValueError, match="Username sudah terdaftar"):
        User.create_user(username='duplicateuser1', email='unique2@example.com', password='password123')

    print("Current Users in DB:", User.query.all())  
    

def test_duplicate_email(init_db):
    """Test creating two users with the same email."""
    User.create_user(username='uniqueuser1', email='duplicate@example.com', password='password123')

    with pytest.raises(ValueError, match="Email sudah terdaftar"):
        User.create_user(username='uniqueuser2', email='duplicate@example.com', password='password123')
