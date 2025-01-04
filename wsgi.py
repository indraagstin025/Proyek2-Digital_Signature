import sys
import os

# Tambahkan path ke sistem
sys.path.insert(0, os.path.dirname(__file__))

# Import create_app dari app
from app import create_app

# Buat instance aplikasi
application = create_app()
