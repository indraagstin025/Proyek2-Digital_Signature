import os
from flask import Blueprint, request, redirect, url_for, render_template, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.exceptions import NotFound
from app.models import Document
from app import db
import mimetypes
import hashlib
from flask import send_file

UPLOAD_FOLDER = os.path.abspath(os.path.join('app', 'static', 'uploads'))

ALLOWED_EXTENSIONS = {'pdf', 'docx'}
MAX_FILE_SIZE_MB = 15

# Blueprint untuk dokumentasi
document_bp = Blueprint('document', __name__)

def create_upload_folder_if_not_exists():
    """Membuat folder upload jika belum ada."""
    try:
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            print(f"[DEBUG] Folder created: {UPLOAD_FOLDER}")  # Debugging
        else:
            print(f"[DEBUG] Folder already exists: {UPLOAD_FOLDER}")  # Debugging
    except OSError as e:
        print(f"[DEBUG] Error creating folder: {e}")
        raise RuntimeError(f"Gagal membuat folder upload: {str(e)}")

def allowed_file(filename):
    """Memeriksa apakah ekstensi file sesuai dengan yang diperbolehkan."""
    mimetype, _ = mimetypes.guess_type(filename)
    allowed_mimetypes = {
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    }
    return (
        '.' in filename
        and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
        and mimetype in allowed_mimetypes
    )

def file_size_valid(file):
    """Memeriksa apakah ukuran file sesuai batas maksimal."""
    file.seek(0, os.SEEK_END)
    size_mb = file.tell() / (1024 * 1024)
    file.seek(0)
    return size_mb <= MAX_FILE_SIZE_MB

def generate_file_hash(file):
    """Menghasilkan hash SHA256 dari file."""
    hash_sha256 = hashlib.sha256()
    file.seek(0)  # Pastikan untuk memulai pembacaan file dari awal
    for chunk in iter(lambda: file.read(4096), b""):
        hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


def save_file(file):
    create_upload_folder_if_not_exists()
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    try:
        with open(filepath, 'wb') as f:
            f.write(file.read())
        print(f"[DEBUG] File saved at: {filepath}")  # Debugging
    except OSError as e:
        raise RuntimeError(f"Gagal menyimpan file: {str(e)}")
    return filename

@document_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_document():
    """Route untuk meng-upload dokumen."""
    if request.method == 'POST':
        file = request.files.get('file')

        if file and allowed_file(file.filename):
            print(f"[DEBUG] File received: {file.filename}")
            
            # Cek ukuran file
            if not file_size_valid(file):
                flash(f'File terlalu besar. Maksimal {MAX_FILE_SIZE_MB}MB.', 'error')
                return redirect(request.url)

            try:
                # Simpan file terlebih dahulu
                filename = save_file(file)

                # Generate hash file
                file_hash = generate_file_hash(file)
                print(f"[DEBUG] Generated file hash: {file_hash}")

                # Cek apakah ada dokumen dengan hash yang sama
                existing_document = Document.query.filter_by(file_hash=file_hash).first()
                if existing_document:
                    flash('File dengan isi yang sama sudah ada di database.', 'error')
                    return redirect(request.url)

                # Buat entri dokumen baru di database
                new_document = Document(
                    user_id=current_user.id,
                    filename=filename,
                    filepath=os.path.join(UPLOAD_FOLDER, filename),
                    file_hash=file_hash,  # Menggunakan hash file yang unik
                )
                db.session.add(new_document)
                db.session.commit()

                flash('Dokumen berhasil di-upload!', 'success')
                return redirect(url_for('document.list_documents'))  # Mengarahkan ke halaman daftar dokumen
            except RuntimeError as e:
                flash(f'Error sistem file: {str(e)}', 'error')
                return redirect(request.url)
            except Exception as e:
                db.session.rollback()
                flash(f'Error database: {str(e)}', 'error')
                return redirect(request.url)
        else:
            flash('Format file tidak diperbolehkan atau tidak ada file yang diunggah.', 'error')

    return render_template('upload_document.html')


@document_bp.route('/document/<int:doc_id>', methods=['GET'])
@login_required
def view_document(doc_id):
    document = Document.query.get_or_404(doc_id)

    if document.user_id != current_user.id:
        flash('Anda tidak memiliki akses ke dokumen ini.', 'error')
        return redirect(url_for('document.upload_document'))

    file_path = os.path.join(UPLOAD_FOLDER, document.filename)

    if not os.path.exists(file_path):
        raise NotFound("File tidak ditemukan.")

    # Kirim file
    return send_file(file_path, as_attachment=False)

@document_bp.route('/documents', methods=['GET'])
@login_required
def list_documents():
    """Route untuk menampilkan daftar dokumen pengguna."""
    # Ambil semua dokumen milik pengguna saat ini, diurutkan berdasarkan waktu upload terbaru
    user_documents = (
        Document.query.filter_by(user_id=current_user.id)
        .order_by(Document.uploaded_at.desc())
        .all()
    )

    # Kirim data dokumen ke template
    return render_template('list_documents.html', documents=user_documents)

@document_bp.route('/document/delete/<int:doc_id>', methods=['POST'])
@login_required
def delete_document(doc_id):
    """Route untuk menghapus dokumen berdasarkan ID."""
    try:
        # Cari dokumen berdasarkan ID
        document = Document.query.get_or_404(doc_id)

        # Pastikan hanya pengguna yang memiliki dokumen ini yang dapat menghapusnya
        if document.user_id != current_user.id:
            flash('Anda tidak memiliki izin untuk menghapus dokumen ini.', 'error')
            return redirect(url_for('document.list_documents'))

        # Hapus file dari sistem file
        file_path = os.path.join(UPLOAD_FOLDER, document.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"[DEBUG] File deleted: {file_path}")  # Debugging
        else:
            print(f"[DEBUG] File not found for deletion: {file_path}")  # Debugging

        # Hapus entri dokumen dari database
        db.session.delete(document)
        db.session.commit()

        flash('Dokumen berhasil dihapus.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal menghapus dokumen: {str(e)}', 'error')

    return redirect(url_for('document.list_documents'))
