import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))



class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', '0d9f920bdaeb0ea0e2e8757eda2b1df2d298d07ad1b7129066f2635923c1496a')  
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'mysql://root@localhost/tanda_tangan_online')  
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class TestingConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # Gunakan SQLite in-memory untuk pengujian
    TESTING = True
    