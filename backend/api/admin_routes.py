from flask import Blueprint, request
import pandas as pd
import zipfile
import os
import json
from datetime import datetime
from backend.models.database import db_session, SemesterModel, ClassModel, BatchModel
from backend.utils.response import api_response, api_error
from backend.middleware.authentication import token_required
from backend.middleware.authorization import require_roles
from backend.services.student_service import student_service
from backend.config import Config

admin_bp = Blueprint("admin_bp", __name__, url_prefix="/api/v1/admin")

@admin_bp.route("/semesters", methods=["GET"])
@token_required
def get_semesters():
    sems = db_session.query(SemesterModel).order_by(SemesterModel.number).all()
    return api_response(data=[{"id": s.id, "number": s.number, "label": s.label, "level": s.level} for s in sems])

@admin_bp.route("/semesters", methods=["POST"])
@token_required
@require_roles("ADMIN")
def add_semester():
    data = request.get_json(silent=True) or {}
    try:
        sem = SemesterModel(number=int(data["number"]), label=data.get("label"), level=data.get("level"))
        db_session.add(sem)
        db_session.commit()
        return api_response(data={"id": sem.id, "number": sem.number}, message="Semester added", status_code=201)
    except Exception as e:
        return api_error(str(e), code="BAD_REQUEST", status_code=400)

@admin_bp.route("/classes", methods=["GET"])
@token_required
def get_classes():
    sem_id = request.args.get("semester_id", type=int)
    query = db_session.query(ClassModel)
    if sem_id:
        query = query.filter(ClassModel.semester_id == sem_id)
    classes = query.order_by(ClassModel.name).all()
    return api_response(data=[{"id": c.id, "semester_id": c.semester_id, "name": c.name, "section": c.section} for c in classes])

@admin_bp.route("/classes", methods=["POST"])
@token_required
@require_roles("ADMIN")
def add_class():
    data = request.get_json(silent=True) or {}
    try:
        cls = ClassModel(semester_id=int(data["semester_id"]), name=data["name"].strip(), section=data.get("section"))
        db_session.add(cls)
        db_session.commit()
        return api_response(data={"id": cls.id, "name": cls.name}, message="Class added", status_code=201)
    except Exception as e:
        return api_error(str(e), code="BAD_REQUEST", status_code=400)

@admin_bp.route("/batches", methods=["GET"])
@token_required
def get_batches():
    cls_id = request.args.get("class_id", type=int)
    query = db_session.query(BatchModel)
    if cls_id:
        query = query.filter(BatchModel.class_id == cls_id)
    batches = query.order_by(BatchModel.name).all()
    return api_response(data=[{"id": b.id, "class_id": b.class_id, "name": b.name} for b in batches])

@admin_bp.route("/batches", methods=["POST"])
@token_required
@require_roles("ADMIN")
def add_batch():
    data = request.get_json(silent=True) or {}
    try:
        b = BatchModel(class_id=int(data["class_id"]), name=data["name"].strip())
        db_session.add(b)
        db_session.commit()
        return api_response(data={"id": b.id, "name": b.name}, message="Batch added", status_code=201)
    except Exception as e:
        return api_error(str(e), code="BAD_REQUEST", status_code=400)

@admin_bp.route("/students/bulk-upload", methods=["POST"])
@token_required
@require_roles("ADMIN")
def bulk_upload_students():
    if 'excel' not in request.files or 'zip' not in request.files:
        return api_error("Both Excel/CSV and ZIP files are required", code="BAD_REQUEST", status_code=400)

    excel_file = request.files['excel']
    zip_file = request.files['zip']

    try:
        fname = excel_file.filename.lower()
        if fname.endswith('.csv'):
            df = pd.read_csv(excel_file)
        else:
            df = pd.read_excel(excel_file)

        added_count = 0
        photo_count = 0

        with zipfile.ZipFile(zip_file) as zf:
            zip_contents = zf.namelist()
            zip_basename_map = {os.path.basename(p): p for p in zip_contents if not p.endswith('/')}

            for idx, row in df.iterrows():
                try:
                    gr_num = str(row.get('gr_number') or row.get('gr_no') or row.get('student_id') or '').strip()
                    name = str(row.get('name') or row.get('student_name') or '').strip()
                    email = str(row.get('email') or '').strip().lower()
                    dept = str(row.get('department') or 'General').strip()

                    if not gr_num or not name or not email:
                        continue

                    # Create student
                    stu_data = {
                        "gr_number": gr_num,
                        "enrollment_number": str(row.get('enrollment_number') or row.get('enroll_no') or '').strip(),
                        "name": name,
                        "email": email,
                        "department": dept,
                        "roll_number": str(row.get('roll_number') or '').strip(),
                        "phone": str(row.get('phone') or '').strip()
                    }
                    try:
                        stu = student_service.create_student(stu_data)
                        added_count += 1
                        stu_id = stu["id"]
                    except Exception:
                        existing = student_service.get_all_students(search=gr_num)
                        stu_id = existing[0]["id"] if existing else None

                    if stu_id:
                        for ext in ['.jpg', '.jpeg', '.png', '.JPG']:
                            target_name = f"{gr_num}{ext}"
                            if target_name in zip_basename_map:
                                with zf.open(zip_basename_map[target_name]) as pf:
                                    img_data = pf.read()
                                    student_service.register_face(stu_id, img_data)
                                    photo_count += 1
                                break
                except Exception as row_err:
                    print(f"[Bulk Upload Row Error] {row_err}")

        return api_response(message=f"Successfully processed {added_count} students with {photo_count} photo face profiles mapped")
    except Exception as e:
        return api_error(str(e), code="BULK_UPLOAD_FAILED", status_code=400)
