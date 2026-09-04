from flask import Blueprint, request
from backend.services.report_service import report_service
from backend.utils.response import api_response
from backend.middleware.authentication import token_required
from backend.middleware.authorization import require_roles

log_bp = Blueprint("log_bp", __name__, url_prefix="/api/v1/logs")

@log_bp.route("/audit", methods=["GET"])
@token_required
@require_roles("ADMIN")
def get_audit_logs():
    limit = request.args.get("limit", default=100, type=int)
    action = request.args.get("action")
    user_email = request.args.get("user_email")
    logs = report_service.get_audit_logs(limit=limit, action=action, user_email=user_email)
    return api_response(data=logs)

@log_bp.route("/system", methods=["GET"])
@token_required
@require_roles("ADMIN")
def get_system_logs():
    limit = request.args.get("limit", default=100, type=int)
    level = request.args.get("level")
    logs = report_service.get_system_logs(limit=limit, level=level)
    return api_response(data=logs)
