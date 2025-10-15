"""
CLI commands for the Flask application.
"""

import click
from flask import current_app
from flask.cli import with_appcontext

from .extensions import db
from .models import User, Role
from .security.roles import ensure_role_exists


@click.command()
@click.option('--email', prompt=True, help='Admin email address')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='Admin password')
@with_appcontext
def create_admin(email, password):
    """Create an admin user with the specified email and password."""
    try:
        # Check if user already exists
        user = User.query.filter_by(email=email.lower()).first()
        
        if user:
            click.echo(f"User {email} already exists.")
            
            # Ensure admin role exists and assign it
            admin_role = ensure_role_exists('admin')
            if user.add_role('admin'):
                db.session.commit()
                click.echo(f"Admin role assigned to existing user {email}")
            else:
                click.echo(f"User {email} already has admin role")
        else:
            # Create new user
            user = User(email=email.lower())
            user.set_password(password)
            db.session.add(user)
            db.session.flush()  # Get the user ID
            
            # Ensure admin role exists and assign it
            admin_role = ensure_role_exists('admin')
            user.add_role('admin')
            
            db.session.commit()
            click.echo(f"Admin user {email} created successfully")
            
    except Exception as e:
        click.echo(f"Error creating admin user: {str(e)}")
        db.session.rollback()
        raise click.Abort()


@click.command()
@click.option('--email', prompt=True, help='User email address')
@click.option('--role', prompt=True, help='Role name to assign')
@with_appcontext
def assign_role(email, role):
    """Assign a role to a user."""
    try:
        user = User.query.filter_by(email=email.lower()).first()
        
        if not user:
            click.echo(f"User {email} not found.")
            return
        
        # Ensure role exists
        role_obj = ensure_role_exists(role)
        
        if user.add_role(role):
            db.session.commit()
            click.echo(f"Role '{role}' assigned to {email}")
        else:
            click.echo(f"User {email} already has role '{role}'")
            
    except Exception as e:
        click.echo(f"Error assigning role: {str(e)}")
        db.session.rollback()
        raise click.Abort()


@click.command()
@click.option('--role', prompt=True, help='Role name to create')
@with_appcontext
def create_role(role):
    """Create a new role."""
    try:
        # Check if role already exists
        existing_role = Role.query.filter_by(name=role).first()
        
        if existing_role:
            click.echo(f"Role '{role}' already exists.")
            return
        
        # Create new role
        new_role = Role(name=role)
        db.session.add(new_role)
        db.session.commit()
        click.echo(f"Role '{role}' created successfully")
        
    except Exception as e:
        click.echo(f"Error creating role: {str(e)}")
        db.session.rollback()
        raise click.Abort()


def register_commands(app):
    """Register CLI commands with the Flask app."""
    app.cli.add_command(create_admin)
    app.cli.add_command(assign_role)
    app.cli.add_command(create_role)
