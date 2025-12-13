"""
Authentication routes.
"""

from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse

from . import auth_bp
from .forms import RegisterForm, LoginForm, ForgotPasswordForm
from .services import create_user
from ..models import User
from ..extensions import db
from ..services.session_tracker import create_session


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration."""
    if current_user.is_authenticated:
        # Redirect admins to dashboard, others to home page
        if current_user.is_admin:
            return redirect(url_for('admin.live_dashboard'))
        else:
            return redirect(url_for('main.index'))

    form = RegisterForm()
    if form.validate_on_submit():
        user = create_user(
            email=form.email.data.lower(),
            password=form.password.data,
            username=form.username.data,
            first_name=form.first_name.data.strip(),
            last_name=form.last_name.data.strip()
        )

        if user:
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Email or username is already registered.', 'error')

    return render_template('auth/register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login."""
    if current_user.is_authenticated:
        # Redirect admins to dashboard, others to home page
        if current_user.is_admin:
            return redirect(url_for('admin.live_dashboard'))
        else:
            return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        # Try username first (case-insensitive)
        user = User.query.filter_by(username=form.username_or_email.data.lower()).first()

        # If not found, try email (case-insensitive)
        if not user:
            user = User.query.filter_by(email=form.username_or_email.data.lower()).first()

        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Your account has been deactivated.', 'error')
                return render_template('auth/login.html', form=form)

            login_user(user, remember=form.remember_me.data)

            # Create session tracking record
            try:
                # Generate session token and store in Flask session
                import uuid
                session_token = str(uuid.uuid4())
                session['session_token'] = session_token
                
                # Create UserSession record
                create_session(user, session_token=session_token)
            except Exception as e:
                # Log error but don't fail login if session tracking fails
                from flask import current_app
                current_app.logger.error(f"Failed to create session record: {e}")

            # Redirect to next page, dashboard (if admin), or home page
            next_page = request.args.get('next')
            if not next_page or urlparse(next_page).netloc != '':
                # Redirect admins to dashboard, others to home page
                if user.is_admin:
                    next_page = url_for('admin.live_dashboard')
                else:
                    next_page = url_for('main.index')

            # Use username if available, otherwise email
            display_name = user.username if user.username else user.email
            flash(f'Welcome back, {display_name}!', 'success')
            return redirect(next_page)
        else:
            flash('Invalid username/email or password.', 'error')

    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout."""
    # Mark current session as inactive before logout
    try:
        from ..services.session_tracker import get_current_session_token, revoke_session
        session_token = get_current_session_token()
        if session_token:
            # Find and revoke the session
            from ..models import UserSession
            user_session = UserSession.query.filter_by(
                session_token=session_token,
                user_id=current_user.id
            ).first()
            if user_session:
                revoke_session(user_session.id, current_user.id)
    except Exception as e:
        from flask import current_app
        current_app.logger.error(f"Failed to revoke session on logout: {e}")
    
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password form (stub implementation)."""
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        # TODO: Implement password reset functionality
        flash('Password reset functionality not yet implemented.', 'info')
        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html', form=form)
