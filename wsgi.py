import sys
import os

# Tambahkan path aplikasi ke sys.path
sys.path.insert(0, os.path.dirname(__file__))

# Impor aplikasi Flask Anda
from app import app as application  # Sesuaikan nama package 'app' dengan folder aplikasi Anda
