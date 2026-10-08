"""
Authorization decorators for EcoBuild.
Server-side enforcement — do not rely on hiding UI elements.
"""
from functools import wraps

from flask import abort
from flask_login import current_user


def admin_required(f):
    """Require the current user to be authenticated AND have role='admin'.
    Returns 403 if the user is not an admin (even if logged in).
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated


def owner_required(model_class, id_kwarg: str, owner_field: str = "user_id"):
    """Factory decorator that loads a record by primary key from id_kwarg,
    verifies the record's owner_field matches current_user.user_id,
    and aborts 404/403 otherwise.

    Usage:
        @owner_required(BuildingAnalysis, "analysis_id")
        def view_analysis(analysis_id):
            ...  # analysis object is NOT injected — load inside view
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            record_id = kwargs.get(id_kwarg)
            record = model_class.query.get_or_404(record_id)
            if getattr(record, owner_field) != current_user.user_id:
                abort(403)
            return f(*args, **kwargs)
        return decorated
    return decorator
