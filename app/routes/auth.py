from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app.extensions import db
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message
from app.extensions import mail
from itsdangerous import BadSignature, SignatureExpired
import logging


# Utility functions for token generation and verification
def generate_token(email, secret_key, salt):
    serializer = URLSafeTimedSerializer(secret_key)
    return serializer.dumps(email, salt=salt)


def verify_token(token, secret_key, salt, max_age):
    serializer = URLSafeTimedSerializer(secret_key)
    try:
        return serializer.loads(token, salt=salt, max_age=max_age)
    except SignatureExpired:
        return 'expired'
    except BadSignature:
        return None


def send_reset_email(email, reset_url, sender):
    msg = Message(
        subject="Reset Your Password",
        recipients=[email],
        body=f"Click the link to reset your password: {reset_url}",
        sender=sender
    )
    mail.send(msg)


# Blueprint setup
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


# Registration route
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.home'))

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        try:
            # Tambahkan validasi untuk memastikan format username dan password
            if not User._is_username_format_valid(username):
                flash("Username tidak valid. Harus minimal 3 karakter dan mengandung angka.", "danger")
                return redirect(url_for('auth.register'))

            if not User._is_password_format_valid(password):
                flash("Password tidak valid. Harus minimal 8 karakter dan mengandung angka.", "danger")
                return redirect(url_for('auth.register'))

            # Buat pengguna baru
            User.create_user(username=username, email=email, password=password)
            flash('Registrasi berhasil! Silakan login.', 'success')
            return redirect(url_for('auth.login'))
        except ValueError as e:
            flash(str(e), 'danger')

    return render_template('auth/register.html')



# Login route
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Jika pengguna sudah login, arahkan ke dashboard
    if current_user.is_authenticated:
        if request.is_json:
            return jsonify({"message": "Already logged in", "user_id": current_user.id}), 200
        return redirect(url_for('dashboard.home'))

    if request.method == 'POST':
        # Mendukung request berbasis JSON (Postman) atau form HTML
        if request.is_json:
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')
        else:
            email = request.form.get('email')
            password = request.form.get('password')

        # Validasi email dan password
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)

            # Log user ID dan cookie session
            logging.info(f"User {user.id} berhasil login. Session: {request.cookies.get('session')}")
            
            # Respon jika request JSON (API)
            if request.is_json:
                response = jsonify({
                    "message": "Login successful",
                    "user": {"id": user.id, "email": user.email, "username": user.username}
                })
                response.set_cookie('session', request.cookies.get('session'), httponly=True)
                return response, 200

            # Respon jika form HTML
            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard.home'))

        # Jika kredensial salah
        if request.is_json:
            return jsonify({"error": "Invalid email or password"}), 401
        flash('Invalid email or password.', 'danger')

    # Render halaman login untuk request GET
    return render_template('auth/login.html')





# Forgot password route
@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()

        if user:
            token = generate_token(
                email,
                current_app.config['SECRET_KEY'],
                current_app.config['PASSWORD_RESET_SALT']
            )
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            send_reset_email(email, reset_url, current_app.config['MAIL_DEFAULT_SENDER'])
            flash('Email untuk reset password telah dikirim.', 'info')
        else:
            flash('Alamat email tidak ditemukan.', 'danger')
            current_app.logger.warning(f"Permintaan reset password untuk email yang tidak terdaftar: {email}")

        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html')



# Reset password route
@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    email = verify_token(
        token,
        current_app.config['SECRET_KEY'],
        current_app.config['PASSWORD_RESET_SALT'],
        current_app.config['PASSWORD_RESET_MAX_AGE']
    )

    if email == 'expired':
        flash('The reset link has expired.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    elif not email:
        flash('The reset link is invalid.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        new_password = request.form['password']

        if not User._is_password_format_valid(new_password):
            flash('Password tidak valid. Harus minimal 8 karakter dan mengandung angka.', 'danger')
            return redirect(url_for('auth.reset_password', token=token))

        user = User.query.filter_by(email=email).first()
        if user:
            user.set_password(new_password)
            db.session.commit()
            flash('Your password has been updated. You can now log in.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('User not found.', 'danger')

    return render_template('auth/reset_password.html', token=token)



@auth_bp.route('/delete-all-users', methods=['POST'])
@login_required
def delete_all_users():
    """
    Hapus semua pengguna dari database dan atur ulang AUTO_INCREMENT.
    Endpoint ini hanya boleh digunakan oleh administrator.
    """
    if not current_user.is_authenticated or not current_user.is_admin:  # Tambahkan logika admin
        return jsonify({"error": "Unauthorized access"}), 403

    try:
        # Hapus semua pengguna
        User.query.delete()
        db.session.commit()

        # Reset AUTO_INCREMENT
        User.reset_auto_increment()

        return jsonify({"message": "Semua pengguna berhasil dihapus dan AUTO_INCREMENT direset."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Terjadi kesalahan: {str(e)}"}), 500



# Logout route
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
