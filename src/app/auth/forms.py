"""
Authentication forms.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError

from ..models import User


class RegisterForm(FlaskForm):
    """User registration form."""
    
    email = StringField('Email', validators=[
        DataRequired(),
        Email(),
        Length(max=255)
    ])
    first_name = StringField('First Name', validators=[
        Length(max=100)
    ])
    last_name = StringField('Last Name', validators=[
        Length(max=100)
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, max=128)
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Register')
    
    def validate_email(self, field):
        """Validate that email is not already registered."""
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('Email is already registered')


class LoginForm(FlaskForm):
    """User login form."""
    
    email = StringField('Email', validators=[
        DataRequired(),
        Email()
    ])
    password = PasswordField('Password', validators=[
        DataRequired()
    ])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')


class ForgotPasswordForm(FlaskForm):
    """Forgot password form."""
    
    email = StringField('Email', validators=[
        DataRequired(),
        Email()
    ])
    submit = SubmitField('Send Reset Link')
    
    def validate_email(self, field):
        """Validate that email exists."""
        if not User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('Email not found')
