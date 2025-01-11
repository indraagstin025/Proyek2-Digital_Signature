import re
import os
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from app.extensions import db
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import func
from sqlalchemy import text 
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
        
        
    @classmethod
    def reset_auto_increment(cls):
        """
        Reset AUTO_INCREMENT untuk tabel User jika tabel kosong.
        """
        if cls.query.count() == 0:
            db.session.execute(text("ALTER TABLE user AUTO_INCREMENT = 1"))
            db.session.commit()


class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    file_hash = db.Column(db.String(64), nullable=False, unique=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
    status = db.Column(db.String(50), default='pending', nullable=False)
    doc_hash = db.Column(db.String(64), unique=True, nullable=False)  # Kolom baru untuk hash ID

    user = db.relationship('User', backref=db.backref('documents', lazy=True))

    @classmethod
    def is_duplicate(cls, file_hash):
        """
        Check if a document with the same hash already exists.
        """
        return cls.query.filter_by(file_hash=file_hash).first() is not None

    @classmethod
    def create_document(cls, user_id, filename, filepath, file_hash):
        """
        Create a document record in the database with hash ID.
        """
        if cls.is_duplicate(file_hash):
            raise ValueError("Dokumen dengan isi yang sama sudah diunggah sebelumnya.")

        # Generate doc_hash (hashed ID)
        raw_id = f"{user_id}-{file_hash}-{datetime.utcnow().isoformat()}"
        doc_hash = sha256(raw_id.encode()).hexdigest()

        new_document = cls(
            user_id=user_id,
            filename=filename,
            filepath=filepath,
            file_hash=file_hash,
            doc_hash=doc_hash
        )

        try:
            db.session.add(new_document)
            db.session.commit()
            return new_document
        except IntegrityError:
            db.session.rollback()
            raise ValueError("Terjadi kesalahan saat menyimpan dokumen.")
        
    @classmethod
    def reset_auto_increment(cls):
        """
        Reset AUTO_INCREMENT untuk tabel Document jika tabel kosong.
        """
        if cls.query.count() == 0:
            db.session.execute(text("ALTER TABLE document AUTO_INCREMENT = 1"))
            db.session.commit()




class Signature(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    document_hash = db.Column(db.String(64), db.ForeignKey('document.doc_hash'), nullable=False)
    token = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(50), default='pending', nullable=False)
    qr_code_path = db.Column(db.String(500), nullable=True)
    signer_email = db.Column(db.String(150), nullable=False)
    document_name = db.Column(db.String(255), nullable=False)

    @classmethod
    def create_signature(cls, document_hash, user_id, token, signer_email, document_name):
        """
        Membuat entri tanda tangan baru di database.
        """
        signature = cls(
            document_hash=document_hash,
            user_id=user_id,
            token=token,
            signer_email=signer_email,
            document_name=document_name,
            status='pending'
        )
        try:
            db.session.add(signature)
            db.session.commit()
            return signature
        except IntegrityError as e:
            db.session.rollback()
            raise ValueError(f"Kesalahan saat menyimpan tanda tangan: {e}")


    @classmethod
    def reset_auto_increment(cls):
        """
        Reset AUTO_INCREMENT untuk tabel Signature jika kosong.
        """
        db.session.execute(text("ALTER TABLE signature AUTO_INCREMENT = 1"))
        db.session.commit()

        
    
    
    
