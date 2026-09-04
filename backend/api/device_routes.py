from flask import Blueprint, request, g
from backend.services.device_service import device_service
from backend.utils.response import api_response, api_error
from backend.middleware.authentication import token_required, optional_token
from backend.middleware.authorization import require_roles

device_bp = Blueprint("device_bp", __name__, url_prefix="/api/v1/devices")

@device_bp.route("/register", methods=["POST"])
@optional_token
def register_device():
    data = request.get_json(silent=True) or {}
    device_id = data.get("device_id") or request.headers.get("X-Device-ID")
    if not device_id:
        return api_error("device_id is required", code="BAD_REQUEST", status_code=400)

    user_id = g.current_user["id"] if hasattr(g, 'current_user') and g.current_user else None
    dev = device_service.register_or_update_device(
        device_id=device_id,
        user_id=user_id,
        device_name=data.get("device_name") or request.headers.get("X-Device-Model"),
        platform=data.get("platform") or request.headers.get("X-OS-Version", "Android"),
        app_version=data.get("app_version") or request.headers.get("X-App-Version", "v1.0.0")
    )
    return api_response(data=dev, message="Device registered successfully")

@device_bp.route("", methods=["GET"])
@token_required
@require_roles("ADMIN")
def list_devices():
    devices = device_service.get_all_devices()
    return api_response(data=devices)

@device_bp.route("/<device_id>/status", methods=["PUT"])
@token_required
@require_roles("ADMIN")
def update_device_status(device_id):
    data = request.get_json(silent=True) or {}
    status = data.get("status")
    if not status:
        return api_error("status parameter (ACTIVE / BLOCKED) is required", code="BAD_REQUEST", status_code=400)

    dev = device_service.update_device_status(device_id, status)
    if not dev:
        return api_error("Device not found", code="NOT_FOUND", status_code=404)
    return api_response(data=dev, message=f"Device status updated to {status}")
