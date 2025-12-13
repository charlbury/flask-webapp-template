"""
User blueprint for account management functions.
"""

from flask import Blueprint

user_bp = Blueprint('user', __name__)

from . import routes

