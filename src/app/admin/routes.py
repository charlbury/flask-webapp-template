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
    # Get all users
    users = User.query.order_by(User.created_at.desc()).all()
    
    # Get all available roles for the dropdown (as names only)
    roles = Role.query.all()
    role_names = [role.name for role in roles]
    
    return render_template('admin/users.html', users=users, roles=role_names)


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


# ============================================================================
# Dashboard Routes
# ============================================================================

@admin_bp.route('/dashboards/analytics')
@admin_required
def dashboards_analytics():
    """Analytics dashboard."""
    return render_template('admin/dashboards/analytics.html')


@admin_bp.route('/dashboards/discover')
@admin_required
def dashboards_discover():
    """Discover dashboard."""
    return render_template('admin/dashboards/discover.html')


@admin_bp.route('/dashboards/sales')
@admin_required
def dashboards_sales():
    """Sales dashboard."""
    return render_template('admin/dashboards/sales.html')


@admin_bp.route('/dashboards/automotive')
@admin_required
def dashboards_automotive():
    """Automotive dashboard."""
    return render_template('admin/dashboards/automotive.html')


@admin_bp.route('/dashboards/smart-home')
@admin_required
def dashboards_smart_home():
    """Smart Home dashboard."""
    return render_template('admin/dashboards/smart-home.html')


@admin_bp.route('/dashboards/blocks-analytics')
@admin_required
def dashboards_blocks_analytics():
    """Blocks Analytics dashboard."""
    return render_template('admin/dashboards/blocks-analytics.html')


# ============================================================================
# Applications Routes
# ============================================================================

@admin_bp.route('/applications/calendar')
@admin_required
def applications_calendar():
    """Calendar application."""
    return render_template('admin/applications/calendar.html')


@admin_bp.route('/applications/crm')
@admin_required
def applications_crm():
    """CRM application."""
    return render_template('admin/applications/crm.html')


@admin_bp.route('/applications/datatables')
@admin_required
def applications_datatables():
    """DataTables application."""
    return render_template('admin/applications/datatables.html')


@admin_bp.route('/applications/kanban')
@admin_required
def applications_kanban():
    """Kanban application."""
    return render_template('admin/applications/kanban.html')


@admin_bp.route('/applications/stats')
@admin_required
def applications_stats():
    """Stats application."""
    return render_template('admin/applications/stats.html')


@admin_bp.route('/applications/validation')
@admin_required
def applications_validation():
    """Validation application."""
    return render_template('admin/applications/validation.html')


@admin_bp.route('/applications/wizard')
@admin_required
def applications_wizard():
    """Wizard application."""
    return render_template('admin/applications/wizard.html')


# ============================================================================
# Ecommerce Routes
# ============================================================================

@admin_bp.route('/ecommerce/products/list')
@admin_required
def ecommerce_products_list():
    """Products list."""
    return render_template('admin/ecommerce/products/products-list.html')


@admin_bp.route('/ecommerce/products/new')
@admin_required
def ecommerce_products_new():
    """New product."""
    return render_template('admin/ecommerce/products/new-product.html')


@admin_bp.route('/ecommerce/products/edit')
@admin_required
def ecommerce_products_edit():
    """Edit product."""
    return render_template('admin/ecommerce/products/edit-product.html')


@admin_bp.route('/ecommerce/products/page')
@admin_required
def ecommerce_products_page():
    """Product page."""
    return render_template('admin/ecommerce/products/product-page.html')


@admin_bp.route('/ecommerce/orders/list')
@admin_required
def ecommerce_orders_list():
    """Orders list."""
    return render_template('admin/ecommerce/orders/list.html')


@admin_bp.route('/ecommerce/orders/details')
@admin_required
def ecommerce_orders_details():
    """Order details."""
    return render_template('admin/ecommerce/orders/details.html')


@admin_bp.route('/ecommerce/referral')
@admin_required
def ecommerce_referral():
    """Referral page."""
    return render_template('admin/ecommerce/referral.html')


# ============================================================================
# Pages Routes
# ============================================================================

@admin_bp.route('/pages/charts')
@admin_required
def pages_charts():
    """Charts page."""
    return render_template('admin/pages/charts.html')


@admin_bp.route('/pages/notifications')
@admin_required
def pages_notifications():
    """Notifications page."""
    return render_template('admin/pages/notifications.html')


@admin_bp.route('/pages/pricing')
@admin_required
def pages_pricing():
    """Pricing page."""
    return render_template('admin/pages/pricing-page.html')


@admin_bp.route('/pages/rtl')
@admin_required
def pages_rtl():
    """RTL page."""
    return render_template('admin/pages/rtl-page.html')


@admin_bp.route('/pages/sweet-alerts')
@admin_required
def pages_sweet_alerts():
    """Sweet alerts page."""
    return render_template('admin/pages/sweet-alerts.html')


@admin_bp.route('/pages/widgets')
@admin_required
def pages_widgets():
    """Widgets page."""
    return render_template('admin/pages/widgets.html')


@admin_bp.route('/pages/vr/default')
@admin_required
def pages_vr_default():
    """VR default page."""
    return render_template('admin/pages/vr/vr-default.html')


@admin_bp.route('/pages/vr/info')
@admin_required
def pages_vr_info():
    """VR info page."""
    return render_template('admin/pages/vr/vr-info.html')


# ============================================================================
# Account Routes
# ============================================================================

@admin_bp.route('/account/settings')
@admin_required
def account_settings():
    """Account settings."""
    return render_template('admin/account/settings.html')


@admin_bp.route('/account/billing')
@admin_required
def account_billing():
    """Account billing."""
    return render_template('admin/account/billing.html')


@admin_bp.route('/account/invoice')
@admin_required
def account_invoice():
    """Account invoice."""
    return render_template('admin/account/invoice.html')


@admin_bp.route('/account/security')
@admin_required
def account_security():
    """Account security."""
    return render_template('admin/account/security.html')


# ============================================================================
# Profile Routes
# ============================================================================

@admin_bp.route('/profile/projects')
@admin_required
def profile_projects():
    """Profile projects."""
    return render_template('admin/profile/projects.html')


# ============================================================================
# Projects Routes
# ============================================================================

@admin_bp.route('/projects/general')
@admin_required
def projects_general():
    """Projects general."""
    return render_template('admin/projects/general.html')


@admin_bp.route('/projects/new')
@admin_required
def projects_new():
    """New project."""
    return render_template('admin/projects/new-project.html')


@admin_bp.route('/projects/timeline')
@admin_required
def projects_timeline():
    """Projects timeline."""
    return render_template('admin/projects/timeline.html')


# ============================================================================
# Team Routes
# ============================================================================

@admin_bp.route('/team/all-projects')
@admin_required
def team_all_projects():
    """Team all projects."""
    return render_template('admin/team/all-projects.html')


@admin_bp.route('/team/messages')
@admin_required
def team_messages():
    """Team messages."""
    return render_template('admin/team/messages.html')


@admin_bp.route('/team/new-user')
@admin_required
def team_new_user():
    """Team new user."""
    return render_template('admin/team/new-user.html')


@admin_bp.route('/team/profile-overview')
@admin_required
def team_profile_overview():
    """Team profile overview."""
    return render_template('admin/team/profile-overview.html')


@admin_bp.route('/team/reports')
@admin_required
def team_reports():
    """Team reports."""
    return render_template('admin/team/reports.html')
