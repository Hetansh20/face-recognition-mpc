from flask import Blueprint, request, g
from backend.services.attendance_service import attendance_service
from backend.utils.response import api_response, api_error
from backend.middleware.authentication import token_required
from backend.middleware.authorization import require_roles

session_bp = Blueprint("session_bp", __name__, url_prefix="/api/v1/attendance/sessions")

@session_bp.route("/start", methods=["POST"])
@token_required
@require_roles("FACULTY", "ADMIN")
def start_session():
    data = request.get_json(silent=True) or {}
    faculty_id = data.get("faculty_id")
    timetable_id = data.get("timetable_id")
    device_id = request.headers.get("X-Device-ID") or data.get("device_id")

    if not faculty_id and g.current_user["role"] == "FACULTY":
        from backend.services.auth_service import auth_service
        prof = auth_service.get_user_profile(g.current_user["id"])
        faculty_id = prof.get("faculty_id")

    if not faculty_id:
        return api_error("faculty_id is required", code="BAD_REQUEST", status_code=400)

    try:
        sess = attendance_service.start_session(faculty_id, timetable_id=timetable_id, device_id=device_id)
        return api_response(data=sess, message="Attendance session started", status_code=201)
    except Exception as e:
        return api_error(str(e), code="SESSION_START_FAILED", status_code=400)

@session_bp.route("/<session_id>", methods=["GET"])
@token_required
def get_session(session_id):
    res = attendance_service.get_session_results(session_id)
    if not res:
        return api_error("Attendance session not found", code="NOT_FOUND", status_code=404)
    return api_response(data=res)

@session_bp.route("/<session_id>/recognize", methods=["POST"])
@token_required
@require_roles("FACULTY", "ADMIN")
def recognize_frame(session_id):
    if 'image' in request.files:
        file = request.files['image']
        image_bytes = file.read()
    else:
        image_bytes = request.get_data()

    if not image_bytes:
        return api_error("Image payload is required", code="BAD_REQUEST", status_code=400)

    try:
        res = attendance_service.process_live_frame(session_id, image_bytes)
        return api_response(data=res)
    except Exception as e:
        return api_error(str(e), code="RECOGNITION_FAILED", status_code=400)

@session_bp.route("/<session_id>/capture", methods=["POST"])
@token_required
@require_roles("FACULTY", "ADMIN")
def group_capture(session_id):
    if 'image' in request.files:
        file = request.files['image']
        image_bytes = file.read()
    else:
        image_bytes = request.get_data()

    if not image_bytes:
        return api_error("Group photo image is required", code="BAD_REQUEST", status_code=400)

    try:
        res = attendance_service.process_group_attendance(session_id, image_bytes)
        return api_response(data=res)
    except Exception as e:
        return api_error(str(e), code="CAPTURE_FAILED", status_code=400)

@session_bp.route("/<session_id>/stop", methods=["POST"])
@token_required
@require_roles("FACULTY", "ADMIN")
def stop_session(session_id):
    try:
        res = attendance_service.stop_session(session_id)
        return api_response(data=res, message="Attendance session completed")
    except Exception as e:
        return api_error(str(e), code="STOP_SESSION_FAILED", status_code=400)

@session_bp.route("/<session_id>/results", methods=["GET"])
@token_required
def get_session_results(session_id):
    res = attendance_service.get_session_results(session_id)
    if not res:
        return api_error("Attendance session not found", code="NOT_FOUND", status_code=404)
    return api_response(data=res)

@session_bp.route("/<session_id>/update-records", methods=["POST", "PUT"])
@token_required
@require_roles("FACULTY", "ADMIN")
def update_session_records(session_id):
    data = request.get_json(silent=True) or {}
    updates = data.get("records", [])
    try:
        res = attendance_service.update_session_records(session_id, updates)
        return api_response(data=res, message="Attendance records updated successfully")
    except Exception as e:
        return api_error(str(e), code="UPDATE_FAILED", status_code=400)
