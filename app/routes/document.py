import os
from flask import Blueprint, request, redirect, url_for, render_template, send_from_directory, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models import Document
from app import db

# Konstanta untuk folder upload dan ekstensi file yang diperbolehkan
UPLOAD_FOLDER = os.path.join('app', 'static', 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'docx'}

# Blueprint untuk dokumentasi
document_bp = Blueprint('document', __name__)

def create_upload_folder_if_not_exists():
    """Membuat folder upload jika belum ada."""
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    """Memeriksa apakah ekstensi file sesuai dengan yang diperbolehkan."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_file(file):
    """Menyimpan file ke folder upload dan mengembalikan path file yang disimpan."""
    create_upload_folder_if_not_exists()
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    return filename, filepath

def handle_upload_error(file):
    """Menangani error jika file tidak valid atau ekstensi tidak sesuai."""
    if not file:
        flash('Tidak ada file yang diunggah.', 'error')
    else:
        flash('Format file tidak diperbolehkan.', 'error')

@document_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_document():
    """Route untuk meng-upload dokumen."""
    if request.method == 'POST':
        file = request.files.get('file')
        
        if file and allowed_file(file.filename):
            try:
                filename, filepath = save_file(file)
                new_document = Document.create_document(
                    user_id=current_user.id,
                    file=file,
                    upload_folder=UPLOAD_FOLDER
                )
                flash('Dokumen berhasil di-upload!', 'success')
                return redirect(url_for('document.view_document', doc_id=new_document.id))
            except ValueError as e:
                flash(str(e), 'error')
        else:
            handle_upload_error(file)

    return render_template('upload_document.html')

@document_bp.route('/document/<int:doc_id>', methods=['GET'])
@login_required
def view_document(doc_id):
    """Route untuk melihat dokumen yang di-upload."""
    document = Document.query.get_or_404(doc_id)
    
    if document.user_id != current_user.id:
        flash('Anda tidak memiliki akses ke dokumen ini.', 'error')
        return redirect(url_for('document.upload_document'))

    return send_from_directory(directory=UPLOAD_FOLDER, filename=document.filename)
