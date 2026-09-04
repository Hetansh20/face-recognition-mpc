from flask import Blueprint, request, g
from backend.services.timetable_service import timetable_service
from backend.utils.response import api_response, api_error
from backend.middleware.authentication import token_required
from backend.middleware.authorization import require_roles

timetable_bp = Blueprint("timetable_bp", __name__, url_prefix="/api/v1/timetables")

@timetable_bp.route("", methods=["GET"])
@token_required
def list_timetables():
    faculty_id = request.args.get("faculty_id", type=int)
    day = request.args.get("day")
    timetables = timetable_service.get_all_timetables(faculty_id=faculty_id, day=day)
    return api_response(data=timetables)

@timetable_bp.route("/active", methods=["GET"])
@token_required
def get_active_timetable():
    faculty_id = request.args.get("faculty_id", type=int)
    if (not faculty_id or faculty_id == 0) and g.current_user:
        from backend.services.auth_service import auth_service
        prof = auth_service.get_user_profile(g.current_user["id"])
        if prof:
            faculty_id = prof.get("faculty_id")

        if not faculty_id or faculty_id == 0:
            from backend.models.database import db_session, FacultyModel
            fac = db_session.query(FacultyModel).filter(
                (FacultyModel.user_id == g.current_user["id"]) | (FacultyModel.email == g.current_user.get("email"))
            ).first()
            if fac:
                faculty_id = fac.id

    if not faculty_id:
        return api_error("faculty_id parameter is required", code="BAD_REQUEST", status_code=400)

    active = timetable_service.get_active_class_for_faculty(faculty_id)
    if not active:
        return api_error("No active class scheduled at this time for this faculty", code="NO_ACTIVE_CLASS", status_code=404)

    return api_response(data=active)

@timetable_bp.route("/<int:timetable_id>", methods=["GET"])
@token_required
def get_timetable(timetable_id):
    tt = timetable_service.get_timetable_by_id(timetable_id)
    if not tt:
        return api_error("Timetable entry not found", code="NOT_FOUND", status_code=404)
    return api_response(data=tt)

@timetable_bp.route("", methods=["POST"])
@token_required
@require_roles("ADMIN")
def create_timetable():
    data = request.get_json(silent=True) or {}
    try:
        tt = timetable_service.create_timetable(data)
        return api_response(data=tt, message="Timetable created successfully", status_code=201)
    except Exception as e:
        return api_error(str(e), code="BAD_REQUEST", status_code=400)

@timetable_bp.route("/<int:timetable_id>", methods=["PUT"])
@token_required
@require_roles("ADMIN")
def update_timetable(timetable_id):
    data = request.get_json(silent=True) or {}
    try:
        tt = timetable_service.update_timetable(timetable_id, data)
        if not tt:
            return api_error("Timetable entry not found", code="NOT_FOUND", status_code=404)
        return api_response(data=tt, message="Timetable entry updated successfully")
    except Exception as e:
        return api_error(str(e), code="BAD_REQUEST", status_code=400)

@timetable_bp.route("/<int:timetable_id>", methods=["DELETE"])
@token_required
@require_roles("ADMIN")
def delete_timetable(timetable_id):
    success = timetable_service.delete_timetable(timetable_id)
    if not success:
        return api_error("Timetable entry not found", code="NOT_FOUND", status_code=404)
    return api_response(message="Timetable entry deleted successfully")
