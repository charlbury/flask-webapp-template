"""
Admin forms.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import SelectField, HiddenField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from flask import current_app

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


class AvatarUploadForm(FlaskForm):
    """Form for uploading avatar image."""

    avatar = FileField('Avatar', validators=[
        FileRequired(message='Please select an image file'),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], message='Only image files are allowed (jpg, jpeg, png, gif, webp)')
    ])
    submit = SubmitField('Upload Avatar')

    def validate_avatar(self, field):
        """Custom validation for avatar file."""
        if not field.data:
            return

        # Check file size
        max_size = current_app.config.get('MAX_AVATAR_SIZE', 5242880)
        field.data.seek(0, 2)  # Seek to end
        file_size = field.data.tell()
        field.data.seek(0)  # Reset to beginning

        if file_size > max_size:
            max_size_mb = max_size / (1024 * 1024)
            raise ValidationError(f'File size must be less than {max_size_mb}MB')

        if file_size == 0:
            raise ValidationError('File is empty')
