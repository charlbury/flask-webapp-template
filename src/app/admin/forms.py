"""
Admin forms.
"""

from flask_wtf import FlaskForm
from wtforms import SelectField, HiddenField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError

from ..models import Role


class AssignRoleForm(FlaskForm):
    """Form for assigning roles to users."""
    
    role_name = SelectField('Role', validators=[DataRequired()], coerce=str)
    user_id = HiddenField('User ID', validators=[DataRequired()])
    submit = SubmitField('Assign Role')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate role choices
        self.role_name.choices = [
            (role.name, role.name) for role in Role.query.all()
        ]


class RemoveRoleForm(FlaskForm):
    """Form for removing roles from users."""
    
    role_name = SelectField('Role', validators=[DataRequired()], coerce=str)
    user_id = HiddenField('User ID', validators=[DataRequired()])
    submit = SubmitField('Remove Role')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate role choices
        self.role_name.choices = [
            (role.name, role.name) for role in Role.query.all()
        ]


class ChangePasswordForm(FlaskForm):
    """Form for changing user password."""
    
    current_password = PasswordField('Current Password', validators=[
        DataRequired()
    ])
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=6, max=128, message='Password must be between 6 and 128 characters')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('new_password', message='New passwords must match')
    ])
    submit = SubmitField('Update Password')
