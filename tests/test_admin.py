"""
Test admin functionality and RBAC.
"""

import pytest
from flask import url_for


class TestAdminAccess:
    """Test admin access control."""
    
    def test_anonymous_access_to_admin_redirects_to_login(self, client):
        """Test anonymous user accessing admin redirects to login."""
        response = client.get('/admin/', follow_redirects=False)
        assert response.status_code == 302
        assert '/auth/login' in response.location
    
    def test_regular_user_access_to_admin_returns_403(self, client, regular_user):
        """Test regular user accessing admin returns 403."""
        # Login as regular user
        client.post('/auth/login', data={
            'email': regular_user.email,
            'password': 'userpass',
            'remember_me': False
        })
        
        # Try to access admin
        response = client.get('/admin/')
        assert response.status_code == 403
        assert b'Access Forbidden' in response.data
    
    def test_admin_user_can_access_admin_dashboard(self, client, admin_user):
        """Test admin user can access admin dashboard."""
        # Login as admin
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpass',
            'remember_me': False
        })
        
        # Access admin dashboard
        response = client.get('/admin/')
        assert response.status_code == 200
        assert b'Admin Dashboard' in response.data
    
    def test_admin_user_can_access_users_page(self, client, admin_user):
        """Test admin user can access users management page."""
        # Login as admin
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpass',
            'remember_me': False
        })
        
        # Access users page
        response = client.get('/admin/users')
        assert response.status_code == 200
        assert b'User Management' in response.data


class TestAdminDashboard:
    """Test admin dashboard functionality."""
    
    def test_admin_dashboard_shows_statistics(self, client, admin_user, regular_user, sample_project):
        """Test admin dashboard shows correct statistics."""
        # Login as admin
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpass',
            'remember_me': False
        })
        
        # Access admin dashboard
        response = client.get('/admin/')
        assert response.status_code == 200
        
        # Check statistics are displayed
        assert b'Total Users' in response.data
        assert b'Admin Users' in response.data
        assert b'Total Projects' in response.data
    
    def test_admin_dashboard_shows_recent_users(self, client, admin_user, regular_user):
        """Test admin dashboard shows recent users."""
        # Login as admin
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpass',
            'remember_me': False
        })
        
        # Access admin dashboard
        response = client.get('/admin/')
        assert response.status_code == 200
        
        # Check recent users are displayed
        assert admin_user.email.encode() in response.data
        assert regular_user.email.encode() in response.data


class TestUserManagement:
    """Test user management functionality."""
    
    def test_admin_can_view_users(self, client, admin_user, regular_user):
        """Test admin can view user list."""
        # Login as admin
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpass',
            'remember_me': False
        })
        
        # Access users page
        response = client.get('/admin/users')
        assert response.status_code == 200
        
        # Check users are displayed
        assert admin_user.email.encode() in response.data
        assert regular_user.email.encode() in response.data
    
    def test_admin_can_toggle_user_active_status(self, client, admin_user, regular_user):
        """Test admin can toggle user active status."""
        # Login as admin
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpass',
            'remember_me': False
        })
        
        # Toggle user active status
        response = client.post(f'/admin/users/{regular_user.id}/toggle-active', 
                              follow_redirects=True)
        assert response.status_code == 200
        assert b'has been deactivated' in response.data
    
    def test_admin_cannot_deactivate_self(self, client, admin_user):
        """Test admin cannot deactivate their own account."""
        # Login as admin
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpass',
            'remember_me': False
        })
        
        # Try to deactivate self
        response = client.post(f'/admin/users/{admin_user.id}/toggle-active', 
                              follow_redirects=True)
        assert response.status_code == 200
        assert b'cannot deactivate your own account' in response.data
    
    def test_regular_user_cannot_access_user_management(self, client, regular_user):
        """Test regular user cannot access user management."""
        # Login as regular user
        client.post('/auth/login', data={
            'email': regular_user.email,
            'password': 'userpass',
            'remember_me': False
        })
        
        # Try to access user management
        response = client.get('/admin/users')
        assert response.status_code == 403


class TestRoleManagement:
    """Test role management functionality."""
    
    def test_admin_can_assign_roles(self, client, admin_user, regular_user, db_session):
        """Test admin can assign roles to users."""
        # Create a test role
        from src.app.models import Role
        test_role = Role(name='test_role')
        db_session.session.add(test_role)
        db_session.session.commit()
        
        # Login as admin
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpass',
            'remember_me': False
        })
        
        # Assign role to user
        response = client.post(f'/admin/users/{regular_user.id}/roles', data={
            'role_name': 'test_role',
            'user_id': regular_user.id
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Role "test_role" assigned' in response.data
        
        # Check role was assigned
        assert regular_user.has_role('test_role') is True
    
    def test_admin_can_remove_roles(self, client, admin_user, regular_user, db_session):
        """Test admin can remove roles from users."""
        # Create and assign a test role
        from src.app.models import Role
        test_role = Role(name='test_role')
        db_session.session.add(test_role)
        db_session.session.flush()
        regular_user.roles.append(test_role)
        db_session.session.commit()
        
        # Login as admin
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpass',
            'remember_me': False
        })
        
        # Remove role from user
        response = client.post(f'/admin/users/{regular_user.id}/roles/remove', data={
            'role_name': 'test_role',
            'user_id': regular_user.id
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Role "test_role" removed' in response.data
        
        # Check role was removed
        assert regular_user.has_role('test_role') is False
    
    def test_assign_nonexistent_role_fails(self, client, admin_user, regular_user):
        """Test assigning nonexistent role fails gracefully."""
        # Login as admin
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpass',
            'remember_me': False
        })
        
        # Try to assign nonexistent role
        response = client.post(f'/admin/users/{regular_user.id}/roles', data={
            'role_name': 'nonexistent_role',
            'user_id': regular_user.id
        }, follow_redirects=True)
        
        # Should still work (role will be created)
        assert response.status_code == 200


class TestNavigation:
    """Test navigation and UI elements."""
    
    def test_admin_link_shows_for_admin_users(self, client, admin_user):
        """Test admin link shows in navigation for admin users."""
        # Login as admin
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpass',
            'remember_me': False
        })
        
        # Check navigation
        response = client.get('/')
        assert response.status_code == 200
        assert b'Admin' in response.data
    
    def test_admin_link_hidden_for_regular_users(self, client, regular_user):
        """Test admin link is hidden for regular users."""
        # Login as regular user
        client.post('/auth/login', data={
            'email': regular_user.email,
            'password': 'userpass',
            'remember_me': False
        })
        
        # Check navigation
        response = client.get('/')
        assert response.status_code == 200
        assert b'Admin' not in response.data
    
    def test_admin_link_hidden_for_anonymous_users(self, client):
        """Test admin link is hidden for anonymous users."""
        # Check navigation without login
        response = client.get('/')
        assert response.status_code == 200
        assert b'Admin' not in response.data
