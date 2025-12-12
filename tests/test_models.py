"""
Test database models.
"""

import pytest
from src.app.models import User, Role, Project
from src.app.extensions import db


class TestUserModel:
    """Test User model functionality."""
    
    def test_user_creation(self, db_session):
        """Test user creation."""
        user = User(email='test@example.com', username='testuser')
        user.set_password('testpass')
        db_session.session.add(user)
        db_session.session.commit()
        
        assert user.id is not None
        assert user.email == 'test@example.com'
        assert user.username == 'testuser'
        assert user.check_password('testpass')
        assert user.is_active is True
    
    def test_user_password_hashing(self, db_session):
        """Test password hashing and verification."""
        user = User(email='test@example.com', username='testuser')
        user.set_password('testpass')
        
        # Password should be hashed
        assert user.password_hash != 'testpass'
        assert user.password_hash is not None
        
        # Should be able to verify correct password
        assert user.check_password('testpass') is True
        assert user.check_password('wrongpass') is False
    
    def test_user_email_uniqueness(self, db_session):
        """Test email uniqueness constraint."""
        user1 = User(email='test@example.com', username='testuser1')
        user1.set_password('testpass')
        db_session.session.add(user1)
        db_session.session.commit()
        
        # Try to create another user with same email
        user2 = User(email='test@example.com', username='testuser2')
        user2.set_password('testpass')
        db_session.session.add(user2)
        
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.session.commit()
    
    def test_user_username_uniqueness(self, db_session):
        """Test username uniqueness constraint."""
        user1 = User(email='test1@example.com', username='testuser')
        user1.set_password('testpass')
        db_session.session.add(user1)
        db_session.session.commit()
        
        # Try to create another user with same username
        user2 = User(email='test2@example.com', username='testuser')
        user2.set_password('testpass')
        db_session.session.add(user2)
        
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.session.commit()
    
    def test_user_roles_relationship(self, db_session):
        """Test user-roles many-to-many relationship."""
        # Create roles
        admin_role = Role(name='admin')
        user_role = Role(name='user')
        db_session.session.add_all([admin_role, user_role])
        db_session.session.flush()
        
        # Create user
        user = User(email='test@example.com', username='testuser')
        user.set_password('testpass')
        user.roles.extend([admin_role, user_role])
        db_session.session.add(user)
        db_session.session.commit()
        
        # Check relationships
        assert len(user.roles.all()) == 2
        assert user.has_role('admin') is True
        assert user.has_role('user') is True
        assert user.has_role('nonexistent') is False
    
    def test_user_is_admin_property(self, db_session):
        """Test is_admin property."""
        # Create admin role
        admin_role = Role(name='admin')
        db_session.session.add(admin_role)
        db_session.session.flush()
        
        # Create admin user
        admin_user = User(email='admin@example.com', username='adminuser')
        admin_user.set_password('adminpass')
        admin_user.roles.append(admin_role)
        db_session.session.add(admin_user)
        
        # Create regular user
        regular_user = User(email='user@example.com', username='regularuser')
        regular_user.set_password('userpass')
        db_session.session.add(regular_user)
        
        db_session.session.commit()
        
        assert admin_user.is_admin is True
        assert regular_user.is_admin is False
    
    def test_user_add_remove_roles(self, db_session):
        """Test adding and removing roles."""
        # Create role
        role = Role(name='test_role')
        db_session.session.add(role)
        db_session.session.flush()
        
        # Create user
        user = User(email='test@example.com', username='testuser')
        user.set_password('testpass')
        db_session.session.add(user)
        db_session.session.commit()
        
        # Add role
        assert user.add_role('test_role') is True
        assert user.has_role('test_role') is True
        
        # Try to add same role again
        assert user.add_role('test_role') is False
        
        # Remove role
        assert user.remove_role('test_role') is True
        assert user.has_role('test_role') is False
        
        # Try to remove non-existent role
        assert user.remove_role('nonexistent') is False


class TestRoleModel:
    """Test Role model functionality."""
    
    def test_role_creation(self, db_session):
        """Test role creation."""
        role = Role(name='test_role')
        db_session.session.add(role)
        db_session.session.commit()
        
        assert role.id is not None
        assert role.name == 'test_role'
    
    def test_role_name_uniqueness(self, db_session):
        """Test role name uniqueness constraint."""
        role1 = Role(name='test_role')
        db_session.session.add(role1)
        db_session.session.commit()
        
        # Try to create another role with same name
        role2 = Role(name='test_role')
        db_session.session.add(role2)
        
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.session.commit()
    
    def test_role_users_relationship(self, db_session):
        """Test role-users many-to-many relationship."""
        # Create role
        role = Role(name='test_role')
        db_session.session.add(role)
        db_session.session.flush()
        
        # Create users
        user1 = User(email='user1@example.com', username='user1')
        user1.set_password('pass1')
        user2 = User(email='user2@example.com', username='user2')
        user2.set_password('pass2')
        
        # Add users to role
        role.users.extend([user1, user2])
        db_session.session.add_all([user1, user2])
        db_session.session.commit()
        
        # Check relationships
        assert len(role.users.all()) == 2


class TestProjectModel:
    """Test Project model functionality."""
    
    def test_project_creation(self, db_session, regular_user):
        """Test project creation."""
        project = Project(
            name='Test Project',
            description='A test project',
            owner_id=regular_user.id
        )
        db_session.session.add(project)
        db_session.session.commit()
        
        assert project.id is not None
        assert project.name == 'Test Project'
        assert project.description == 'A test project'
        assert project.owner_id == regular_user.id
    
    def test_project_owner_relationship(self, db_session, regular_user):
        """Test project-owner relationship."""
        project = Project(
            name='Test Project',
            owner_id=regular_user.id
        )
        db_session.session.add(project)
        db_session.session.commit()
        
        # Check relationship
        assert project.owner == regular_user
        assert project in regular_user.projects.all()
