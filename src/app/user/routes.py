"""
User account routes.
"""

import os
from flask import render_template, redirect, url_for, flash, current_app
from flask_login import current_user, login_required

from . import user_bp
from .forms import ChangePasswordForm, AvatarUploadForm
from ..extensions import db
from ..models import UserSession
from ..services.blob_storage import BlobStorageService
from ..utils.image_validator import validate_image_file, crop_to_square
from ..services.session_tracker import get_user_sessions, revoke_session, get_current_session_token


@user_bp.route('/')
@login_required
def index():
    """Redirect to dashboard."""
    return redirect(url_for('user.dashboard'))


@user_bp.route('/dashboard')
@login_required
def dashboard():
    """User account dashboard - blank holding page."""
    return render_template('user/dashboard.html')


@user_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """User account settings page."""
    form = ChangePasswordForm()
    avatar_form = AvatarUploadForm()

    if form.validate_on_submit():
        # Verify current password
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect', 'error')
            return render_template('user/settings.html', form=form, avatar_form=avatar_form)

        # Verify new password matches confirm password (form validation handles this, but double-check)
        if form.new_password.data != form.confirm_password.data:
            flash('New passwords do not match', 'error')
            return render_template('user/settings.html', form=form, avatar_form=avatar_form)

        # Update password
        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash('Password updated successfully', 'success')
        return redirect(url_for('user.settings'))

    # Get user sessions for display
    sessions = get_user_sessions(current_user.id)

    return render_template('user/settings.html', form=form, avatar_form=avatar_form, sessions=sessions)


@user_bp.route('/avatar/upload', methods=['POST'])
@login_required
def upload_avatar():
    """Handle avatar image upload."""
    form = AvatarUploadForm()

    if not form.validate_on_submit():
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Avatar upload error: {error}', 'error')
        return redirect(url_for('user.settings'))

    try:
        # Validate image file
        is_valid, error_message = validate_image_file(
            form.avatar.data,
            max_size=current_app.config.get('MAX_AVATAR_SIZE', 5242880)
        )

        if not is_valid:
            flash(f'Avatar upload error: {error_message}', 'error')
            return redirect(url_for('user.settings'))

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
            return redirect(url_for('user.settings'))

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

    return redirect(url_for('user.settings'))


@user_bp.route('/sessions/<session_id>/revoke', methods=['POST'])
@login_required
def revoke_user_session(session_id):
    """Revoke a user session."""
    try:
        # Get the session to check ownership
        user_session = UserSession.query.get_or_404(session_id)
        
        # Ensure user owns this session
        if user_session.user_id != current_user.id:
            flash('You do not have permission to revoke this session.', 'error')
            return redirect(url_for('user.settings'))
        
        # Check if this is the current session
        current_session_token = get_current_session_token()
        is_current = user_session.session_token == current_session_token
        
        # Revoke the session
        if revoke_session(session_id, current_user.id):
            if is_current:
                # If revoking current session, log out immediately
                from flask_login import logout_user
                logout_user()
                flash('Your session has been revoked. You have been logged out.', 'info')
                return redirect(url_for('auth.login'))
            else:
                flash('Session revoked successfully.', 'success')
        else:
            flash('Failed to revoke session.', 'error')
    except Exception as e:
        current_app.logger.error(f"Error revoking session: {e}", exc_info=True)
        flash('An error occurred while revoking the session.', 'error')
    
    return redirect(url_for('user.settings'))

