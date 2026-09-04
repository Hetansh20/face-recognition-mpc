from flask import Blueprint, request, g
from backend.services.auth_service import auth_service
from backend.utils.response import api_response, api_error
from backend.middleware.authentication import token_required

auth_bp = Blueprint("auth_bp", __name__, url_prefix="/api/v1/auth")

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("email") or data.get("username")
    password = data.get("password") or data.get("passcode")

    if not username or not password:
        return api_error("Username/Email and password/passcode are required", code="INVALID_CREDENTIALS", status_code=400)

    result, err = auth_service.login(username, password)
    if err:
        return api_error(err, code="UNAUTHORIZED", status_code=401)
    return api_response(data=result, message="Login successful")

@auth_bp.route("/refresh", methods=["POST"])
def refresh():
    data = request.get_json(silent=True) or {}
    refresh_token = data.get("refresh_token")
    if not refresh_token:
        return api_error("Refresh token is required", code="INVALID_TOKEN", status_code=400)

    result, err = auth_service.refresh_token(refresh_token)
    if err:
        return api_error(err, code="UNAUTHORIZED", status_code=401)
    return api_response(data=result, message="Token refreshed successfully")

@auth_bp.route("/logout", methods=["POST"])
@token_required
def logout():
    data = request.get_json(silent=True) or {}
    refresh_token = data.get("refresh_token")
    auth_service.logout(g.current_user["id"], refresh_token)
    return api_response(message="Logout successful")

@auth_bp.route("/me", methods=["GET"])
@token_required
def me():
    profile = auth_service.get_user_profile(g.current_user["id"])
    if not profile:
        return api_error("User profile not found", code="NOT_FOUND", status_code=404)
    return api_response(data=profile)

@auth_bp.route("/change-password", methods=["POST"])
@token_required
def change_password():
    data = request.get_json(silent=True) or {}
    old_pass = data.get("old_password")
    new_pass = data.get("new_password")

    if not old_pass or not new_pass:
        return api_error("Both old_password and new_password are required", code="BAD_REQUEST", status_code=400)

    success, msg = auth_service.change_password(g.current_user["id"], old_pass, new_pass)
    if not success:
        return api_error(msg, code="BAD_REQUEST", status_code=400)
    return api_response(message=msg)
