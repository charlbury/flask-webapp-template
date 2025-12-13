"""
Flask application factory for Azure SQL Flask app with RBAC.
"""

import os
from flask import Flask, render_template
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from dotenv import load_dotenv

from .config import config
from .extensions import db, login_manager, csrf, migrate
from .models import User, Role, Project
from .security.roles import admin_required
from .db_utils import retry_db_operation


def create_app(config_name: str = None) -> Flask:
    """Create and configure the Flask application."""
    # Load environment variables from .env file
    load_dotenv()

    app = Flask(__name__)

    # Determine configuration
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)

    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    @retry_db_operation(max_retries=6, initial_delay=2, max_delay=10)
    def load_user(user_id):
        return User.query.get(user_id)

    # Register blueprints
    from .auth import auth_bp
    from .main import main_bp
    from .admin import admin_bp
    from .user import user_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(user_bp, url_prefix='/user')

    # Error handlers
    @app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500

    # Context processors
    @app.context_processor
    def inject_app_info():
        """Inject application information into all templates."""
        from .config import config
        from sqlalchemy import create_engine
        from urllib.parse import urlparse

        # Get current config
        current_config = config[config_name]

        # Determine database type
        db_uri = current_config.SQLALCHEMY_DATABASE_URI
        if db_uri.startswith('sqlite'):
            db_type = "SQLite (Development)"
        elif db_uri.startswith('mssql'):
            db_type = "Azure SQL Server (Production)"
        else:
            db_type = "Unknown"

        return {
            'app_version': current_config.VERSION,
            'database_type': db_type,
            'debug_mode': app.debug
        }

    # CLI commands
    from .cli import register_commands
    register_commands(app)

    return app
