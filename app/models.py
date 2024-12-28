import re
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from sqlalchemy.exc import IntegrityError


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        """Set password with validation."""
        if not self.is_valid_password(password):
            raise ValueError("Password harus minimal 8 karakter dan mengandung angka.")
        self.password = generate_password_hash(password)

    def check_password(self, password):
        """Check if the given password matches the stored hash."""
        return check_password_hash(self.password, password)

    @staticmethod
    def is_valid_username(username):
        """Validate username to ensure it contains numbers and is unique."""
        # Pastikan username tidak kosong dan panjangnya minimal 3 karakter
        if not username or len(username) < 3:
            return False
        
        # Username harus mengandung angka
        if not any(char.isdigit() for char in username):
            return False
        
        # Validasi untuk memastikan username unik di database
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return False  # Username sudah ada di database
        
        return True

    @staticmethod
    def is_valid_password(password):
        """Validate password to ensure it has at least 8 characters and contains numbers."""
        if len(password) < 8:
            return False  # Password harus minimal 8 karakter
        if not any(char.isdigit() for char in password):
            return False  # Password harus mengandung angka
        return True

    @classmethod
    def create_user(cls, username, email, password):
        """Create a new user after validating username and password."""
        # Validasi username dan password
        if not cls.is_valid_username(username):
            raise ValueError("Username tidak valid. Pastikan username mengandung angka dan unik.")
        
        if not cls.is_valid_password(password):
            raise ValueError("Password tidak valid. Password harus minimal 8 karakter dan mengandung angka.")
        
        # Membuat user baru
        new_user = cls(username=username, email=email)
        new_user.set_password(password)

        try:
            db.session.add(new_user)
            db.session.commit()
            return new_user
        except IntegrityError:
            db.session.rollback()
            raise ValueError("Username atau email sudah terdaftar.")
