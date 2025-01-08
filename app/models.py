import re
import os
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from app.extensions import db
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import func
from hashlib import sha256
from datetime import datetime, timezone



class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)  # Waktu pembuatan akun
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)  # Waktu pembaruan akun


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


class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    file_hash = db.Column(db.String(64), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
    status = db.Column(db.String(50), default='pending', nullable=False)
    
    user = db.relationship('User', backref=db.backref('documents', lazy=True))
    # Tidak perlu backref di sini karena sudah diatur di model Signature

    @classmethod
    def is_duplicate(cls, file_content):
        file_content.seek(0)  # Reset pointer ke awal file
        file_hash = sha256(file_content).hexdigest()
        file_content.seek(0)  # Reset ulang setelah hashing
        return cls.query.filter_by(file_hash=file_hash).first() is not None


    @classmethod
    def create_document(cls, user_id, file, upload_folder):
        """Buat entri dokumen baru. Menghindari unggahan duplikat dengan memeriksa hash file."""
        from werkzeug.utils import secure_filename
        import os

        filename = file.filename

        if not filename or filename.startswith('.') or '..' in filename or '/' in filename or '\\' in filename:
            raise ValueError("Nama file tidak valid atau berbahaya")

        filename = secure_filename(filename)
        filepath = os.path.join(upload_folder, filename)

        file_content = file.read()
        file_hash = sha256(file_content).hexdigest()

        if cls.query.filter_by(file_hash=file_hash).first():
            raise ValueError("Dokumen dengan isi yang sama sudah diunggah sebelumnya.")

        file.seek(0)

        new_document = cls(
            user_id=user_id,
            filename=filename,
            filepath=filepath,
            file_hash=file_hash
        )

        try:
            db.session.add(new_document)
            db.session.commit()
            return new_document
        except IntegrityError:
            db.session.rollback()
            raise ValueError("Terjadi kesalahan saat menyimpan dokumen.")


class Signature(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=False)
    token = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    status = db.Column(db.String(50), default='pending', nullable=False)
    
    document = db.relationship('Document', backref=db.backref('signatures', lazy=True))  # 'signatures' tetap di sini
    user = db.relationship('User', backref=db.backref('signatures', lazy=True)) # Relasi balik ke User

    @classmethod
    def verify_signature(cls, document_id, token):
        """Verifikasi apakah token yang diberikan cocok dengan tanda tangan untuk dokumen tertentu."""
        signature = Signature.query.filter_by(document_id=document_id, token=token).first()
        if signature:
            return True
        return False

    @classmethod
    def create_signature(cls, document_id, user_id, token):
        """Membuat tanda tangan baru untuk dokumen tertentu."""
        signature = cls(document_id=document_id, user_id=user_id, token=token, status='pending')
        try:
            db.session.add(signature)
            db.session.commit()
            return signature
        except IntegrityError:
            db.session.rollback()
            raise ValueError("Terjadi kesalahan saat membuat tanda tangan.")
