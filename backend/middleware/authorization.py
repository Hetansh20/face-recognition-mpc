from functools import wraps
from flask import g
from backend.utils.response import api_error

def require_roles(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(g, 'current_user') or not g.current_user:
                return api_error("User authentication required", code="UNAUTHORIZED", status_code=401)
            
            user_role = g.current_user.get("role", "").upper()
            allowed_roles = [r.upper() for r in roles]
            
            if user_role not in allowed_roles:
                return api_error(f"Role '{user_role}' is not authorized to access this resource", code="FORBIDDEN", status_code=403)
            
            return f(*args, **kwargs)
        return decorated
    return decorator
