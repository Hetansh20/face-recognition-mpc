import os
import cv2
import numpy as np
from backend.models.database import (
    db_session, StudentModel, UserModel, ClassModel, BatchModel,
    FaceProfileModel, FaceEmbeddingModel, AttendanceRecordModel
)
from backend.utils.security import hash_password
from backend.services.logging_service import logging_service
from backend.face_engine.embedding_service import embedding_service
from backend.config import Config
import json

class StudentService:
    def get_all_students(self, class_id=None, batch_id=None, search=None):
        query = db_session.query(StudentModel).filter(StudentModel.is_active == True)
        if class_id:
            query = query.filter(StudentModel.class_id == class_id)
        if batch_id:
            query = query.filter(StudentModel.batch_id == batch_id)
        if search:
            q = f"%{search}%"
            query = query.filter(
                (StudentModel.name.ilike(q)) |
                (StudentModel.gr_number.ilike(q)) |
                (StudentModel.enrollment_number.ilike(q)) |
                (StudentModel.email.ilike(q)) |
                (StudentModel.roll_number.ilike(q))
            )
        students = query.order_by(StudentModel.name).all()
        return [self._format_student(s) for s in students]

    def get_student_by_id(self, student_id: int):
        s = db_session.query(StudentModel).filter(StudentModel.id == student_id, StudentModel.is_active == True).first()
        return self._format_student(s) if s else None

    def create_student(self, data: dict):
        gr_number = data.get("gr_number", "").strip()
        enrollment_number = data.get("enrollment_number", "").strip()
        email = data.get("email", "").strip().lower()
        name = data.get("name", "").strip()
        department = data.get("department", "Unassigned").strip()

        if not gr_number or not name or not email:
            raise ValueError("gr_number, name, and email are required")

        # Check unique constraint
        existing = db_session.query(StudentModel).filter(
            (StudentModel.gr_number == gr_number) | (StudentModel.email == email)
        ).first()
        if existing:
            raise ValueError(f"Student with GR Number '{gr_number}' or email '{email}' already exists")

        # Create user account for student
        user = UserModel(
            email=email,
            password_hash=hash_password("student123"),
            full_name=name,
            role="STUDENT",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        student = StudentModel(
            user_id=user.id,
            gr_number=gr_number,
            enrollment_number=enrollment_number or None,
            student_id=gr_number,
            name=name,
            email=email,
            department=department,
            class_id=data.get("class_id"),
            batch_id=data.get("batch_id"),
            roll_number=data.get("roll_number"),
            phone=data.get("phone"),
            face_pid=data.get("face_pid"),
            is_active=True
        )
        db_session.add(student)
        db_session.commit()

        logging_service.log_audit("CREATE_STUDENT", "student", student.id, f"Created student {name} ({gr_number})")
        return self._format_student(student)

    def update_student(self, student_id: int, data: dict):
        student = db_session.query(StudentModel).filter(StudentModel.id == student_id, StudentModel.is_active == True).first()
        if not student:
            return None

        for field in ["name", "email", "department", "gr_number", "enrollment_number", "roll_number", "phone", "face_pid", "class_id", "batch_id"]:
            if field in data and data[field] is not None:
                setattr(student, field, data[field])

        db_session.commit()
        logging_service.log_audit("UPDATE_STUDENT", "student", student.id, f"Updated student {student.name}")
        return self._format_student(student)

    def delete_student(self, student_id: int):
        student = db_session.query(StudentModel).filter(StudentModel.id == student_id).first()
        if not student:
            return False

        student.is_active = False
        if student.user_id:
            user = db_session.query(UserModel).filter(UserModel.id == student.user_id).first()
            if user:
                user.is_active = False
        db_session.commit()
        logging_service.log_audit("DELETE_STUDENT", "student", student_id, f"Deactivated student {student.name}")
        return True

    def register_face(self, student_id: int, image_bytes: bytes):
        from backend.face_engine.face_engine import face_service
        student = db_session.query(StudentModel).filter(StudentModel.id == student_id).first()
        if not student:
            return None, "Student not found"

        np_arr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if frame is None:
            return None, "Invalid image payload"

        faces = face_service.detect_faces(frame)
        if not faces:
            return None, "No clear face detected in the image"

        safe_name = student.name.replace(" ", "_")
        safe_gr = (student.gr_number or f"STU{student.id}").replace(" ", "_")
        person_id = f"{safe_name}_{safe_gr}"

        os.makedirs(Config.FACES_DIR, exist_ok=True)
        img_filename = f"{person_id}_reg.jpg"
        img_path = os.path.join(Config.FACES_DIR, img_filename)
        with open(img_path, "wb") as f:
            f.write(image_bytes)

        # Save face profile
        profile = FaceProfileModel(student_id=student.id, face_pid=person_id, image_path=img_path)
        db_session.add(profile)
        student.face_pid = person_id
        db_session.commit()

        # Extract and register face embedding
        vectors = [face.embedding.tolist() for face in faces if hasattr(face, "embedding")]
        if vectors:
            embedding_service.register_embedding(
                person_id=person_id,
                name=student.name,
                gr_number=student.gr_number or f"STU{student.id}",
                vectors=vectors,
                image_paths=[img_path]
            )

        logging_service.log_audit("FACE_REGISTERED", "student", student.id, f"Registered face profile for {student.name}")
        return {"student_id": student.id, "face_pid": person_id, "registered": True}, "Face registered successfully"

    def get_student_attendance(self, student_id: int):
        records = db_session.query(AttendanceRecordModel).filter(AttendanceRecordModel.student_id == student_id).order_by(AttendanceRecordModel.timestamp.desc()).all()
        return [{
            "id": r.id,
            "timetable_id": r.timetable_id,
            "session_id": r.session_id,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            "status": r.status,
            "confidence_score": r.confidence_score
        } for r in records]

    def _format_student(self, s: StudentModel) -> dict:
        if not s:
            return None
        cls_name = None
        if s.class_id:
            c = db_session.query(ClassModel).filter(ClassModel.id == s.class_id).first()
            if c: cls_name = c.name
        batch_name = None
        if s.batch_id:
            b = db_session.query(BatchModel).filter(BatchModel.id == s.batch_id).first()
            if b: batch_name = b.name

        has_face = bool(s.face_pid)
        return {
            "id": s.id,
            "student_id": s.gr_number or s.student_id or f"STU{s.id}",
            "gr_number": s.gr_number,
            "enrollment_number": s.enrollment_number,
            "name": s.name,
            "email": s.email,
            "department": s.department,
            "class_id": s.class_id,
            "class_name": cls_name,
            "batch_id": s.batch_id,
            "batch_name": batch_name,
            "roll_number": s.roll_number,
            "phone": s.phone,
            "face_pid": s.face_pid,
            "has_face_registered": has_face,
            "is_active": s.is_active,
            "created_at": s.created_at.isoformat() if s.created_at else None
        }

student_service = StudentService()
