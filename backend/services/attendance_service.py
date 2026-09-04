import uuid
from datetime import datetime
from backend.models.database import (
    db_session, AttendanceSessionModel, AttendanceRecordModel,
    TimetableModel, StudentModel, FacultyModel
)
from backend.services.timetable_service import timetable_service
from backend.services.logging_service import logging_service
from backend.face_engine.face_engine import face_service
from backend.face_engine.group_recognizer import process_group_photo

class AttendanceService:
    def start_session(self, faculty_id: int, timetable_id: int = None, device_id: str = None):
        """Starts an attendance session for faculty."""
        if not timetable_id:
            active = timetable_service.get_active_class_for_faculty(faculty_id)
            if not active:
                raise ValueError("No active class scheduled at this time for this faculty")
            timetable_id = active["timetable_id"]

        tt = db_session.query(TimetableModel).filter(TimetableModel.id == timetable_id).first()
        if not tt:
            raise ValueError(f"Timetable #{timetable_id} not found")

        # Get expected students
        enrolled_students = timetable_service.get_students_for_timetable(timetable_id)
        total_students = len(enrolled_students)

        # Check if an active session already exists for this timetable
        existing = db_session.query(AttendanceSessionModel).filter(
            AttendanceSessionModel.timetable_id == timetable_id,
            AttendanceSessionModel.status == 'active'
        ).first()

        if existing:
            return self._format_session(existing)

        session_id = f"session-{uuid.uuid4().hex[:12]}"
        sess = AttendanceSessionModel(
            session_uuid=session_id,
            faculty_id=faculty_id,
            timetable_id=timetable_id,
            session_start=datetime.utcnow(),
            total_students=total_students,
            present_count=0,
            status='active',
            device_id=device_id
        )
        db_session.add(sess)
        db_session.commit()

        logging_service.log_audit("SESSION_STARTED", "session", sess.id, f"Session started for {tt.class_name} ({tt.subject_name})")
        return self._format_session(sess)

    def process_live_frame(self, session_id: int, image_bytes: bytes):
        """Processes a single live camera frame sent from Android / Client."""
        sess = db_session.query(AttendanceSessionModel).filter(
            (AttendanceSessionModel.id == session_id) | (AttendanceSessionModel.session_uuid == str(session_id)),
            AttendanceSessionModel.status == 'active'
        ).first()

        if not sess:
            raise ValueError("Attendance session not active or not found")

        # Get target student pids for optimized matching specifically for this class
        students = timetable_service.get_students_for_timetable(sess.timetable_id)
        enrolled_ids = {s["id"] for s in students}
        enrolled_grs = {s["gr_number"] for s in students if s.get("gr_number")}
        enrolled_pids = {s["face_pid"] for s in students if s.get("face_pid")}

        target_pids = enrolled_pids if enrolled_pids else None
        res = face_service.process_frame(image_bytes, target_pids=target_pids)

        newly_marked = []
        for matched in res.get("students", []):
            if matched.get("status") == "PRESENT" and matched.get("person_id"):
                pid = matched["person_id"]
                stu_gr = matched.get("student_id")

                stu = db_session.query(StudentModel).filter(
                    (StudentModel.face_pid == pid) | (StudentModel.gr_number == stu_gr)
                ).first()

                # Verify student is in enrolled list for THIS class/timetable
                if stu and (stu.id in enrolled_ids or stu.gr_number in enrolled_grs or stu.face_pid in enrolled_pids):
                    # Check if already marked present in this session
                    existing_rec = db_session.query(AttendanceRecordModel).filter(
                        AttendanceRecordModel.session_id == sess.id,
                        AttendanceRecordModel.student_id == stu.id
                    ).first()

                    if not existing_rec:
                        rec = AttendanceRecordModel(
                            student_id=stu.id,
                            timetable_id=sess.timetable_id,
                            session_id=sess.id,
                            timestamp=datetime.utcnow(),
                            status='present',
                            confidence_score=matched.get("confidence")
                        )
                        db_session.add(rec)
                        sess.present_count = (sess.present_count or 0) + 1
                        db_session.commit()
                        newly_marked.append({
                            "student_id": stu.gr_number,
                            "name": stu.name,
                            "confidence": matched.get("confidence"),
                            "status": "PRESENT"
                        })

        return {
            "session_id": sess.session_uuid or str(sess.id),
            "faces_detected": res.get("faces_detected", 0),
            "recognized": res.get("recognized", 0),
            "unknown": res.get("unknown", 0),
            "total_present_in_session": sess.present_count,
            "newly_marked": newly_marked,
            "students": res.get("students", [])
        }

    def process_group_attendance(self, session_id: int, image_bytes: bytes):
        """Processes group photo attendance."""
        sess = db_session.query(AttendanceSessionModel).filter(
            (AttendanceSessionModel.id == session_id) | (AttendanceSessionModel.session_uuid == str(session_id))
        ).first()

        if not sess:
            raise ValueError("Attendance session not found")

        students = timetable_service.get_students_for_timetable(sess.timetable_id)
        enrolled_ids = {s["id"] for s in students}
        enrolled_grs = {s["gr_number"] for s in students if s.get("gr_number")}
        enrolled_pids = {s["face_pid"] for s in students if s.get("face_pid")}

        target_pids = enrolled_pids if enrolled_pids else None
        res = process_group_photo(image_bytes, target_pids=target_pids)

        newly_marked = []
        for matched in res.get("recognized", []):
            pid = matched.get("person_id")
            stu_gr = matched.get("student_id")

            stu = db_session.query(StudentModel).filter(
                (StudentModel.face_pid == pid) | (StudentModel.gr_number == stu_gr)
            ).first()

            # Verify student is in enrolled list for THIS class/timetable
            if stu and (stu.id in enrolled_ids or stu.gr_number in enrolled_grs or stu.face_pid in enrolled_pids):
                existing_rec = db_session.query(AttendanceRecordModel).filter(
                    AttendanceRecordModel.session_id == sess.id,
                    AttendanceRecordModel.student_id == stu.id
                ).first()

                if not existing_rec:
                    rec = AttendanceRecordModel(
                        student_id=stu.id,
                        timetable_id=sess.timetable_id,
                        session_id=sess.id,
                        timestamp=datetime.utcnow(),
                        status='present',
                        confidence_score=float(matched.get("confidence", 80.0)) / 100.0
                    )
                    db_session.add(rec)
                    sess.present_count = (sess.present_count or 0) + 1
                    db_session.commit()
                    newly_marked.append({
                        "student_id": stu.gr_number,
                        "name": stu.name,
                        "status": "PRESENT"
                    })

        return {
            "session_id": sess.session_uuid or str(sess.id),
            "total_faces": res.get("total_faces", 0),
            "recognized_count": len(res.get("recognized", [])),
            "unrecognized_count": res.get("unrecognized_count", 0),
            "newly_marked": newly_marked,
            "annotated_image": res.get("annotated_image")
        }

    def stop_session(self, session_id: int):
        """Stops attendance session and calculates absent records."""
        sess = db_session.query(AttendanceSessionModel).filter(
            (AttendanceSessionModel.id == session_id) | (AttendanceSessionModel.session_uuid == str(session_id))
        ).first()

        if not sess:
            raise ValueError("Session not found")

        sess.status = 'completed'
        sess.session_end = datetime.utcnow()

        # Enrolled students vs marked students
        enrolled = timetable_service.get_students_for_timetable(sess.timetable_id)
        present_recs = db_session.query(AttendanceRecordModel).filter(AttendanceRecordModel.session_id == sess.id).all()
        present_ids = {r.student_id for r in present_recs}

        for stu in enrolled:
            if stu["id"] not in present_ids:
                # Mark absent record
                abs_rec = AttendanceRecordModel(
                    student_id=stu["id"],
                    timetable_id=sess.timetable_id,
                    session_id=sess.id,
                    timestamp=datetime.utcnow(),
                    status='absent',
                    confidence_score=0.0
                )
                db_session.add(abs_rec)

        db_session.commit()

        total = sess.total_students or len(enrolled)
        present = len(present_ids)
        absent = total - present
        pct = round((present / total * 100), 1) if total > 0 else 0.0

        logging_service.log_audit("SESSION_STOPPED", "session", sess.id, f"Completed session #{sess.id} — Present: {present}, Absent: {absent}")
        return {
            "session_id": sess.session_uuid or str(sess.id),
            "status": "COMPLETED",
            "total_students": total,
            "present_count": present,
            "absent_count": max(0, absent),
            "attendance_percentage": pct,
            "session_start": sess.session_start.isoformat() if sess.session_start else None,
            "session_end": sess.session_end.isoformat() if sess.session_end else None
        }

    def get_session_results(self, session_id: int):
        sess = db_session.query(AttendanceSessionModel).filter(
            (AttendanceSessionModel.id == session_id) | (AttendanceSessionModel.session_uuid == str(session_id))
        ).first()
        if not sess:
            return None

        recs = db_session.query(AttendanceRecordModel).filter(AttendanceRecordModel.session_id == sess.id).all()
        records_list = []
        for r in recs:
            stu = db_session.query(StudentModel).filter(StudentModel.id == r.student_id).first()
            records_list.append({
                "id": r.id,
                "student_id": stu.gr_number if stu else "N/A",
                "name": stu.name if stu else "Unknown",
                "department": stu.department if stu else "N/A",
                "status": r.status.upper(),
                "confidence": r.confidence_score,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None
            })

        return {
            "session": self._format_session(sess),
            "records": records_list
        }

    def update_session_records(self, session_id: str, updates: list):
        sess = db_session.query(AttendanceSessionModel).filter(
            (AttendanceSessionModel.id == session_id) | (AttendanceSessionModel.session_uuid == str(session_id))
        ).first()
        if not sess:
            raise ValueError("Attendance session not found")

        for item in updates:
            stu_gr = item.get("student_id")
            status = str(item.get("status", "ABSENT")).lower()
            stu = db_session.query(StudentModel).filter(
                (StudentModel.gr_number == stu_gr) | (StudentModel.id == item.get("id"))
            ).first()

            if stu:
                rec = db_session.query(AttendanceRecordModel).filter(
                    AttendanceRecordModel.session_id == sess.id,
                    AttendanceRecordModel.student_id == stu.id
                ).first()

                if rec:
                    rec.status = status
                else:
                    rec = AttendanceRecordModel(
                        student_id=stu.id,
                        timetable_id=sess.timetable_id,
                        session_id=sess.id,
                        timestamp=datetime.utcnow(),
                        status=status,
                        confidence_score=1.0 if status == 'present' else 0.0
                    )
                    db_session.add(rec)

        db_session.commit()

        present_count = db_session.query(AttendanceRecordModel).filter(
            AttendanceRecordModel.session_id == sess.id,
            AttendanceRecordModel.status == 'present'
        ).count()
        sess.present_count = present_count
        db_session.commit()

        return self.get_session_results(sess.id)

    def _format_session(self, sess: AttendanceSessionModel) -> dict:
        tt = db_session.query(TimetableModel).filter(TimetableModel.id == sess.timetable_id).first()
        fac = db_session.query(FacultyModel).filter(FacultyModel.id == sess.faculty_id).first()
        return {
            "id": sess.id,
            "session_id": sess.session_uuid or str(sess.id),
            "faculty_id": sess.faculty_id,
            "faculty_name": fac.name if fac else "Unknown",
            "timetable_id": sess.timetable_id,
            "class_name": tt.class_name if tt else "Class",
            "subject_name": tt.subject_name if tt else "Subject",
            "start_time": sess.session_start.isoformat() if sess.session_start else None,
            "end_time": sess.session_end.isoformat() if sess.session_end else None,
            "total_students": sess.total_students,
            "present_count": sess.present_count,
            "status": sess.status.upper()
        }

attendance_service = AttendanceService()
