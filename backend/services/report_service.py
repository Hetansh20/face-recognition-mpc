import os
import csv
from datetime import datetime
from backend.models.database import (
    db_session, AttendanceRecordModel, StudentModel, TimetableModel,
    AttendanceSessionModel, FacultyModel, AuditLogModel, SystemLogModel
)
from backend.config import Config

class ReportService:
    def get_dashboard_stats(self):
        total_students = db_session.query(StudentModel).filter(StudentModel.is_active == True).count()
        total_faculty = db_session.query(FacultyModel).filter(FacultyModel.is_active == True).count()
        total_sessions = db_session.query(AttendanceSessionModel).count()
        today_sessions = db_session.query(AttendanceSessionModel).filter(
            AttendanceSessionModel.session_start >= datetime.utcnow().replace(hour=0, minute=0, second=0)
        ).count()
        active_sessions = db_session.query(AttendanceSessionModel).filter(AttendanceSessionModel.status == 'active').count()

        today_records = db_session.query(AttendanceRecordModel).filter(
            AttendanceRecordModel.timestamp >= datetime.utcnow().replace(hour=0, minute=0, second=0)
        ).all()
        present_today = sum(1 for r in today_records if r.status.lower() == 'present')
        absent_today = sum(1 for r in today_records if r.status.lower() == 'absent')

        return {
            "total_students": total_students,
            "total_faculty": total_faculty,
            "total_sessions": total_sessions,
            "today_sessions": today_sessions,
            "active_sessions": active_sessions,
            "present_today": present_today,
            "absent_today": absent_today,
            "attendance_rate": round((present_today / (present_today + absent_today) * 100), 1) if (present_today + absent_today) > 0 else 100.0
        }

    def export_attendance_csv(self, timetable_id=None, session_id=None):
        os.makedirs(Config.REPORTS_DIR, exist_ok=True)
        filename = f"attendance_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(Config.REPORTS_DIR, filename)

        sess = None
        if session_id:
            sess = db_session.query(AttendanceSessionModel).filter(
                (AttendanceSessionModel.id == session_id) | (AttendanceSessionModel.session_uuid == str(session_id))
            ).first()
            if sess:
                timetable_id = sess.timetable_id

        tt = None
        if timetable_id:
            tt = db_session.query(TimetableModel).filter(TimetableModel.id == timetable_id).first()

        from backend.services.timetable_service import timetable_service
        enrolled_students = []
        if timetable_id:
            enrolled_students = timetable_service.get_students_for_timetable(timetable_id)

        rows = []
        if enrolled_students and sess:
            records = db_session.query(AttendanceRecordModel).filter(
                AttendanceRecordModel.session_id == sess.id
            ).all()
            rec_map = {r.student_id: r for r in records}

            class_name = tt.class_name if tt else "N/A"
            subject_name = tt.subject_name if tt else "N/A"

            for idx, stu in enumerate(enrolled_students, 1):
                rec = rec_map.get(stu["id"])
                status = rec.status.upper() if rec else "ABSENT"
                conf = rec.confidence_score if (rec and rec.confidence_score) else 0.0
                ts = rec.timestamp.isoformat() if (rec and rec.timestamp) else (sess.session_start.isoformat() if sess.session_start else "")
                
                rows.append([
                    idx,
                    class_name,
                    subject_name,
                    stu.get("gr_number", "N/A"),
                    stu.get("name", "Unknown"),
                    stu.get("department", "N/A"),
                    timetable_id,
                    sess.session_uuid or str(sess.id),
                    ts,
                    status,
                    conf
                ])
        elif enrolled_students:
            class_name = tt.class_name if tt else "N/A"
            subject_name = tt.subject_name if tt else "N/A"
            enrolled_ids = {s["id"] for s in enrolled_students}
            enrolled_map = {s["id"]: s for s in enrolled_students}

            records = db_session.query(AttendanceRecordModel).filter(
                AttendanceRecordModel.timetable_id == timetable_id,
                AttendanceRecordModel.student_id.in_(enrolled_ids)
            ).order_by(AttendanceRecordModel.timestamp.desc()).all()

            for idx, r in enumerate(records, 1):
                stu = enrolled_map.get(r.student_id)
                rows.append([
                    idx,
                    class_name,
                    subject_name,
                    stu.get("gr_number") if stu else "N/A",
                    stu.get("name") if stu else "Unknown",
                    stu.get("department") if stu else "N/A",
                    r.timetable_id,
                    r.session_id or "N/A",
                    r.timestamp.isoformat() if r.timestamp else "",
                    r.status.upper(),
                    r.confidence_score or 0.0
                ])
        else:
            query = db_session.query(AttendanceRecordModel)
            if timetable_id:
                query = query.filter(AttendanceRecordModel.timetable_id == timetable_id)
            if sess:
                query = query.filter(AttendanceRecordModel.session_id == sess.id)
            records = query.order_by(AttendanceRecordModel.timestamp.desc()).all()

            for idx, r in enumerate(records, 1):
                stu = db_session.query(StudentModel).filter(StudentModel.id == r.student_id).first()
                r_tt = db_session.query(TimetableModel).filter(TimetableModel.id == r.timetable_id).first()
                rows.append([
                    idx,
                    r_tt.class_name if r_tt else "N/A",
                    r_tt.subject_name if r_tt else "N/A",
                    stu.gr_number if stu else "N/A",
                    stu.name if stu else "Unknown",
                    stu.department if stu else "N/A",
                    r.timetable_id,
                    r.session_id or "N/A",
                    r.timestamp.isoformat() if r.timestamp else "",
                    r.status.upper(),
                    r.confidence_score or 0.0
                ])

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Record ID', 'Class Name', 'Subject', 'Student GR Number', 'Student Name', 'Department', 'Timetable ID', 'Session ID', 'Timestamp', 'Status', 'Confidence Score'])
            for row in rows:
                writer.writerow(row)

        return filepath, filename

    def export_attendance_excel(self, timetable_id=None, session_id=None):
        import pandas as pd
        os.makedirs(Config.REPORTS_DIR, exist_ok=True)
        filename = f"attendance_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = os.path.join(Config.REPORTS_DIR, filename)

        sess = None
        if session_id:
            sess = db_session.query(AttendanceSessionModel).filter(
                (AttendanceSessionModel.id == session_id) | (AttendanceSessionModel.session_uuid == str(session_id))
            ).first()
            if sess:
                timetable_id = sess.timetable_id

        tt = None
        if timetable_id:
            tt = db_session.query(TimetableModel).filter(TimetableModel.id == timetable_id).first()

        from backend.services.timetable_service import timetable_service
        enrolled_students = []
        if timetable_id:
            enrolled_students = timetable_service.get_students_for_timetable(timetable_id)

        rows = []
        if enrolled_students and sess:
            records = db_session.query(AttendanceRecordModel).filter(
                AttendanceRecordModel.session_id == sess.id
            ).all()
            rec_map = {r.student_id: r for r in records}

            class_name = tt.class_name if tt else "N/A"
            subject_name = tt.subject_name if tt else "N/A"

            for idx, stu in enumerate(enrolled_students, 1):
                rec = rec_map.get(stu["id"])
                status = rec.status.upper() if rec else "ABSENT"
                conf = rec.confidence_score if (rec and rec.confidence_score) else 0.0
                ts = rec.timestamp.isoformat() if (rec and rec.timestamp) else (sess.session_start.isoformat() if sess.session_start else "")
                
                rows.append({
                    'Record ID': idx,
                    'Class Name': class_name,
                    'Subject': subject_name,
                    'Student GR Number': stu.get("gr_number", "N/A"),
                    'Student Name': stu.get("name", "Unknown"),
                    'Department': stu.get("department", "N/A"),
                    'Timetable ID': timetable_id,
                    'Session ID': sess.session_uuid or str(sess.id),
                    'Timestamp': ts,
                    'Status': status,
                    'Confidence Score': conf
                })
        else:
            query = db_session.query(AttendanceRecordModel)
            if timetable_id:
                query = query.filter(AttendanceRecordModel.timetable_id == timetable_id)
            if sess:
                query = query.filter(AttendanceRecordModel.session_id == sess.id)
            records = query.order_by(AttendanceRecordModel.timestamp.desc()).all()

            for idx, r in enumerate(records, 1):
                stu = db_session.query(StudentModel).filter(StudentModel.id == r.student_id).first()
                r_tt = db_session.query(TimetableModel).filter(TimetableModel.id == r.timetable_id).first()
                rows.append({
                    'Record ID': idx,
                    'Class Name': r_tt.class_name if r_tt else "N/A",
                    'Subject': r_tt.subject_name if r_tt else "N/A",
                    'Student GR Number': stu.gr_number if stu else "N/A",
                    'Student Name': stu.name if stu else "Unknown",
                    'Department': stu.department if stu else "N/A",
                    'Timetable ID': r.timetable_id,
                    'Session ID': r.session_id or "N/A",
                    'Timestamp': r.timestamp.isoformat() if r.timestamp else "",
                    'Status': r.status.upper(),
                    'Confidence Score': r.confidence_score or 0.0
                })

        df = pd.DataFrame(rows)
        if df.empty:
            df = pd.DataFrame(columns=['Record ID', 'Class Name', 'Subject', 'Student GR Number', 'Student Name', 'Department', 'Timetable ID', 'Session ID', 'Timestamp', 'Status', 'Confidence Score'])

        df.to_excel(filepath, index=False, engine='openpyxl')
        return filepath, filename

    def get_audit_logs(self, limit=100, action=None, user_email=None):
        query = db_session.query(AuditLogModel)
        if action:
            query = query.filter(AuditLogModel.action.ilike(f"%{action}%"))
        if user_email:
            query = query.filter(AuditLogModel.user_email.ilike(f"%{user_email}%"))
        logs = query.order_by(AuditLogModel.timestamp.desc()).limit(limit).all()
        return [{
            "id": l.id,
            "user_id": l.user_id,
            "user_email": l.user_email,
            "role": l.role,
            "action": l.action,
            "entity_type": l.entity_type,
            "entity_id": l.entity_id,
            "ip_address": l.ip_address,
            "device_id": l.device_id,
            "details": l.details,
            "timestamp": l.timestamp.isoformat() if l.timestamp else None
        } for l in logs]

    def get_system_logs(self, limit=100, level=None):
        query = db_session.query(SystemLogModel)
        if level:
            query = query.filter(SystemLogModel.level.ilike(level))
        logs = query.order_by(SystemLogModel.timestamp.desc()).limit(limit).all()
        return [{
            "id": l.id,
            "level": l.level,
            "message": l.message,
            "module": l.module,
            "request_id": l.request_id,
            "timestamp": l.timestamp.isoformat() if l.timestamp else None
        } for l in logs]

report_service = ReportService()
