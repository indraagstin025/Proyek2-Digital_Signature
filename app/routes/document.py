import os
from flask import Blueprint, request, redirect, url_for, render_template, flash, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models import Document, Signature
from app import db
from app.utils.sign_token import sign_token
from app.utils.verify_token import verify_token
from werkzeug.exceptions import NotFound
from flask import send_file
import hashlib
import mimetypes

UPLOAD_FOLDER = os.path.abspath(os.path.join('app', 'static', 'uploads'))
ALLOWED_EXTENSIONS = {'pdf', 'docx'}
MAX_FILE_SIZE_MB = 15

document_bp = Blueprint('document', __name__)


def create_upload_folder_if_not_exists():
    """Create upload folder if it doesn't exist."""
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    """Check if the file extension and mimetype are allowed."""
    file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    mimetype, _ = mimetypes.guess_type(filename)
    return file_extension in ALLOWED_EXTENSIONS and mimetype


def generate_file_hash(file):
    """Generate SHA256 hash of the file."""
    hash_sha256 = hashlib.sha256()
    file.seek(0)  # Make sure to read the file from the start
    for chunk in iter(lambda: file.read(4096), b""):
        hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


@document_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_document():
    """
    Endpoint for uploading a document.
    """
    if request.method == 'POST':
        file = request.files.get('file')

        if not file or not allowed_file(file.filename):
            flash('Invalid file type or no file uploaded.', 'error')
            return redirect(url_for('document.list_documents'))

        try:
            create_upload_folder_if_not_exists()

            # Generate file details
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file_hash = generate_file_hash(file)

            # Check for duplicate files
            if Document.query.filter_by(file_hash=file_hash).first():
                flash('A document with the same content already exists.', 'error')
                return redirect(url_for('document.list_documents'))

            # Save file locally
            file.seek(0)  # Reset file pointer
            file.save(filepath)

            # Save document to database
            new_document = Document.create_document(
                user_id=current_user.id,
                file=file,
                upload_folder=UPLOAD_FOLDER
            )

            # Create token for the document
            token = sign_token(file_hash)

            # Save signature to database
            Signature.create_signature(
                document_id=new_document.id,
                user_id=current_user.id,
                token=token
            )

            flash('Document uploaded and signed successfully!', 'success')
            return redirect(url_for('document.list_documents'))

        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'error')

    return render_template('upload_document.html')


@document_bp.route('/documents', methods=['GET'])
@login_required
def list_documents():
    """Route to list user documents."""
    user_documents = Document.query.filter_by(user_id=current_user.id).order_by(Document.uploaded_at.desc()).all()
    return render_template('list_documents.html', documents=user_documents)


@document_bp.route('/view_document/<int:doc_id>', methods=['GET'])
@login_required
def view_document(doc_id):
    """Route to view a specific document in a template."""
    # Ambil dokumen dari database
    document = Document.query.get_or_404(doc_id)

    # Periksa apakah pengguna memiliki akses ke dokumen
    if document.user_id != current_user.id:
        flash("You don't have permission to access this document.", 'error')
        return redirect(url_for('document.list_documents'))

    # Periksa apakah file ada di sistem
    filepath = document.filepath
    if not os.path.exists(filepath):
        flash("The requested document is not found on the server.", 'error')
        return redirect(url_for('document.list_documents'))

    # Kirim data dokumen ke template
    return render_template('view_document.html', document=document)


@document_bp.route('/verify/<int:doc_id>', methods=['POST'])
@login_required
def verify_document_signature(doc_id):
    """Verify the document signature."""
    try:
        document = Document.query.get_or_404(doc_id)
        signature = Signature.query.filter_by(document_id=doc_id).first()

        if not signature:
            return jsonify({"error": "Signature not found for this document."}), 404

        is_valid = verify_token(signature.token, document.file_hash)
        if is_valid:
            return jsonify({"message": "Signature is valid."}), 200
        else:
            return jsonify({"error": "Signature is invalid."}), 400
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@document_bp.route('/document/delete/<int:doc_id>', methods=['POST'])
@login_required
def delete_document(doc_id):
    """Route to delete a specific document."""
    document = Document.query.get_or_404(doc_id)
    if document.user_id != current_user.id:
        flash("You don't have permission to delete this document.", 'error')
        return redirect(url_for('document.list_documents'))

    try:
        # Hapus tanda tangan terkait
        signatures = Signature.query.filter_by(document_id=doc_id).all()
        for signature in signatures:
            db.session.delete(signature)

        # Hapus dokumen
        filepath = document.filepath
        db.session.delete(document)
        db.session.commit()

        # Hapus file dari sistem
        if os.path.exists(filepath):
            os.remove(filepath)
            
        if Document.query.count() == 0:
            db.session.execute("ALTER TABLE document AUTO_INCREMENT = 1")
            db.session.commit()

        flash("Document deleted successfully.", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to delete document: {str(e)}", 'error')

    return redirect(url_for('document.list_documents'))

