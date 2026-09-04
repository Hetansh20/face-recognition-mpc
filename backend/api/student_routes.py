from flask import Blueprint, request, g
from backend.services.student_service import student_service
from backend.utils.response import api_response, api_error
from backend.middleware.authentication import token_required
from backend.middleware.authorization import require_roles

student_bp = Blueprint("student_bp", __name__, url_prefix="/api/v1/students")

@student_bp.route("", methods=["GET"])
@token_required
@require_roles("ADMIN", "FACULTY")
def list_students():
    class_id = request.args.get("class_id", type=int)
    batch_id = request.args.get("batch_id", type=int)
    search = request.args.get("search")
    students = student_service.get_all_students(class_id=class_id, batch_id=batch_id, search=search)
    return api_response(data=students)

@student_bp.route("/<int:student_id>", methods=["GET"])
@token_required
def get_student(student_id):
    student = student_service.get_student_by_id(student_id)
    if not student:
        return api_error("Student not found", code="NOT_FOUND", status_code=404)
    return api_response(data=student)

@student_bp.route("", methods=["POST"])
@token_required
@require_roles("ADMIN")
def create_student():
    data = request.get_json(silent=True) or {}
    try:
        student = student_service.create_student(data)
        return api_response(data=student, message="Student created successfully", status_code=201)
    except Exception as e:
        return api_error(str(e), code="BAD_REQUEST", status_code=400)

@student_bp.route("/<int:student_id>", methods=["PUT"])
@token_required
@require_roles("ADMIN")
def update_student(student_id):
    data = request.get_json(silent=True) or {}
    try:
        updated = student_service.update_student(student_id, data)
        if not updated:
            return api_error("Student not found", code="NOT_FOUND", status_code=404)
        return api_response(data=updated, message="Student updated successfully")
    except Exception as e:
        return api_error(str(e), code="BAD_REQUEST", status_code=400)

@student_bp.route("/<int:student_id>", methods=["DELETE"])
@token_required
@require_roles("ADMIN")
def delete_student(student_id):
    success = student_service.delete_student(student_id)
    if not success:
        return api_error("Student not found", code="NOT_FOUND", status_code=404)
    return api_response(message="Student deleted successfully")

@student_bp.route("/<int:student_id>/face-registration", methods=["POST"])
@token_required
@require_roles("ADMIN", "FACULTY")
def register_student_face(student_id):
    if 'image' in request.files:
        file = request.files['image']
        image_bytes = file.read()
    else:
        image_bytes = request.get_data()

    if not image_bytes:
        return api_error("Image file or binary data is required", code="BAD_REQUEST", status_code=400)

    res, msg = student_service.register_face(student_id, image_bytes)
    if not res:
        return api_error(msg, code="FACE_REGISTRATION_FAILED", status_code=400)
    return api_response(data=res, message=msg)

@student_bp.route("/<int:student_id>/attendance", methods=["GET"])
@token_required
def get_student_attendance(student_id):
    # If student, verify accessing own attendance
    if g.current_user["role"] == "STUDENT":
        prof = student_service.get_student_by_id(student_id)
        if not prof or prof.get("email") != g.current_user["email"]:
            return api_error("Access denied to other student attendance", code="FORBIDDEN", status_code=403)

    records = student_service.get_student_attendance(student_id)
    return api_response(data=records)
