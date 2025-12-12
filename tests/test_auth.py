"""
Test authentication functionality.
"""

import pytest
from flask import url_for
from flask_login import current_user

from src.app.models import User


class TestAuthRoutes:
    """Test authentication routes."""
    
    def test_register_get(self, client):
        """Test registration page loads."""
        response = client.get('/auth/register')
        assert response.status_code == 200
        assert b'Register' in response.data
    
    def test_register_post_valid(self, client, db_session):
        """Test successful user registration."""
        response = client.post('/auth/register', data={
            'email': 'newuser@test.com',
            'username': 'newuser',
            'password': 'newpass123',
            'confirm_password': 'newpass123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Registration successful' in response.data
        
        # Check user was created
        user = User.query.filter_by(email='newuser@test.com').first()
        assert user is not None
        assert user.username == 'newuser'
        assert user.check_password('newpass123')
    
    def test_register_post_duplicate_email(self, client, regular_user):
        """Test registration with duplicate email."""
        response = client.post('/auth/register', data={
            'email': regular_user.email,
            'username': 'differentuser',
            'password': 'newpass123',
            'confirm_password': 'newpass123'
        })
        
        assert response.status_code == 200
        assert b'Email is already registered' in response.data
    
    def test_register_post_duplicate_username(self, client, regular_user):
        """Test registration with duplicate username."""
        response = client.post('/auth/register', data={
            'email': 'different@test.com',
            'username': regular_user.username,
            'password': 'newpass123',
            'confirm_password': 'newpass123'
        })
        
        assert response.status_code == 200
        assert b'Username is already taken' in response.data
    
    def test_register_post_username_too_long(self, client):
        """Test registration with username exceeding 13 characters."""
        response = client.post('/auth/register', data={
            'email': 'newuser@test.com',
            'username': 'a' * 14,  # 14 characters
            'password': 'newpass123',
            'confirm_password': 'newpass123'
        })
        
        assert response.status_code == 200
        assert b'13 characters or less' in response.data
    
    def test_register_post_username_invalid_chars(self, client):
        """Test registration with username containing invalid characters."""
        response = client.post('/auth/register', data={
            'email': 'newuser@test.com',
            'username': 'user-name',  # Contains hyphen
            'password': 'newpass123',
            'confirm_password': 'newpass123'
        })
        
        assert response.status_code == 200
        assert b'only contain letters, numbers, and underscores' in response.data
    
    def test_register_post_password_mismatch(self, client):
        """Test registration with password mismatch."""
        response = client.post('/auth/register', data={
            'email': 'newuser@test.com',
            'username': 'newuser',
            'password': 'newpass123',
            'confirm_password': 'differentpass'
        })
        
        assert response.status_code == 200
        assert b'Passwords must match' in response.data
    
    def test_login_get(self, client):
        """Test login page loads."""
        response = client.get('/auth/login')
        assert response.status_code == 200
        assert b'Login' in response.data
    
    def test_login_post_valid_username(self, client, regular_user):
        """Test successful login with username."""
        response = client.post('/auth/login', data={
            'username_or_email': regular_user.username,
            'password': 'userpass',
            'remember_me': False
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Welcome back' in response.data
    
    def test_login_post_valid_email(self, client, regular_user):
        """Test successful login with email."""
        response = client.post('/auth/login', data={
            'username_or_email': regular_user.email,
            'password': 'userpass',
            'remember_me': False
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Welcome back' in response.data
    
    def test_login_post_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        response = client.post('/auth/login', data={
            'username_or_email': 'nonexistent@test.com',
            'password': 'wrongpass',
            'remember_me': False
        })
        
        assert response.status_code == 200
        assert b'Invalid username/email or password' in response.data
    
    def test_login_post_inactive_user(self, client, db_session):
        """Test login with inactive user."""
        user = User(email='inactive@test.com', username='inactive')
        user.set_password('testpass')
        user.is_active = False
        db_session.session.add(user)
        db_session.session.commit()
        
        response = client.post('/auth/login', data={
            'username_or_email': user.username,
            'password': 'testpass',
            'remember_me': False
        })
        
        assert response.status_code == 200
        assert b'account has been deactivated' in response.data
    
    def test_logout(self, client, regular_user):
        """Test user logout."""
        # Login first
        client.post('/auth/login', data={
            'username_or_email': regular_user.username,
            'password': 'userpass',
            'remember_me': False
        })
        
        # Logout
        response = client.get('/auth/logout', follow_redirects=True)
        assert response.status_code == 200
        assert b'You have been logged out' in response.data
    
    def test_forgot_password_get(self, client):
        """Test forgot password page loads."""
        response = client.get('/auth/forgot-password')
        assert response.status_code == 200
        assert b'Forgot Password' in response.data
    
    def test_forgot_password_post(self, client, regular_user):
        """Test forgot password form submission."""
        response = client.post('/auth/forgot-password', data={
            'email': regular_user.email
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Password reset functionality not yet implemented' in response.data


class TestAuthRedirects:
    """Test authentication redirects."""
    
    def test_anonymous_access_to_dashboard_redirects_to_login(self, client):
        """Test anonymous user accessing dashboard redirects to login."""
        response = client.get('/dashboard', follow_redirects=False)
        assert response.status_code == 302
        assert '/auth/login' in response.location
    
    def test_authenticated_user_can_access_dashboard(self, client, regular_user):
        """Test authenticated user can access dashboard."""
        # Login
        client.post('/auth/login', data={
            'username_or_email': regular_user.username,
            'password': 'userpass',
            'remember_me': False
        })
        
        # Access dashboard
        response = client.get('/dashboard')
        assert response.status_code == 200
        assert b'Dashboard' in response.data
    
    def test_login_redirects_to_next_page(self, client, regular_user):
        """Test login redirects to next page after authentication."""
        # Try to access dashboard without login
        response = client.get('/dashboard', follow_redirects=False)
        assert response.status_code == 302
        
        # Login
        response = client.post('/auth/login', data={
            'username_or_email': regular_user.username,
            'password': 'userpass',
            'remember_me': False
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Dashboard' in response.data
