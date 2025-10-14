"""
Role-based access control decorators and utilities.
"""

from functools import wraps
from flask import abort, current_app
from flask_login import current_user, login_required
from sqlalchemy.orm import joinedload

from ..extensions import db
from ..models import Role


def roles_required(*role_names):
    """
    Decorator that requires the user to have at least one of the specified roles.
    
    Args:
        *role_names: Names of roles that are allowed access
        
    Returns:
        Decorated function that checks role permissions
    """
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(403)
            
            # Check if user has any of the required roles
            user_roles = current_user.roles.with_entities(Role.name).all()
            user_role_names = [role.name for role in user_roles]
            
            if not any(role_name in user_role_names for role_name in role_names):
                current_app.logger.warning(
                    f"User {current_user.email} attempted to access {f.__name__} "
                    f"but lacks required roles: {role_names}"
                )
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """
    Decorator that requires the user to have admin role.
    
    Args:
        f: Function to decorate
        
    Returns:
        Decorated function that checks admin permissions
    """
    return roles_required('admin')(f)


def ensure_role_exists(role_name: str) -> Role:
    """
    Ensure a role exists in the database, create it if it doesn't.
    
    Args:
        role_name: Name of the role to ensure exists
        
    Returns:
        Role instance
    """
    role = Role.query.filter_by(name=role_name).first()
    if not role:
        role = Role(name=role_name)
        db.session.add(role)
        db.session.commit()
        current_app.logger.info(f"Created role: {role_name}")
    return role
