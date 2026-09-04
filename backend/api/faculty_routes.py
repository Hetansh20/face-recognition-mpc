from flask import Blueprint, request, g
from backend.services.faculty_service import faculty_service
from backend.utils.response import api_response, api_error
from backend.middleware.authentication import token_required
from backend.middleware.authorization import require_roles

faculty_bp = Blueprint("faculty_bp", __name__, url_prefix="/api/v1/faculty")

@faculty_bp.route("", methods=["GET"])
@token_required
@require_roles("ADMIN", "FACULTY")
def list_faculty():
    dept = request.args.get("department")
    search = request.args.get("search")
    faculties = faculty_service.get_all_faculty(department=dept, search=search)
    return api_response(data=faculties)

@faculty_bp.route("/<int:faculty_id>", methods=["GET"])
@token_required
def get_faculty(faculty_id):
    fac = faculty_service.get_faculty_by_id(faculty_id)
    if not fac:
        return api_error("Faculty not found", code="NOT_FOUND", status_code=404)
    return api_response(data=fac)

@faculty_bp.route("", methods=["POST"])
@token_required
@require_roles("ADMIN")
def create_faculty():
    data = request.get_json(silent=True) or {}
    try:
        fac = faculty_service.create_faculty(data)
        return api_response(data=fac, message="Faculty created successfully", status_code=201)
    except Exception as e:
        return api_error(str(e), code="BAD_REQUEST", status_code=400)

@faculty_bp.route("/<int:faculty_id>", methods=["PUT"])
@token_required
@require_roles("ADMIN")
def update_faculty(faculty_id):
    data = request.get_json(silent=True) or {}
    try:
        fac = faculty_service.update_faculty(faculty_id, data)
        if not fac:
            return api_error("Faculty not found", code="NOT_FOUND", status_code=404)
        return api_response(data=fac, message="Faculty updated successfully")
    except Exception as e:
        return api_error(str(e), code="BAD_REQUEST", status_code=400)

@faculty_bp.route("/<int:faculty_id>", methods=["DELETE"])
@token_required
@require_roles("ADMIN")
def delete_faculty(faculty_id):
    success = faculty_service.delete_faculty(faculty_id)
    if not success:
        return api_error("Faculty not found", code="NOT_FOUND", status_code=404)
    return api_response(message="Faculty deactivated successfully")

@faculty_bp.route("/<int:faculty_id>/classes", methods=["GET"])
@token_required
def get_faculty_classes(faculty_id):
    classes = faculty_service.get_faculty_classes(faculty_id)
    return api_response(data=classes)
