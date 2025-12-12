"""
Test configuration and fixtures.
"""

import pytest
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate

from src.app import create_app
from src.app.extensions import db
from src.app.models import User, Role, Project


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def db_session(app):
    """Create database session for testing."""
    with app.app_context():
        yield db


@pytest.fixture
def admin_user(db_session):
    """Create admin user for testing."""
    # Create admin role
    admin_role = Role(name='admin')
    db_session.session.add(admin_role)
    db_session.session.flush()
    
    # Create admin user
    user = User(email='admin@test.com', username='admin')
    user.set_password('adminpass')
    user.roles.append(admin_role)
    db_session.session.add(user)
    db_session.session.commit()
    
    return user


@pytest.fixture
def regular_user(db_session):
    """Create regular user for testing."""
    user = User(email='user@test.com', username='testuser')
    user.set_password('userpass')
    db_session.session.add(user)
    db_session.session.commit()
    
    return user


@pytest.fixture
def sample_project(db_session, regular_user):
    """Create sample project for testing."""
    project = Project(
        name='Test Project',
        description='A test project',
        owner_id=regular_user.id
    )
    db_session.session.add(project)
    db_session.session.commit()
    
    return project


@pytest.fixture
def auth_headers(client, regular_user):
    """Get authentication headers for API testing."""
    # Login to get session
    response = client.post('/auth/login', data={
        'username_or_email': regular_user.username,
        'password': 'userpass',
        'remember_me': False
    }, follow_redirects=True)
    
    return response.headers


@pytest.fixture
def admin_headers(client, admin_user):
    """Get admin authentication headers for API testing."""
    # Login as admin
    response = client.post('/auth/login', data={
        'username_or_email': admin_user.username,
        'password': 'adminpass',
        'remember_me': False
    }, follow_redirects=True)
    
    return response.headers
