from functools import wraps
from flask import request, g
from backend.utils.security import decode_access_token
from backend.utils.response import api_error

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return api_error("Authorization header is missing", code="UNAUTHORIZED", status_code=401)
        
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return api_error("Invalid Authorization header format. Expected 'Bearer <token>'", code="UNAUTHORIZED", status_code=401)
        
        token = parts[1]
        payload = decode_access_token(token)
        if not payload:
            return api_error("Token is invalid or has expired", code="UNAUTHORIZED", status_code=401)
        
        g.current_user = {
            "id": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role")
        }
        return f(*args, **kwargs)
    return decorated

def optional_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        g.current_user = None
        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == "bearer":
                payload = decode_access_token(parts[1])
                if payload:
                    g.current_user = {
                        "id": payload.get("sub"),
                        "email": payload.get("email"),
                        "role": payload.get("role")
                    }
        return f(*args, **kwargs)
    return decorated
