from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user


def rol_requerido(*roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            rol_actual = current_user.rol.nombre if current_user.rol else ''
            if rol_actual not in roles:
                flash('No tienes permiso para acceder a este modulo', 'warning')
                return redirect(url_for('admin.dashboard'))
            return func(*args, **kwargs)
        return wrapper
    return decorator
