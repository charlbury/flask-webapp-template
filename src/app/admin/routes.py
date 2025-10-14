"""
Admin routes.
"""

from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user
from sqlalchemy.orm import joinedload

from . import admin_bp
from .forms import AssignRoleForm, RemoveRoleForm
from ..models import User, Role, Project
from ..extensions import db
from ..security.roles import admin_required, ensure_role_exists


@admin_bp.route('/')
@admin_required
def dashboard():
    """Admin dashboard with statistics."""
    # Get counts
    total_users = User.query.count()
    admin_users = User.query.join(User.roles).filter(Role.name == 'admin').count()
    total_projects = Project.query.count()
    
    # Get recent users
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                         total_users=total_users,
                         admin_users=admin_users,
                         total_projects=total_projects,
                         recent_users=recent_users)


@admin_bp.route('/users')
@admin_required
def users():
    """List all users with their roles."""
    # Get users with their roles loaded to avoid N+1 queries
    users = User.query.options(joinedload(User.roles)).order_by(User.created_at.desc()).all()
    
    return render_template('admin/users.html', users=users)


@admin_bp.route('/users/<user_id>/roles', methods=['POST'])
@admin_required
def assign_role(user_id):
    """Assign a role to a user."""
    form = AssignRoleForm()
    
    if form.validate_on_submit():
        user = User.query.get_or_404(user_id)
        role_name = form.role_name.data
        
        # Ensure role exists
        role = ensure_role_exists(role_name)
        
        if user.add_role(role_name):
            db.session.commit()
            flash(f'Role "{role_name}" assigned to {user.email}', 'success')
        else:
            flash(f'User {user.email} already has role "{role_name}"', 'info')
    else:
        flash('Invalid form data', 'error')
    
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<user_id>/roles/remove', methods=['POST'])
@admin_required
def remove_role(user_id):
    """Remove a role from a user."""
    form = RemoveRoleForm()
    
    if form.validate_on_submit():
        user = User.query.get_or_404(user_id)
        role_name = form.role_name.data
        
        if user.remove_role(role_name):
            db.session.commit()
            flash(f'Role "{role_name}" removed from {user.email}', 'success')
        else:
            flash(f'User {user.email} does not have role "{role_name}"', 'info')
    else:
        flash('Invalid form data', 'error')
    
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<user_id>/toggle-active', methods=['POST'])
@admin_required
def toggle_user_active(user_id):
    """Toggle user active status."""
    user = User.query.get_or_404(user_id)
    
    # Prevent deactivating yourself
    if user.id == current_user.id:
        flash('You cannot deactivate your own account', 'error')
        return redirect(url_for('admin.users'))
    
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'activated' if user.is_active else 'deactivated'
    flash(f'User {user.email} has been {status}', 'success')
    
    return redirect(url_for('admin.users'))
