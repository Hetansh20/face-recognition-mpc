import io
from flask import Blueprint, request, send_file
from backend.services.report_service import report_service
from backend.utils.response import api_response, api_error
from backend.middleware.authentication import token_required
from backend.middleware.authorization import require_roles

report_bp = Blueprint("report_bp", __name__, url_prefix="/api/v1/reports")

@report_bp.route("/stats", methods=["GET"])
@token_required
@require_roles("ADMIN", "FACULTY")
def get_stats():
    stats = report_service.get_dashboard_stats()
    return api_response(data=stats)

@report_bp.route("/export/csv", methods=["GET", "POST"])
@token_required
@require_roles("ADMIN", "FACULTY")
def export_csv():
    timetable_id = request.args.get("timetable_id")
    session_id = request.args.get("session_id")

    if request.is_json:
        data = request.get_json(silent=True) or {}
        timetable_id = data.get("timetable_id", timetable_id)
        session_id = data.get("session_id", session_id)

    filepath, filename = report_service.export_attendance_csv(timetable_id=timetable_id, session_id=session_id)
    return send_file(filepath, as_attachment=True, download_name=filename, mimetype="text/csv")

@report_bp.route("/export/session-csv", methods=["GET"])
@token_required
@require_roles("ADMIN", "FACULTY")
def export_session_present_csv():
    """Present-students CSV for one session, in the same column format as
    the web app (GR Number, Enrollment Number, Student Name, Email,
    Timestamp, Status, Confidence Score)."""
    session_id = request.args.get("session_id")
    if not session_id:
        return api_error("session_id is required", code="BAD_REQUEST", status_code=400)
    try:
        csv_bytes, filename = report_service.build_session_csv_bytes(session_id)
    except ValueError as e:
        return api_error(str(e), code="NOT_FOUND", status_code=404)
    return send_file(io.BytesIO(csv_bytes), as_attachment=True, download_name=filename, mimetype="text/csv")

@report_bp.route("/export/session-absent-csv", methods=["GET"])
@token_required
@require_roles("ADMIN", "FACULTY")
def export_session_absent_csv():
    """Absent-students CSV for one session, in the same column format as
    the web app (GR Number, Enrollment Number, Student Name, Status, Date,
    Class)."""
    session_id = request.args.get("session_id")
    if not session_id:
        return api_error("session_id is required", code="BAD_REQUEST", status_code=400)
    try:
        csv_bytes, filename = report_service.build_absent_csv_bytes(session_id)
    except ValueError as e:
        return api_error(str(e), code="NOT_FOUND", status_code=404)
    return send_file(io.BytesIO(csv_bytes), as_attachment=True, download_name=filename, mimetype="text/csv")

@report_bp.route("/export/excel", methods=["GET", "POST"])
@token_required
@require_roles("ADMIN", "FACULTY")
def export_excel():
    timetable_id = request.args.get("timetable_id")
    session_id = request.args.get("session_id")

    if request.is_json:
        data = request.get_json(silent=True) or {}
        timetable_id = data.get("timetable_id", timetable_id)
        session_id = data.get("session_id", session_id)

    filepath, filename = report_service.export_attendance_excel(timetable_id=timetable_id, session_id=session_id)
    return send_file(filepath, as_attachment=True, download_name=filename, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

