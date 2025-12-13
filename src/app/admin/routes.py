"""
Admin routes.
"""

import os
from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import current_user
from sqlalchemy.orm import joinedload

from . import admin_bp
from .forms import AssignRoleForm, RemoveRoleForm, ChangePasswordForm, AvatarUploadForm
from ..models import User, Role, Project
from ..extensions import db
from ..security.roles import admin_required, ensure_role_exists
from ..services.blob_storage import BlobStorageService
from ..utils.image_validator import validate_image_file, crop_to_square


# Live App Routes (for production development)
@admin_bp.route('/')
@admin_required
def index():
    """Redirect to live dashboard."""
    return redirect(url_for('admin.live_dashboard'))


@admin_bp.route('/dashboard')
@admin_required
def live_dashboard():
    """Live app dashboard with statistics."""
    # Get counts
    total_users = User.query.count()
    admin_users = User.query.join(User.roles).filter(Role.name == 'admin').count()
    total_projects = Project.query.count()

    # Get recent users
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()

    return render_template('admin/live/dashboard.html',
                         total_users=total_users,
                         admin_users=admin_users,
                         total_projects=total_projects,
                         recent_users=recent_users)


@admin_bp.route('/user-management')
@admin_required
def live_users():
    """Live app user management."""
    # Get all users
    users = User.query.order_by(User.created_at.desc()).all()

    # Get all available roles for the dropdown (as names only)
    roles = Role.query.all()
    role_names = [role.name for role in roles]

    return render_template('admin/live/users.html', users=users, roles=role_names)


@admin_bp.route('/settings', methods=['GET', 'POST'])
@admin_required
def live_settings():
    """Live app settings page."""
    form = ChangePasswordForm()
    avatar_form = AvatarUploadForm()

    if form.validate_on_submit():
        # Verify current password
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect', 'error')
            return render_template('admin/live/settings.html', form=form, avatar_form=avatar_form)

        # Verify new password matches confirm password (form validation handles this, but double-check)
        if form.new_password.data != form.confirm_password.data:
            flash('New passwords do not match', 'error')
            return render_template('admin/live/settings.html', form=form, avatar_form=avatar_form)

        # Update password
        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash('Password updated successfully', 'success')
        return redirect(url_for('admin.live_settings'))

    return render_template('admin/live/settings.html', form=form, avatar_form=avatar_form)


@admin_bp.route('/avatar/upload', methods=['POST'])
@admin_required
def upload_avatar():
    """Handle avatar image upload."""
    form = AvatarUploadForm()

    if not form.validate_on_submit():
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Avatar upload error: {error}', 'error')
        return redirect(url_for('admin.live_settings'))

    try:
        # Validate image file
        is_valid, error_message = validate_image_file(
            form.avatar.data,
            max_size=current_app.config.get('MAX_AVATAR_SIZE', 5242880)
        )

        if not is_valid:
            flash(f'Avatar upload error: {error_message}', 'error')
            return redirect(url_for('admin.live_settings'))

        # Read file data
        file_data = form.avatar.data.read()
        content_type = form.avatar.data.content_type

        # Crop image to square if needed
        file_data, content_type = crop_to_square(file_data, content_type)

        # Upload to Azure Blob Storage
        blob_service = BlobStorageService()

        if not blob_service.is_configured():
            # Log the issue for debugging
            connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
            if not connection_string:
                current_app.logger.error("AZURE_STORAGE_CONNECTION_STRING environment variable is not set")
                flash('Avatar storage is not configured. AZURE_STORAGE_CONNECTION_STRING is not set.', 'error')
            else:
                current_app.logger.error("Blob storage service failed to initialize despite connection string being set")
                flash('Avatar storage is not configured. Please check server logs for details.', 'error')
            return redirect(url_for('admin.live_settings'))

        # Delete all existing avatar files for this user (handles different extensions)
        blob_service.delete_user_avatars(current_user.id)

        # Upload new avatar
        blob_url = blob_service.upload_avatar(
            user_id=current_user.id,
            file_data=file_data,
            content_type=content_type
        )

        if blob_url:
            # Update user's avatar_url
            current_user.avatar_url = blob_url
            db.session.commit()
            flash('Avatar uploaded successfully', 'success')
        else:
            flash('Failed to upload avatar. Please try again.', 'error')

    except Exception as e:
        current_app.logger.error(f"Avatar upload error: {e}", exc_info=True)
        flash('An error occurred while uploading your avatar. Please try again.', 'error')
        db.session.rollback()

    return redirect(url_for('admin.live_settings'))


# Demo Routes (kept for reference)
@admin_bp.route('/demo/dashboard')
@admin_required
def demo_dashboard():
    """Demo admin dashboard with statistics."""
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


