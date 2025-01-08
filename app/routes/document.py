import os
from flask import Blueprint, request, redirect, url_for, render_template, flash, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.exceptions import NotFound
from app.models import Document, Signature
from app import db 
from app.utils.sign_token import sign_token
from app.utils.verify_token import verify_token
import mimetypes
import hashlib
from flask import send_file

UPLOAD_FOLDER = os.path.abspath(os.path.join('app', 'static', 'uploads'))

ALLOWED_EXTENSIONS = {'pdf', 'docx'}
MAX_FILE_SIZE_MB = 15


document_bp = Blueprint('document', __name__)

def create_upload_folder_if_not_exists():
    """Create upload folder if it doesn't exist."""
    try:
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            print(f"[DEBUG] Folder created: {UPLOAD_FOLDER}")  
        else:
            print(f"[DEBUG] Folder already exists: {UPLOAD_FOLDER}")  
    except OSError as e:
        print(f"[DEBUG] Error creating folder: {e}")
        raise RuntimeError(f"Failed to create upload folder: {str(e)}")

def allowed_file(filename):
    allowed_extensions = {'pdf', 'docx'}
    allowed_mimetypes = {'application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'}
    file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    mimetype, _ = mimetypes.guess_type(filename)

    return file_extension in allowed_extensions and mimetype in allowed_mimetypes


def file_size_valid(file):
    """Check if file size is within allowed limit."""
    file.seek(0, os.SEEK_END)
    size_mb = file.tell() / (1024 * 1024)
    file.seek(0)
    return size_mb <= MAX_FILE_SIZE_MB

def generate_file_hash(file):
    """Generate SHA256 hash of the file."""
    hash_sha256 = hashlib.sha256()
    file.seek(0)  # Make sure to read the file from the start
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
        raise RuntimeError(f"Failed to save file: {str(e)}")
    return filename

@document_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_document():
    if request.method == 'POST':
        file = request.files.get('file')

        if file and allowed_file(file.filename):
            try:
                # Proses penyimpanan file
                filename = save_file(file)
                file_hash = generate_file_hash(file)

                # Membuat token tanda tangan
                token = sign_token(file_hash)
                print(f"[DEBUG] Token tanda tangan: {token}")

                # Simpan dokumen ke database
                new_document = Document(
                    user_id=current_user.id,
                    filename=filename,
                    filepath=os.path.join(UPLOAD_FOLDER, filename),
                    file_hash=file_hash,
                )
                db.session.add(new_document)
                db.session.commit()

                # Simpan tanda tangan ke database
                new_signature = Signature.create_signature(
                    document_id=new_document.id,
                    user_id=current_user.id,
                    token=token,
                )

                flash('Dokumen berhasil diunggah dan ditandatangani!', 'success')
                return redirect(url_for('document.list_documents'))
            except Exception as e:
                db.session.rollback()
                flash(f'Terjadi kesalahan: {str(e)}', 'error')

    return render_template('upload_document.html')

@document_bp.route('/verify/<int:doc_id>', methods=['POST'])
@login_required
def verify_document_signature(doc_id):
    try:
        document = Document.query.get_or_404(doc_id)

        # Ambil token tanda tangan dari database
        signature = Signature.query.filter_by(document_id=doc_id).first()
        if not signature:
            return jsonify({"error": "Tanda tangan tidak ditemukan untuk dokumen ini."}), 404

        # Verifikasi tanda tangan
        is_valid = verify_token(signature.token, document.file_hash)
        if is_valid:
            return jsonify({"message": "Tanda tangan valid."}), 200
        else:
            return jsonify({"error": "Tanda tangan tidak valid."}), 400
    except Exception as e:
        return jsonify({"error": f"Terjadi kesalahan: {e}"}), 500

@document_bp.route('/view_document/<int:doc_id>', methods=['GET'])
@login_required
def view_document(doc_id):
    document = Document.query.get_or_404(doc_id)

    # Check if the logged-in user is the owner of the document
    if document.user_id != current_user.id:
        flash('You do not have access to this document.', 'error')
        return redirect(url_for('document.upload_document'))

    file_path = os.path.join(UPLOAD_FOLDER, document.filename)

    # Check if file exists
    if not os.path.exists(file_path):
        flash('File not found on the server.', 'error')
        return redirect(url_for('document.list_documents'))

    # Send the file for viewing in the template
    return render_template('view_document.html', document=document)


@document_bp.route('/documents', methods=['GET'])
@login_required
def list_documents():
    """Route to show list of user documents."""
    user_documents = (
        Document.query.filter_by(user_id=current_user.id)
        .order_by(Document.uploaded_at.desc())
        .all()
    )

    return render_template('list_documents.html', documents=user_documents)


@document_bp.route('/document/delete/<int:doc_id>', methods=['POST'])
@login_required
def delete_document(doc_id):
    try:
        document = Document.query.get_or_404(doc_id)
        if document.user_id != current_user.id:
            flash('You do not have permission to delete this document.', 'error')
            return redirect(url_for('document.list_documents'))

        filepath = document.filepath
        db.session.delete(document)
        db.session.commit()

        if os.path.exists(filepath):
            os.remove(filepath)

        flash('Document successfully deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to delete document: {e}', 'error')

    return redirect(url_for('document.list_documents'))
