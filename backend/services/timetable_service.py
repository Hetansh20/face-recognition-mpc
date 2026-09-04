from datetime import datetime, timedelta, timezone
from backend.models.database import (
    db_session, TimetableModel, FacultyModel, ClassModel, BatchModel,
    FacultySubstitutionModel, StudentModel
)
from backend.services.logging_service import logging_service

class TimetableService:
    def get_all_timetables(self, faculty_id=None, day=None):
        query = db_session.query(TimetableModel)
        if faculty_id:
            query = query.filter(TimetableModel.faculty_id == faculty_id)
        if day:
            query = query.filter(TimetableModel.day_of_week.ilike(day))
        timetables = query.order_by(TimetableModel.day_of_week, TimetableModel.start_time).all()
        return [self._format_timetable(t) for t in timetables]

    def get_timetable_by_id(self, timetable_id: int):
        t = db_session.query(TimetableModel).filter(TimetableModel.id == timetable_id).first()
        return self._format_timetable(t) if t else None

    def create_timetable(self, data: dict):
        faculty_id = data.get("faculty_id")
        class_name = data.get("class_name")
        day_of_week = data.get("day_of_week") or data.get("day")
        start_time = data.get("start_time")
        end_time = data.get("end_time")

        if not faculty_id or not class_name or not day_of_week or not start_time or not end_time:
            raise ValueError("faculty_id, class_name, day_of_week, start_time, and end_time are required")

        # Resolve class_id and batch_id if missing
        class_id = data.get("class_id")
        if not class_id and class_name:
            c = db_session.query(ClassModel).filter(ClassModel.name.ilike(class_name.strip())).first()
            if c: class_id = c.id

        t = TimetableModel(
            faculty_id=faculty_id,
            class_name=class_name.strip(),
            class_id=class_id,
            batch_id=data.get("batch_id"),
            semester=data.get("semester") or data.get("sem"),
            subject_name=data.get("subject_name"),
            day_of_week=day_of_week.capitalize(),
            start_time=start_time.strip(),
            end_time=end_time.strip(),
            room_number=data.get("room_number") or data.get("room")
        )
        db_session.add(t)
        db_session.commit()

        logging_service.log_audit("TIMETABLE_CREATED", "timetable", t.id, f"Created timetable {t.subject_name} for {t.class_name}")
        return self._format_timetable(t)

    def update_timetable(self, timetable_id: int, data: dict):
        t = db_session.query(TimetableModel).filter(TimetableModel.id == timetable_id).first()
        if not t: return None

        for k, v in data.items():
            if hasattr(t, k) and v is not None:
                setattr(t, k, v)
        db_session.commit()
        logging_service.log_audit("TIMETABLE_UPDATED", "timetable", t.id, f"Updated timetable entry #{t.id}")
        return self._format_timetable(t)

    def delete_timetable(self, timetable_id: int):
        t = db_session.query(TimetableModel).filter(TimetableModel.id == timetable_id).first()
        if not t: return False
        db_session.delete(t)
        db_session.commit()
        logging_service.log_audit("TIMETABLE_DELETED", "timetable", timetable_id, f"Deleted timetable entry #{timetable_id}")
        return True

    def get_active_class_for_faculty(self, faculty_id: int):
        """Calculates active class for faculty at current IST time (UTC+5:30)."""
        IST = timezone(timedelta(hours=5, minutes=30))
        now = datetime.now(IST)
        current_day = now.strftime("%A")
        current_time_str = now.strftime("%H:%M")
        today_date_str = now.strftime("%Y-%m-%d")

        # 1. Check direct faculty timetables
        timetables = db_session.query(TimetableModel).filter(TimetableModel.faculty_id == faculty_id).all()
        for t in timetables:
            if t.day_of_week.lower() == current_day.lower():
                if t.start_time < t.end_time:
                    if t.start_time <= current_time_str <= t.end_time:
                        return self._format_active_class(t, is_substitution=False)
                else: # overnight
                    if current_time_str >= t.start_time or current_time_str <= t.end_time:
                        return self._format_active_class(t, is_substitution=False)

        # 2. Check active faculty substitutions for today
        sub = db_session.query(FacultySubstitutionModel).filter(
            FacultySubstitutionModel.substitute_faculty_id == faculty_id,
            FacultySubstitutionModel.date == today_date_str,
            FacultySubstitutionModel.status == 'active'
        ).first()

        if sub:
            t = db_session.query(TimetableModel).filter(TimetableModel.id == sub.timetable_id).first()
            if t and t.day_of_week.lower() == current_day.lower():
                if t.start_time <= current_time_str <= t.end_time:
                    return self._format_active_class(t, is_substitution=True, sub_info=sub)

        return None

    def get_students_for_timetable(self, timetable_id: int):
        t = db_session.query(TimetableModel).filter(TimetableModel.id == timetable_id).first()
        if not t: return []

        query = db_session.query(StudentModel).filter(StudentModel.is_active == True)
        if t.batch_id:
            query = query.filter(StudentModel.batch_id == t.batch_id)
        elif t.class_id:
            query = query.filter(StudentModel.class_id == t.class_id)
        else:
            # Fallback by matching class_name with ClassModel or StudentModel.department
            class_str = t.class_name.strip() if t.class_name else ""
            clean_class_str = class_str
            # Remove leading digit (e.g., '6EK1' -> 'EK1', '4EK2' -> 'EK2')
            if len(class_str) > 1 and class_str[0].isdigit():
                clean_class_str = class_str[1:].strip()

            c = db_session.query(ClassModel).filter(
                (ClassModel.name.ilike(class_str)) |
                (ClassModel.name.ilike(clean_class_str)) |
                (ClassModel.name.ilike(f"%{clean_class_str}%"))
            ).first()

            if c:
                query = query.filter(StudentModel.class_id == c.id)
            elif class_str:
                query = query.filter(
                    (StudentModel.department.ilike(f"%{class_str}%")) |
                    (StudentModel.department.ilike(f"%{clean_class_str}%"))
                )

        students = query.all()
        return [{
            "id": s.id,
            "gr_number": s.gr_number,
            "name": s.name,
            "email": s.email,
            "department": s.department,
            "class_id": s.class_id,
            "face_pid": s.face_pid
        } for s in students]

    def _format_active_class(self, t: TimetableModel, is_substitution: bool = False, sub_info = None) -> dict:
        fac = db_session.query(FacultyModel).filter(FacultyModel.id == t.faculty_id).first()
        students = self.get_students_for_timetable(t.id)
        return {
            "timetable_id": t.id,
            "faculty_id": t.faculty_id,
            "faculty_name": fac.name if fac else "Unknown",
            "class_name": t.class_name,
            "semester": t.semester or "N/A",
            "subject_name": t.subject_name or t.class_name,
            "day": t.day_of_week,
            "start_time": t.start_time,
            "end_time": t.end_time,
            "room_number": t.room_number or "Room N/A",
            "is_substitution": is_substitution,
            "total_students": len(students),
            "students": students
        }

    def _format_timetable(self, t: TimetableModel) -> dict:
        if not t: return None
        fac = db_session.query(FacultyModel).filter(FacultyModel.id == t.faculty_id).first()
        return {
            "id": t.id,
            "faculty_id": t.faculty_id,
            "faculty_name": fac.name if fac else "Unknown",
            "class_name": t.class_name,
            "class_id": t.class_id,
            "batch_id": t.batch_id,
            "semester": t.semester,
            "subject_name": t.subject_name,
            "day_of_week": t.day_of_week,
            "start_time": t.start_time,
            "end_time": t.end_time,
            "room_number": t.room_number,
            "created_at": t.created_at.isoformat() if t.created_at else None
        }

timetable_service = TimetableService()
