"""
Admin forms.
"""

from flask_wtf import FlaskForm
from wtforms import SelectField, HiddenField, SubmitField
from wtforms.validators import DataRequired

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
