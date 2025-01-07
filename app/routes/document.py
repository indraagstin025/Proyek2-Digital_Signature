import os
from flask import Blueprint, request, redirect, url_for, render_template, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.exceptions import NotFound
from app.models import Document, Signature
from app import db 
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
    """Check if file extension is allowed."""
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
    """Route for uploading documents."""
    if request.method == 'POST':
        file = request.files.get('file')

        if file and allowed_file(file.filename):
            print(f"[DEBUG] File received: {file.filename}")
            
            # Check file size
            if not file_size_valid(file):
                flash(f'File is too large. Max allowed is {MAX_FILE_SIZE_MB}MB.', 'error')
                return redirect(request.url)

            try:
                # Save file first
                filename = save_file(file)

                # Generate file hash
                file_hash = generate_file_hash(file)
                print(f"[DEBUG] Generated file hash: {file_hash}")

                # Check if document with the same hash already exists
                existing_document = Document.query.filter_by(file_hash=file_hash).first()
                if existing_document:
                    flash('File with the same content already exists in the database.', 'error')
                    return redirect(request.url)

                # Create new document entry in the database
                new_document = Document(
                    user_id=current_user.id,
                    filename=filename,
                    filepath=os.path.join(UPLOAD_FOLDER, filename),
                    file_hash=file_hash,  # Using unique file hash
                )
                db.session.add(new_document)
                db.session.commit()

                flash('Document successfully uploaded!', 'success')
                return redirect(url_for('document.list_documents'))  # Redirect to list of documents
            except RuntimeError as e:
                flash(f'File system error: {str(e)}', 'error')
                return redirect(request.url)
            except Exception as e:
                db.session.rollback()
                flash(f'Database error: {str(e)}', 'error')
                return redirect(request.url)
        else:
            flash('Invalid file format or no file uploaded.', 'error')

    return render_template('upload_document.html')


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
    """Route to delete document by ID."""
    try:
        document = Document.query.get_or_404(doc_id)

        # Check if the user has permission to delete the document
        if document.user_id != current_user.id:
            flash('You do not have permission to delete this document.', 'error')
            return redirect(url_for('document.list_documents'))

        # Delete the file from the file system
        def delete_file(filepath):
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    print(f"[DEBUG] File deleted: {filepath}")
                else:
                    flash('File not found, but the record will be deleted from the database.', 'info')
            except Exception as file_error:
                flash(f'Failed to delete file: {file_error}', 'error')
                return False
            return True

        # Delete file and then database entry
        if not delete_file(document.filepath):
            db.session.delete(document)
            db.session.commit()
            flash('Document deleted from database (file not found).', 'success')
            return redirect(url_for('document.list_documents'))

        db.session.delete(document)
        db.session.commit()
        flash('Document successfully deleted.', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Failed to delete document: {e}', 'error')

    return redirect(url_for('document.list_documents'))
