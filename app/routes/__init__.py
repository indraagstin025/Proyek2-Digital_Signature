from app.routes.auth import auth_bp
from app.routes.dashboard import dashboard_bp
from app.routes.document import document_bp
from app.routes.signature import signature_bp

def register_blueprints(app):
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(document_bp, url_prefix='/documents')
    app.register_blueprint(signature_bp, url_prefix='/signature/api')  # Menambahkan url_prefix
