from flask import Flask
from flask_login import LoginManager
from app.extensions import init_extensions, db
from app.routes import register_blueprints
from dotenv import load_dotenv
from app.extensions import db
from app.extensions import mail, db
import pymysql



load_dotenv()
pymysql.install_as_MySQLdb()

from app.models import User

def create_app(config_name='default'):
    app = Flask(__name__)
    
    if config_name == 'testing':
        app.config.from_object('config.TestingConfig')  # Gunakan TestingConfig untuk pengujian
    else:
        app.config.from_object('config.Config') 
    
    init_extensions(app)
    register_blueprints(app)
    mail.init_app(app)
    
    
    with app.app_context():
        db.create_all() 
    
    @app.after_request
    def add_header(response):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response
    
    
    return app