@admin_bp.route('/demo/users')
@admin_required
def demo_users():
    """Demo user management."""
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

    # Determine redirect based on referrer
    referrer = request.referrer or ''
    redirect_to = 'admin.live_users' if '/user-management' in referrer else 'admin.demo_users'

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

    return redirect(url_for(redirect_to))


@admin_bp.route('/users/<user_id>/roles/remove', methods=['POST'])
@admin_required
def remove_role(user_id):
    """Remove a role from a user."""
    form = RemoveRoleForm()

    # Determine redirect based on referrer
    referrer = request.referrer or ''
    redirect_to = 'admin.live_users' if '/user-management' in referrer else 'admin.demo_users'

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

    return redirect(url_for(redirect_to))


@admin_bp.route('/users/<user_id>/toggle-active', methods=['POST'])
@admin_required
def toggle_user_active(user_id):
    """Toggle user active status."""
    user = User.query.get_or_404(user_id)

    # Determine redirect based on referrer
    referrer = request.referrer or ''
    redirect_to = 'admin.live_users' if '/user-management' in referrer else 'admin.demo_users'

    # Prevent deactivating yourself
    if user.id == current_user.id:
        flash('You cannot deactivate your own account', 'error')
        return redirect(url_for(redirect_to))

    user.is_active = not user.is_active
    db.session.commit()

    status = 'activated' if user.is_active else 'deactivated'
    flash(f'User {user.email} has been {status}', 'success')

    return redirect(url_for(redirect_to))


# ============================================================================
# Dashboard Routes
# ============================================================================

@admin_bp.route('/demo/dashboards/analytics')
@admin_required
def demo_dashboards_analytics():
    """Analytics dashboard."""
    return render_template('admin/dashboards/analytics.html')


@admin_bp.route('/demo/dashboards/discover')
@admin_required
def demo_dashboards_discover():
    """Discover dashboard."""
    return render_template('admin/dashboards/discover.html')


@admin_bp.route('/demo/dashboards/sales')
@admin_required
def demo_dashboards_sales():
    """Sales dashboard."""
    return render_template('admin/dashboards/sales.html')


@admin_bp.route('/demo/dashboards/automotive')
@admin_required
def demo_dashboards_automotive():
    """Automotive dashboard."""
    return render_template('admin/dashboards/automotive.html')


@admin_bp.route('/demo/dashboards/smart-home')
@admin_required
def demo_dashboards_smart_home():
    """Smart Home dashboard."""
    return render_template('admin/dashboards/smart-home.html')


@admin_bp.route('/demo/dashboards/blocks-analytics')
@admin_required
def demo_dashboards_blocks_analytics():
    """Blocks Analytics dashboard."""
    return render_template('admin/dashboards/blocks-analytics.html')


# ============================================================================
# Applications Routes
# ============================================================================

@admin_bp.route('/demo/applications/calendar')
@admin_required
def demo_applications_calendar():
    """Calendar application."""
    return render_template('admin/applications/calendar.html')


@admin_bp.route('/demo/applications/crm')
@admin_required
def demo_applications_crm():
    """CRM application."""
    return render_template('admin/applications/crm.html')


@admin_bp.route('/demo/applications/datatables')
@admin_required
def demo_applications_datatables():
    """DataTables application."""
    return render_template('admin/applications/datatables.html')


@admin_bp.route('/demo/applications/kanban')
@admin_required
def demo_applications_kanban():
    """Kanban application."""
    return render_template('admin/applications/kanban.html')


@admin_bp.route('/demo/applications/stats')
@admin_required
def demo_applications_stats():
    """Stats application."""
    return render_template('admin/applications/stats.html')


@admin_bp.route('/demo/applications/validation')
@admin_required
def demo_applications_validation():
    """Validation application."""
    return render_template('admin/applications/validation.html')


@admin_bp.route('/demo/applications/wizard')
@admin_required
def demo_applications_wizard():
    """Wizard application."""
    return render_template('admin/applications/wizard.html')


# ============================================================================
# Ecommerce Routes
# ============================================================================

@admin_bp.route('/demo/ecommerce/products/list')
@admin_required
def demo_ecommerce_products_list():
    """Products list."""
    return render_template('admin/ecommerce/products/products-list.html')


@admin_bp.route('/demo/ecommerce/products/new')
@admin_required
def demo_ecommerce_products_new():
    """New product."""
    return render_template('admin/ecommerce/products/new-product.html')


@admin_bp.route('/demo/ecommerce/products/edit')
@admin_required
def demo_ecommerce_products_edit():
    """Edit product."""
    return render_template('admin/ecommerce/products/edit-product.html')


