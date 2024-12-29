from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app.extensions import db
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message
from app.extensions import mail

def generate_token(email, secret_key, salt):
    serializer = URLSafeTimedSerializer(secret_key)
    return serializer.dumps(email, salt=salt)

def verify_token(token, secret_key, salt, max_age):
    serializer = URLSafeTimedSerializer(secret_key)
    try:
        return serializer.loads(token, salt=salt, max_age=max_age)
    except:
        return None

def send_reset_email(email, reset_url, sender):
    msg = Message(
        subject="Reset Your Password",
        recipients=[email],
        body=f"Click the link to reset your password: {reset_url}",
        sender=sender
    )
    mail.send(msg)

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.home'))

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        try:
            User.create_user(username=username, email=email, password=password)
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('auth.login'))
        except ValueError as e:
            flash(str(e), 'danger')

    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.home'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard.home'))

        flash('Invalid email or password.', 'danger')

    return render_template('auth/login.html')

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
            flash('An email has been sent with instructions to reset your password.', 'info')
        else:
            flash('Email address not found.', 'danger')

        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    email = verify_token(
        token, 
        current_app.config['SECRET_KEY'], 
        current_app.config['PASSWORD_RESET_SALT'], 
        current_app.config['PASSWORD_RESET_MAX_AGE']
    )

    if not email:
        flash('The reset link is invalid or has expired.', 'danger')
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

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
