from flask_login import UserMixin
from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user

class User(UserMixin):
    """User class for Flask-Login"""
    def __init__(self, id, username, role):
        self.id = str(id)
        self.username = username
        self.role = role
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    @property
    def is_staff(self):
        return self.role == 'staff'
    
    def get_id(self):
        return self.id

def role_required(*roles):
    """Decorator to restrict access to specific roles"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'error')
                return redirect(url_for('login'))
            if current_user.role not in roles:
                flash('You do not have permission to access this page.', 'error')
                return abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Decorator for admin-only routes"""
    return role_required('admin')(f)

def staff_required(f):
    """Decorator for staff-only routes (admin also allowed)"""
    return role_required('staff', 'admin')(f)