from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='')

@dashboard_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.home'))
    return render_template('index.html')

@dashboard_bp.route('/dashboard')
@login_required
def home():
    return render_template('dashboard.html')

@dashboard_bp.route('/base')
def base():
    return render_template('base.html')
