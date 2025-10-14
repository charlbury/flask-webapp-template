"""
Main application routes.
"""

from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from . import main_bp
from ..models import User, Project


@main_bp.route('/')
def index():
    """Landing page."""
    return render_template('main/index.html')


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard."""
    # Get user's projects
    user_projects = Project.query.filter_by(owner_id=current_user.id).all()
    
    return render_template('main/dashboard.html', projects=user_projects)