@admin_bp.route('/demo/ecommerce/products/page')
@admin_required
def demo_ecommerce_products_page():
    """Product page."""
    return render_template('admin/ecommerce/products/product-page.html')


@admin_bp.route('/demo/ecommerce/orders/list')
@admin_required
def demo_ecommerce_orders_list():
    """Orders list."""
    return render_template('admin/ecommerce/orders/list.html')


@admin_bp.route('/demo/ecommerce/orders/details')
@admin_required
def demo_ecommerce_orders_details():
    """Order details."""
    return render_template('admin/ecommerce/orders/details.html')


@admin_bp.route('/demo/ecommerce/referral')
@admin_required
def demo_ecommerce_referral():
    """Referral page."""
    return render_template('admin/ecommerce/referral.html')


# ============================================================================
# Pages Routes
# ============================================================================

@admin_bp.route('/demo/pages/charts')
@admin_required
def demo_pages_charts():
    """Charts page."""
    return render_template('admin/pages/charts.html')


@admin_bp.route('/demo/pages/notifications')
@admin_required
def demo_pages_notifications():
    """Notifications page."""
    return render_template('admin/pages/notifications.html')


@admin_bp.route('/demo/pages/pricing')
@admin_required
def demo_pages_pricing():
    """Pricing page."""
    return render_template('admin/pages/pricing-page.html')


@admin_bp.route('/demo/pages/rtl')
@admin_required
def demo_pages_rtl():
    """RTL page."""
    return render_template('admin/pages/rtl-page.html')


@admin_bp.route('/demo/pages/sweet-alerts')
@admin_required
def demo_pages_sweet_alerts():
    """Sweet alerts page."""
    return render_template('admin/pages/sweet-alerts.html')


@admin_bp.route('/demo/pages/widgets')
@admin_required
def demo_pages_widgets():
    """Widgets page."""
    return render_template('admin/pages/widgets.html')


@admin_bp.route('/demo/pages/vr/default')
@admin_required
def demo_pages_vr_default():
    """VR default page."""
    return render_template('admin/pages/vr/vr-default.html')


@admin_bp.route('/demo/pages/vr/info')
@admin_required
def demo_pages_vr_info():
    """VR info page."""
    return render_template('admin/pages/vr/vr-info.html')


# ============================================================================
# Account Routes
# ============================================================================

@admin_bp.route('/demo/account/settings')
@admin_required
def demo_account_settings():
    """Account settings."""
    return render_template('admin/account/settings.html')


@admin_bp.route('/demo/account/billing')
@admin_required
def demo_account_billing():
    """Account billing."""
    return render_template('admin/account/billing.html')


@admin_bp.route('/demo/account/invoice')
@admin_required
def demo_account_invoice():
    """Account invoice."""
    return render_template('admin/account/invoice.html')


@admin_bp.route('/demo/account/security')
@admin_required
def demo_account_security():
    """Account security."""
    return render_template('admin/account/security.html')


# ============================================================================
# Profile Routes
# ============================================================================

@admin_bp.route('/demo/profile/projects')
@admin_required
def demo_profile_projects():
    """Profile projects."""
    return render_template('admin/profile/projects.html')


# ============================================================================
# Projects Routes
# ============================================================================

@admin_bp.route('/demo/projects/general')
@admin_required
def demo_projects_general():
    """Projects general."""
    return render_template('admin/projects/general.html')


@admin_bp.route('/demo/projects/new')
@admin_required
def demo_projects_new():
    """New project."""
    return render_template('admin/projects/new-project.html')


@admin_bp.route('/demo/projects/timeline')
@admin_required
def demo_projects_timeline():
    """Projects timeline."""
    return render_template('admin/projects/timeline.html')


# ============================================================================
# Team Routes
# ============================================================================

@admin_bp.route('/demo/team/all-projects')
@admin_required
def demo_team_all_projects():
    """Team all projects."""
    return render_template('admin/team/all-projects.html')


@admin_bp.route('/demo/team/messages')
@admin_required
def demo_team_messages():
    """Team messages."""
    return render_template('admin/team/messages.html')


@admin_bp.route('/demo/team/new-user')
@admin_required
def demo_team_new_user():
    """Team new user."""
    return render_template('admin/team/new-user.html')


@admin_bp.route('/demo/team/profile-overview')
@admin_required
def demo_team_profile_overview():
    """Team profile overview."""
    return render_template('admin/team/profile-overview.html')


@admin_bp.route('/demo/team/reports')
@admin_required
def demo_team_reports():
    """Team reports."""
    return render_template('admin/team/reports.html')
