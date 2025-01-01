import os
import pytest
from dotenv import load_dotenv
from config import Config, TestingConfig


load_dotenv()

@pytest.fixture(scope="module")
def config():
    """Fixture untuk memuat konfigurasi dari config.py"""
    return Config()

def test_secret_key(config):
    """Uji apakah SECRET_KEY diambil dengan benar"""
    assert config.SECRET_KEY == os.getenv('SECRET_KEY', '0d9f920bdaeb0ea0e2e8757eda2b1df2d298d07ad1b7129066f2635923c1496a')

def test_database_uri(config):
    """Uji apakah SQLALCHEMY_DATABASE_URI diambil dengan benar"""
    expected_uri = os.getenv('DATABASE_URL', 'mysql://root@localhost/tanda_tangan_online')
    assert config.SQLALCHEMY_DATABASE_URI == expected_uri

def test_mail_settings(config):
    """Uji apakah pengaturan email diambil dengan benar"""
    assert config.MAIL_SERVER == 'smtp.gmail.com'
    assert config.MAIL_PORT == 587
    assert config.MAIL_USE_TLS is True
    assert config.MAIL_USE_SSL is False
    assert config.MAIL_USERNAME == 'mahasiswaulbiit@gmail.com'
    assert config.MAIL_PASSWORD == 'vqdh soin nczl vhmy'
    assert config.MAIL_DEFAULT_SENDER == 'mahasiswaulbiit@gmail.com'

def test_testing_config():
    """Uji apakah pengaturan TestingConfig bekerja dengan benar"""
    testing_config = TestingConfig()
    assert testing_config.SQLALCHEMY_DATABASE_URI == 'sqlite:///:memory:'
    assert testing_config.TESTING is True

def test_env_variables():
    """Uji apakah variabel lingkungan dari .env bekerja dengan benar"""
    
    load_dotenv()  
    assert os.getenv('SECRET_KEY') == '0d9f920bdaeb0ea0e2e8757eda2b1df2d298d07ad1b7129066f2635923c1496a'  
    assert os.getenv('DATABASE_URL') == 'mysql://root@localhost/tanda_tangan_online'  

def test_default_values_when_env_not_set():
    """Uji apakah aplikasi fallback ke nilai default jika variabel lingkungan tidak ada"""
    
    os.environ.pop('SECRET_KEY', None)
    os.environ.pop('DATABASE_URL', None)
    
    default_config = Config()
    assert default_config.SECRET_KEY == '0d9f920bdaeb0ea0e2e8757eda2b1df2d298d07ad1b7129066f2635923c1496a'
    assert default_config.SQLALCHEMY_DATABASE_URI == 'mysql://root@localhost/tanda_tangan_online'

def test_gitignore_for_env():
    """Uji apakah .env sudah di-ignore oleh git"""
    assert '.env' in open('.gitignore').read()

if __name__ == "__main__":
    pytest.main()
