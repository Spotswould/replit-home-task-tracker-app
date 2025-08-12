from functools import wraps
from flask import redirect, url_for, flash, abort
from flask_login import current_user

def login_required(f):
    """Decorator to require user login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        if not current_user.is_admin():
            flash('Access denied. Admin privileges required.', 'danger')
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def worker_required(f):
    """Decorator to require worker role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        if not current_user.is_worker():
            flash('Access denied. Worker privileges required.', 'danger')
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def owns_worker(worker_id):
    """Check if current admin owns the worker"""
    if not current_user.is_admin():
        return False
    from models import User
    worker = User.query.get(worker_id)
    return worker and worker.admin_id == current_user.id

def owns_task(task_id):
    """Check if current admin owns the task"""
    if not current_user.is_admin():
        return False
    from models import Task
    task = Task.query.get(task_id)
    return task and task.created_by == current_user.id

def can_complete_task(task_id):
    """Check if current worker can complete the task"""
    if not current_user.is_worker():
        return False
    from models import Task
    task = Task.query.get(task_id)
    return task and task.created_by == current_user.admin_id
