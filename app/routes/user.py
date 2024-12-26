from flask import render_template, Blueprint
from . import user_bp

@user_bp.route('/')
def dashboard():
    return render_template('base.html')