import os
from flask import Flask
from flask_login import LoginManager
from dotenv import load_dotenv
from app.extensions import init_extensions, db, mail
from app.routes import register_blueprints
import pymysql

# Load environment variables
load_dotenv()

private_key_path = os.getenv('PRIVATE_KEY_PATH')
public_key_path = os.getenv('PUBLIC_KEY_PATH')

# Setup MySQL driver
pymysql.install_as_MySQLdb()

# Fungsi untuk membuat aplikasi
def create_app(config_name='default'):
    app = Flask(__name__,
                template_folder=os.path.join(os.getcwd(), 'app', 'templates'),
                static_folder=os.path.join(os.getcwd(), 'app', 'static'))
    
    # Konfigurasi aplikasi berdasarkan environment
    if config_name == 'testing':
        app.config.from_object('config.TestingConfig')
    elif config_name == 'development':
        app.config.from_object('config.DevelopmentConfig')
    else:
        app.config.from_object('config.ProductionConfig')
    
    # Inisialisasi ekstensi dan blueprint
    init_extensions(app)
    register_blueprints(app)
    mail.init_app(app)
    

    # Tambahkan header untuk mencegah cache
    @app.after_request
    def add_header(response):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response

    return app

# Fungsi untuk list routes yang bisa diakses
def list_routes(app):
    with app.app_context():
        print("Routes available:")
        for rule in app.url_map.iter_rules():
            print(f"Rule: {rule}")

# Buat dan jalankan aplikasi
app = create_app()

# List routes setelah aplikasi siap
list_routes(app)
