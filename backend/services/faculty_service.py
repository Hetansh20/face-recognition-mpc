from backend.models.database import db_session, FacultyModel, UserModel, TimetableModel, AttendanceSessionModel
from backend.utils.security import hash_password
from backend.services.logging_service import logging_service

class FacultyService:
    def get_all_faculty(self, department=None, search=None):
        query = db_session.query(FacultyModel).filter(FacultyModel.is_active == True)
        if department:
            query = query.filter(FacultyModel.department == department)
        if search:
            q = f"%{search}%"
            query = query.filter((FacultyModel.name.ilike(q)) | (FacultyModel.email.ilike(q)))
        faculties = query.order_by(FacultyModel.name).all()
        return [self._format_faculty(f) for f in faculties]

    def get_faculty_by_id(self, faculty_id: int):
        f = db_session.query(FacultyModel).filter(FacultyModel.id == faculty_id, FacultyModel.is_active == True).first()
        return self._format_faculty(f) if f else None

    def create_faculty(self, data: dict):
        name = data.get("name", "").strip()
        email = data.get("email", "").strip().lower()
        department = data.get("department", "General").strip()
        passcode = data.get("passcode", "123456").strip()

        if not name or not email:
            raise ValueError("Faculty name and email are required")

        existing = db_session.query(FacultyModel).filter(FacultyModel.email == email).first()
        if existing:
            raise ValueError(f"Faculty with email '{email}' already exists")

        passcode_hash = hash_password(passcode)

        user = UserModel(
            email=email,
            password_hash=passcode_hash,
            full_name=name,
            role="FACULTY",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        fac = FacultyModel(
            user_id=user.id,
            name=name,
            email=email,
            department=department,
            passcode_hash=passcode_hash,
            is_active=True
        )
        db_session.add(fac)
        db_session.commit()

        logging_service.log_audit("CREATE_FACULTY", "faculty", fac.id, f"Created faculty {name} ({email})")
        return self._format_faculty(fac)

    def update_faculty(self, faculty_id: int, data: dict):
        fac = db_session.query(FacultyModel).filter(FacultyModel.id == faculty_id, FacultyModel.is_active == True).first()
        if not fac:
            return None

        if "name" in data: fac.name = data["name"].strip()
        if "email" in data: fac.email = data["email"].strip().lower()
        if "department" in data: fac.department = data["department"].strip()
        if "passcode" in data and data["passcode"]:
            fac.passcode_hash = hash_password(data["passcode"].strip())
            if fac.user_id:
                user = db_session.query(UserModel).filter(UserModel.id == fac.user_id).first()
                if user: user.password_hash = fac.passcode_hash

        db_session.commit()
        logging_service.log_audit("UPDATE_FACULTY", "faculty", fac.id, f"Updated faculty {fac.name}")
        return self._format_faculty(fac)

    def delete_faculty(self, faculty_id: int):
        fac = db_session.query(FacultyModel).filter(FacultyModel.id == faculty_id).first()
        if not fac:
            return False

        fac.is_active = False
        if fac.user_id:
            user = db_session.query(UserModel).filter(UserModel.id == fac.user_id).first()
            if user: user.is_active = False

        db_session.commit()
        logging_service.log_audit("DELETE_FACULTY", "faculty", faculty_id, f"Deactivated faculty {fac.name}")
        return True

    def get_faculty_classes(self, faculty_id: int):
        timetables = db_session.query(TimetableModel).filter(TimetableModel.faculty_id == faculty_id).all()
        return [{
            "id": t.id,
            "class_name": t.class_name,
            "subject_name": t.subject_name,
            "day_of_week": t.day_of_week,
            "start_time": t.start_time,
            "end_time": t.end_time,
            "room_number": t.room_number
        } for t in timetables]

    def _format_faculty(self, f: FacultyModel) -> dict:
        if not f: return None
        return {
            "id": f.id,
            "user_id": f.user_id,
            "name": f.name,
            "email": f.email,
            "department": f.department,
            "is_active": f.is_active,
            "created_at": f.created_at.isoformat() if f.created_at else None
        }

faculty_service = FacultyService()
