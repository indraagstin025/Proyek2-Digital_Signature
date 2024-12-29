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
        """Set hashed password after validation."""
        if not self._is_password_format_valid(password):
            raise ValueError("Password harus minimal 8 karakter dan mengandung angka.")
        self.password = generate_password_hash(password)

    def check_password(self, password):
        """Verify the given password against the stored hash."""
        return check_password_hash(self.password, password)

    @staticmethod
    def _is_username_format_valid(username):
        """Check if the username format is valid."""
        if not username or len(username) < 3:
            return False  
        if not any(char.isdigit() for char in username):
            return False 
        return True

    @staticmethod
    def _is_password_format_valid(password):
        """Check if the password format is valid."""
        if len(password) < 8:
            return False 
        if not any(char.isdigit() for char in password):
            return False 
        return True

    @classmethod
    def is_username_unique(cls, username):
        """Check if the username is unique in the database."""
        return cls.query.filter_by(username=username).first() is None

    @classmethod
    def is_email_unique(cls, email):
        """Check if the email is unique in the database."""
        return cls.query.filter_by(email=email).first() is None

    @classmethod
    def create_user(cls, username, email, password):
        """
        Create a new user with validated username and password.
        Raises ValueError if validation fails or if username/email is not unique.
        """
        if not cls._is_username_format_valid(username):
            raise ValueError("Username tidak valid. Pastikan username minimal 3 karakter dan mengandung angka.")
        
        if not cls.is_username_unique(username):
            raise ValueError("Username sudah terdaftar.")
        
        if not cls.is_email_unique(email):
            raise ValueError("Email sudah terdaftar.")
        
        if not cls._is_password_format_valid(password):
            raise ValueError("Password tidak valid. Password harus minimal 8 karakter dan mengandung angka.")
        
        
        new_user = cls(username=username, email=email)
        new_user.set_password(password)

        
        try:
            db.session.add(new_user)
            db.session.commit()
            return new_user
        except IntegrityError:
            db.session.rollback()
            raise ValueError("Terjadi kesalahan saat menyimpan data. Coba lagi.")
