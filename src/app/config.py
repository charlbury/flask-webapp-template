"""
Configuration classes for different environments.
"""

import os
from urllib.parse import quote_plus


class Config:
    """Base configuration class."""
    VERSION = "0.1.1"
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Security settings
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    WTF_CSRF_TIME_LIMIT = 3600

    # Content Security Policy for Bootstrap CDN
    CSP_HEADERS = {
        'default-src': "'self'",
        'script-src': "'self' 'unsafe-inline' https://cdn.jsdelivr.net",
        'style-src': "'self' 'unsafe-inline' https://cdn.jsdelivr.net",
        'font-src': "'self' https://cdn.jsdelivr.net",
        'img-src': "'self' data:",
        'connect-src': "'self'"
    }


def _build_azure_sql_uri() -> str:
    """Build Azure SQL connection URI from environment variables."""
    server = os.getenv('AZURE_SQL_SERVER')
    database = os.getenv('AZURE_SQL_DB')
    username = os.getenv('AZURE_SQL_USER')
    password = os.getenv('AZURE_SQL_PASSWORD')
    odbc_driver = os.getenv('ODBC_DRIVER', 'ODBC Driver 18 for SQL Server')

    if not all([server, database, username, password]):
        # Fallback to SQLite for local development
        return 'sqlite:///app.db'

    # URL encode the password to handle special characters
    password_encoded = quote_plus(password)

    # Build ODBC connection string
    odbc_connect = (
        f"Driver={{{odbc_driver}}};"
        f"Server=tcp:{server},1433;"
        f"Database={database};"
        f"Uid={username};"
        f"Pwd={password_encoded};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=no;"
        f"Connection Timeout=30;"
    )

    # URL encode the entire connection string
    odbc_connect_encoded = quote_plus(odbc_connect)

    return f"mssql+pyodbc:///?odbc_connect={odbc_connect_encoded}"


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    SQLALCHEMY_DATABASE_URI = _build_azure_sql_uri()


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False

    # Secure cookies in production
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True

    SQLALCHEMY_DATABASE_URI = _build_azure_sql_uri()

    # Additional security headers
    @staticmethod
    def init_app(app):
        """Initialize production-specific settings."""
        # TODO: Add rate limiting
        # TODO: Add audit logging
        pass


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}