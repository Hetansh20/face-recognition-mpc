from flask import Blueprint, request, g
from backend.models.database import db_session, AttendanceRecordModel, StudentModel, TimetableModel
from backend.utils.response import api_response, api_error
from backend.middleware.authentication import token_required
from backend.middleware.authorization import require_roles

attendance_bp = Blueprint("attendance_bp", __name__, url_prefix="/api/v1/attendance")

@attendance_bp.route("", methods=["GET"])
@token_required
def list_attendance_records():
    student_id = request.args.get("student_id", type=int)
    timetable_id = request.args.get("timetable_id", type=int)
    session_id = request.args.get("session_id", type=int)
    status = request.args.get("status")

    query = db_session.query(AttendanceRecordModel)
    if student_id:
        query = query.filter(AttendanceRecordModel.student_id == student_id)
    if timetable_id:
        query = query.filter(AttendanceRecordModel.timetable_id == timetable_id)
    if session_id:
        query = query.filter(AttendanceRecordModel.session_id == session_id)
    if status:
        query = query.filter(AttendanceRecordModel.status.ilike(status))

    records = query.order_by(AttendanceRecordModel.timestamp.desc()).limit(500).all()

    formatted = []
    for r in records:
        stu = db_session.query(StudentModel).filter(StudentModel.id == r.student_id).first()
        tt = db_session.query(TimetableModel).filter(TimetableModel.id == r.timetable_id).first()
        formatted.append({
            "id": r.id,
            "student_id": stu.gr_number if stu else "N/A",
            "student_name": stu.name if stu else "Unknown",
            "timetable_id": r.timetable_id,
            "subject_name": tt.subject_name if tt else "Subject",
            "session_id": r.session_id,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            "status": r.status.upper(),
            "confidence_score": r.confidence_score
        })

    return api_response(data=formatted)

@attendance_bp.route("/group-detect", methods=["POST"])
@token_required
@require_roles("ADMIN", "FACULTY")
def group_detect_photo():
    import base64
    from datetime import datetime
    from backend.face_engine.group_recognizer import process_group_photo

    image_bytes = None
    if 'image' in request.files:
        image_bytes = request.files['image'].read()
    elif request.is_json:
        data = request.get_json() or {}
        img_b64 = data.get("image", "")
        if img_b64:
            try:
                image_bytes = base64.b64decode(img_b64.split(",")[-1])
            except Exception:
                return api_error("Invalid base64 image data", code="BAD_REQUEST", status_code=400)

    if not image_bytes:
        return api_error("Photo image is required", code="BAD_REQUEST", status_code=400)

    # Process photo through engine
    result = process_group_photo(image_bytes)
    if "error" in result:
        return api_error(result["error"], code="PROCESSING_ERROR", status_code=400)

    # Get all active students for comparison
    all_students = db_session.query(StudentModel).filter(StudentModel.is_active == True).all()
    recognized_pids = {r.get("person_id") for r in result.get("recognized", []) if r.get("person_id")}
    recognized_grs = {r.get("student_id") for r in result.get("recognized", []) if r.get("student_id")}

    present = []
    absent = []

    for s in all_students:
        is_rec = (s.face_pid in recognized_pids) or (s.gr_number in recognized_grs)
        stu_dict = {
            "id": s.id,
            "gr_number": s.gr_number,
            "name": s.name,
            "department": s.department or "ICT",
            "email": s.email
        }
        if is_rec:
            # find confidence
            conf = 95.0
            for r in result.get("recognized", []):
                if r.get("person_id") == s.face_pid or r.get("student_id") == s.gr_number:
                    conf = r.get("confidence", 95.0)
                    break
            stu_dict["confidence"] = conf
            present.append(stu_dict)
        else:
            absent.append(stu_dict)

    return api_response(data={
        "total_faces": result.get("total_faces", 0),
        "recognized_count": len(result.get("recognized", [])),
        "unrecognized_count": result.get("unrecognized_count", 0),
        "annotated_image": result.get("annotated_image", ""),
        "present": present,
        "absent": absent
    })

@attendance_bp.route("/confirm-group", methods=["POST"])
@token_required
@require_roles("ADMIN", "FACULTY")
def confirm_group_attendance():
    from datetime import datetime
    from backend.models.database import AttendanceSessionModel

    data = request.get_json() or {}
    present_student_ids = data.get("present_student_ids", [])  # list of student IDs or GR numbers
    timetable_id = data.get("timetable_id", 1)

    if not present_student_ids:
        return api_error("No present student IDs provided", code="BAD_REQUEST", status_code=400)

    # Resolve actual FacultyModel.id
    faculty_id = None
    if g.current_user and g.current_user.get("id"):
        from backend.services.auth_service import auth_service
        prof = auth_service.get_user_profile(g.current_user["id"])
        if prof:
            faculty_id = prof.get("faculty_id")
        if not faculty_id:
            from backend.models.database import FacultyModel
            fac = db_session.query(FacultyModel).filter(
                (FacultyModel.user_id == g.current_user["id"]) | (FacultyModel.email == g.current_user.get("email"))
            ).first()
            if fac:
                faculty_id = fac.id

    sess = AttendanceSessionModel(
        session_uuid=f"group-{int(datetime.utcnow().timestamp())}",
        faculty_id=faculty_id or 1,
        timetable_id=timetable_id,
        session_start=datetime.utcnow(),
        total_students=len(present_student_ids),
        present_count=len(present_student_ids),
        status='completed',
        session_end=datetime.utcnow()
    )
    db_session.add(sess)
    db_session.commit()

    marked_count = 0
    for sid_or_gr in present_student_ids:
        stu = None
        if isinstance(sid_or_gr, int) or (isinstance(sid_or_gr, str) and sid_or_gr.isdigit()):
            stu = db_session.query(StudentModel).filter(StudentModel.id == int(sid_or_gr)).first()
        if not stu and isinstance(sid_or_gr, str):
            stu = db_session.query(StudentModel).filter(StudentModel.gr_number == sid_or_gr).first()

        if stu:
            rec = AttendanceRecordModel(
                student_id=stu.id,
                timetable_id=timetable_id,
                session_id=sess.id,
                timestamp=datetime.utcnow(),
                status='present',
                confidence_score=0.95
            )
            db_session.add(rec)
            marked_count += 1

    db_session.commit()
    return api_response(data={"session_id": sess.id, "marked_count": marked_count}, message=f"Successfully marked attendance for {marked_count} students!")

