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

