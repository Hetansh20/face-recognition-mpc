import uuid
from datetime import datetime
from backend.models.database import (
    db_session, AttendanceSessionModel, AttendanceRecordModel,
    TimetableModel, StudentModel, FacultyModel
)
from backend.services.timetable_service import timetable_service
from backend.services.logging_service import logging_service
from backend.services.report_service import report_service
from backend.services.email_service import email_service
from backend.utils.security import verify_password
from backend.face_engine.face_engine import face_service
from backend.face_engine.group_recognizer import process_group_photo

class AttendanceService:
    def _auto_register_student(self, pid, gr_number, name):
        """Creates a students row for a face that matched the embedding
        cache but has no corresponding student record yet — mirrors the
        web app's auto-registration in api_group_photo_attend/confirm_attendance."""
        gr = gr_number or pid or name or f"AUTO-{uuid.uuid4().hex[:8]}"
        existing = db_session.query(StudentModel).filter(
            (StudentModel.gr_number == gr) | (StudentModel.face_pid == pid)
        ).first()
        if existing:
            return existing

        email = f"{str(gr).replace(' ', '_').lower()}@student.local"
        stu = StudentModel(
            gr_number=gr,
            name=name or gr,
            email=email,
            department="Unassigned",
            face_pid=pid,
            is_active=True
        )
        try:
            db_session.add(stu)
            db_session.commit()
            logging_service.log_audit("STUDENT_AUTO_REGISTERED", "student", stu.id, f"Auto-registered {stu.name} ({gr}) from face recognition")
            return stu
        except Exception:
            db_session.rollback()
            return db_session.query(StudentModel).filter(
                (StudentModel.gr_number == gr) | (StudentModel.face_pid == pid)
            ).first()

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
                if not stu:
                    stu = self._auto_register_student(pid, stu_gr, matched.get("name"))

                if stu:
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
            if not stu:
                stu = self._auto_register_student(pid, stu_gr, matched.get("name"))

            if stu:
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

    def review_group_photos(self, session_id, images: list):
        """Runs recognition on up to 3 group photos WITHOUT committing any
        attendance — mirrors the web app's multi_photo_attend. Duplicate
        matches across photos are merged, keeping the highest-confidence
        occurrence. Faculty reviews/edits the resulting present/absent
        lists client-side, then calls confirm_attendance() to commit."""
        sess = db_session.query(AttendanceSessionModel).filter(
            (AttendanceSessionModel.id == session_id) | (AttendanceSessionModel.session_uuid == str(session_id))
        ).first()
        if not sess:
            raise ValueError("Attendance session not found")

        students = timetable_service.get_students_for_timetable(sess.timetable_id)
        enrolled_pids = {s["face_pid"] for s in students if s.get("face_pid")}
        target_pids = enrolled_pids if enrolled_pids else None

        merged = {}
        total_faces = 0
        unrecognized_total = 0
        annotated_images = []

        for image_bytes in images[:3]:
            res = process_group_photo(image_bytes, target_pids=target_pids)
            total_faces += res.get("total_faces", 0)
            unrecognized_total += res.get("unrecognized_count", 0)
            if res.get("annotated_image"):
                annotated_images.append(res["annotated_image"])

            for person in res.get("recognized", []):
                key = person.get("person_id") or person.get("student_id")
                if key not in merged or person.get("confidence", 0) > merged[key].get("confidence", 0):
                    merged[key] = person

        recognized_list = list(merged.values())
        recognized_keys = {p.get("person_id") for p in recognized_list} | {p.get("student_id") for p in recognized_list}

        present, absent = [], []
        for s in students:
            match = next(
                (p for p in recognized_list if p.get("person_id") == s.get("face_pid") or p.get("student_id") == s.get("gr_number")),
                None
            )
            entry = {
                "gr_number": s.get("gr_number"),
                "name": s.get("name"),
                "email": s.get("email"),
                "department": s.get("department"),
                "confidence": match.get("confidence") if match else None
            }
            (present if match else absent).append(entry)

        # Recognized faces that matched the embedding cache but aren't on
        # this timetable's roster — still surfaced as present-for-review,
        # will be auto-registered on confirm (mirrors web behavior).
        roster_keys = {s.get("face_pid") for s in students} | {s.get("gr_number") for s in students}
        for p in recognized_list:
            if p.get("person_id") not in roster_keys and p.get("student_id") not in roster_keys:
                present.append({
                    "gr_number": p.get("student_id"),
                    "name": p.get("name"),
                    "email": None,
                    "department": None,
                    "confidence": p.get("confidence"),
                    "person_id": p.get("person_id"),
                    "unregistered": True
                })

        return {
            "session_id": sess.session_uuid or str(sess.id),
            "total_faces": total_faces,
            "recognized_count": len(present),
            "unrecognized_count": unrecognized_total,
            "present": present,
            "absent": absent,
            "annotated_images": annotated_images
        }

    def confirm_attendance(self, session_id, present_entries: list, faculty_email: str = None, faculty_name: str = None):
        """Commits the faculty-edited present list from review_group_photos,
        auto-registering any unregistered-but-recognized faces, then emails
        the present/absent CSVs to the faculty — mirrors the web app's
        api_confirm_attendance."""
        sess = db_session.query(AttendanceSessionModel).filter(
            (AttendanceSessionModel.id == session_id) | (AttendanceSessionModel.session_uuid == str(session_id))
        ).first()
        if not sess:
            raise ValueError("Attendance session not found")

        marked, skipped = [], []
        for entry in present_entries:
            gr = entry.get("gr_number")
            name = entry.get("name")
            stu = db_session.query(StudentModel).filter(StudentModel.gr_number == gr).first() if gr else None
            if not stu:
                stu = self._auto_register_student(entry.get("person_id"), gr, name)
            if not stu:
                skipped.append({"gr_number": gr, "name": name, "reason": "could not register student"})
                continue

            existing = db_session.query(AttendanceRecordModel).filter(
                AttendanceRecordModel.session_id == sess.id,
                AttendanceRecordModel.student_id == stu.id
            ).first()
            if not existing:
                conf = entry.get("confidence")
                rec = AttendanceRecordModel(
                    student_id=stu.id,
                    timetable_id=sess.timetable_id,
                    session_id=sess.id,
                    timestamp=datetime.utcnow(),
                    status='present',
                    confidence_score=(float(conf) / 100.0 if conf is not None else None)
                )
                db_session.add(rec)
                sess.present_count = (sess.present_count or 0) + 1
            marked.append({"gr_number": stu.gr_number, "name": stu.name})

        db_session.commit()
        logging_service.log_audit("ATTENDANCE_CONFIRMED", "session", sess.id, f"Confirmed attendance for {len(marked)} students")

        email_status = {"present_sent": False, "absent_sent": False, "message": "Faculty email not provided"}
        if faculty_email:
            present_csv, present_fn = report_service.build_session_csv_bytes(sess.id)
            absent_csv, absent_fn = report_service.build_absent_csv_bytes(sess.id)
            ok1, msg1 = email_service.send_csv_attachment(
                faculty_email, faculty_name or "Faculty", present_csv, present_fn,
                subject=f"Attendance Present - {datetime.utcnow().strftime('%Y-%m-%d')}"
            )
            ok2, msg2 = email_service.send_csv_attachment(
                faculty_email, faculty_name or "Faculty", absent_csv, absent_fn,
                subject=f"Attendance Absent - {datetime.utcnow().strftime('%Y-%m-%d')}"
            )
            email_status = {"present_sent": ok1, "absent_sent": ok2, "message": f"{msg1}; {msg2}"}

        return {
            "session_id": sess.session_uuid or str(sess.id),
            "marked": marked,
            "skipped": skipped,
            "present_count": sess.present_count,
            "email_status": email_status
        }

    def stop_session(self, session_id: int, passcode: str = None):
        """Stops attendance session and calculates absent records. If the
        faculty account has a passcode set, it must be supplied and verified
        before the session can be stopped — mirrors the web app's re-auth
        gate on /api/faculty/stop_session."""
        sess = db_session.query(AttendanceSessionModel).filter(
            (AttendanceSessionModel.id == session_id) | (AttendanceSessionModel.session_uuid == str(session_id))
        ).first()

        if not sess:
            raise ValueError("Session not found")

        fac = db_session.query(FacultyModel).filter(FacultyModel.id == sess.faculty_id).first()
        if fac and fac.passcode_hash:
            if not passcode or not verify_password(passcode, fac.passcode_hash):
                raise ValueError("Invalid passcode. Cannot stop session.")

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
