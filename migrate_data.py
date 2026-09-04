import os
import sys
import json
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from backend.config import Config
from backend.models.database import (
    Base, engine, db_session, UserModel, FacultyModel, StudentModel,
    SemesterModel, ClassModel, BatchModel, TimetableModel,
    AttendanceSessionModel, AttendanceRecordModel,
    FaceProfileModel, FaceEmbeddingModel
)
from backend.utils.security import hash_password

def run_migration():
    print("=" * 60)
    print("      FACEATTEND DATA MIGRATION ENGINE")
    print("=" * 60)

    sqlite_path = os.path.join(BASE_DIR, "attendance_system.db")
    if not os.path.exists(sqlite_path):
        print(f"[Error] SQLite database not found at {sqlite_path}")
        return

    # If target DB is SQLite file, ensure missing columns exist or create fresh schema
    conn_raw = sqlite3.connect(sqlite_path)
    conn_raw.row_factory = sqlite3.Row
    cur_raw = conn_raw.cursor()

    # Read existing raw tables into memory
    print("[1/5] Reading existing legacy database tables...")
    cur_raw.execute("SELECT * FROM faculties")
    raw_faculties = cur_raw.fetchall()

    cur_raw.execute("SELECT * FROM students")
    raw_students = cur_raw.fetchall()

    cur_raw.execute("SELECT * FROM timetables")
    raw_timetables = cur_raw.fetchall()

    cur_raw.execute("SELECT * FROM attendance_sessions")
    raw_sessions = cur_raw.fetchall()

    cur_raw.execute("SELECT * FROM attendance")
    raw_attendance = cur_raw.fetchall()

    cur_raw.execute("SELECT * FROM semesters")
    raw_semesters = cur_raw.fetchall()

    cur_raw.execute("SELECT * FROM classes")
    raw_classes = cur_raw.fetchall()

    cur_raw.execute("SELECT * FROM batches")
    raw_batches = cur_raw.fetchall()

    conn_raw.close()

    # Alter columns on existing legacy tables if using SQLite BEFORE metadata reflection
    if Config.DATABASE_URL.startswith("sqlite"):
        with engine.connect() as con:
            for col_stmt in [
                "ALTER TABLE faculties ADD COLUMN user_id INTEGER REFERENCES users(id)",
                "ALTER TABLE students ADD COLUMN user_id INTEGER REFERENCES users(id)",
                "ALTER TABLE students ADD COLUMN gr_number VARCHAR(100)",
                "ALTER TABLE students ADD COLUMN enrollment_number VARCHAR(100)",
                "ALTER TABLE students ADD COLUMN face_pid VARCHAR(255)",
                "ALTER TABLE attendance_sessions ADD COLUMN session_uuid VARCHAR(100)",
                "ALTER TABLE attendance_sessions ADD COLUMN device_id VARCHAR(100)",
                "ALTER TABLE attendance ADD COLUMN session_id INTEGER REFERENCES attendance_sessions(id)",
                "ALTER TABLE attendance ADD COLUMN confidence_score FLOAT"
            ]:
                try:
                    con.exec_driver_sql(col_stmt)
                except Exception:
                    pass

    # Drop/Create missing tables on engine to apply new relational schema cleanly
    print("[2/5] Initializing target relational database schema...")
    Base.metadata.create_all(bind=engine)

    stats = {
        "admin": 0,
        "faculty": 0,
        "semesters": 0,
        "classes": 0,
        "batches": 0,
        "students": 0,
        "timetables": 0,
        "sessions": 0,
        "attendance": 0,
        "face_profiles": 0,
        "errors": 0
    }

    try:
        # 1. Admin Account
        admin_email = "admin123@gmail.com"
        admin = db_session.query(UserModel).filter(UserModel.email == admin_email).first()
        if not admin:
            admin = UserModel(
                email=admin_email,
                password_hash=hash_password("admin123"),
                full_name="System Administrator",
                role="ADMIN",
                is_active=True
            )
            db_session.add(admin)
            db_session.commit()
            stats["admin"] += 1
            print(f"[Migration] Primary admin account created ({admin_email})")

        # 2. Semesters
        for row in raw_semesters:
            s = db_session.query(SemesterModel).filter(SemesterModel.id == row["id"]).first()
            if not s:
                s = SemesterModel(
                    id=row["id"],
                    number=row["number"],
                    label=row["label"] if "label" in row.keys() else None,
                    level=row["level"] if "level" in row.keys() else None
                )
                db_session.add(s)
                stats["semesters"] += 1
        db_session.commit()

        # 3. Classes
        for row in raw_classes:
            c = db_session.query(ClassModel).filter(ClassModel.id == row["id"]).first()
            if not c:
                c = ClassModel(
                    id=row["id"],
                    semester_id=row["semester_id"],
                    name=row["name"],
                    section=row["section"] if "section" in row.keys() else None
                )
                db_session.add(c)
                stats["classes"] += 1
        db_session.commit()

        # 4. Batches
        for row in raw_batches:
            b = db_session.query(BatchModel).filter(BatchModel.id == row["id"]).first()
            if not b:
                b = BatchModel(
                    id=row["id"],
                    class_id=row["class_id"],
                    name=row["name"]
                )
                db_session.add(b)
                stats["batches"] += 1
        db_session.commit()

        # 5. Faculty & User Mapping
        for row in raw_faculties:
            fac_email = row["email"].lower().strip()
            user = db_session.query(UserModel).filter(UserModel.email == fac_email).first()
            if not user:
                user = UserModel(
                    email=fac_email,
                    password_hash=row["passcode_hash"],
                    full_name=row["name"],
                    role="FACULTY",
                    is_active=bool(row["is_active"]) if "is_active" in row.keys() else True
                )
                db_session.add(user)
                db_session.commit()

            fac = db_session.query(FacultyModel).filter(FacultyModel.id == row["id"]).first()
            if not fac:
                fac = FacultyModel(
                    id=row["id"],
                    user_id=user.id,
                    name=row["name"],
                    email=fac_email,
                    department=row["department"],
                    passcode_hash=row["passcode_hash"],
                    is_active=bool(row["is_active"]) if "is_active" in row.keys() else True
                )
                db_session.add(fac)
                stats["faculty"] += 1
            else:
                fac.user_id = user.id
        db_session.commit()

        # 6. Students & User Mapping
        for row in raw_students:
            stu_email = row["email"].lower().strip()
            gr_num = row["gr_number"] if "gr_number" in row.keys() and row["gr_number"] else f"GR_{row['id']}"

            user = db_session.query(UserModel).filter(UserModel.email == stu_email).first()
            if not user:
                user = UserModel(
                    email=stu_email,
                    password_hash=hash_password("student123"),
                    full_name=row["name"],
                    role="STUDENT",
                    is_active=bool(row["is_active"]) if "is_active" in row.keys() else True
                )
                db_session.add(user)
                db_session.commit()

            stu = db_session.query(StudentModel).filter(StudentModel.id == row["id"]).first()
            if not stu:
                stu = StudentModel(
                    id=row["id"],
                    user_id=user.id,
                    gr_number=gr_num,
                    enrollment_number=row["enrollment_number"] if "enrollment_number" in row.keys() else None,
                    student_id=gr_num,
                    name=row["name"],
                    email=stu_email,
                    department=row["department"],
                    class_id=row["class_id"] if "class_id" in row.keys() else None,
                    batch_id=row["batch_id"] if "batch_id" in row.keys() else None,
                    roll_number=row["roll_number"] if "roll_number" in row.keys() else None,
                    phone=row["phone"] if "phone" in row.keys() else None,
                    face_pid=row["face_pid"] if "face_pid" in row.keys() else None,
                    is_active=bool(row["is_active"]) if "is_active" in row.keys() else True
                )
                db_session.add(stu)
                stats["students"] += 1
            else:
                stu.user_id = user.id
                if not stu.gr_number: stu.gr_number = gr_num
        db_session.commit()

        # 7. Timetables
        for row in raw_timetables:
            t = db_session.query(TimetableModel).filter(TimetableModel.id == row["id"]).first()
            if not t:
                t = TimetableModel(
                    id=row["id"],
                    faculty_id=row["faculty_id"],
                    class_name=row["class_name"],
                    class_id=row["class_id"] if "class_id" in row.keys() else None,
                    batch_id=row["batch_id"] if "batch_id" in row.keys() else None,
                    subject_name=row["subject_name"] if "subject_name" in row.keys() else None,
                    day_of_week=row["day_of_week"],
                    start_time=row["start_time"],
                    end_time=row["end_time"],
                    room_number=row["room_number"] if "room_number" in row.keys() else None
                )
                db_session.add(t)
                stats["timetables"] += 1
        db_session.commit()

        # 8. Attendance Sessions
        for row in raw_sessions:
            sess = db_session.query(AttendanceSessionModel).filter(AttendanceSessionModel.id == row["id"]).first()
            if not sess:
                sess = AttendanceSessionModel(
                    id=row["id"],
                    session_uuid=f"session-migrated-{row['id']}",
                    faculty_id=row["faculty_id"],
                    timetable_id=row["timetable_id"],
                    total_students=row["total_students"] if "total_students" in row.keys() else 0,
                    present_count=row["present_count"] if "present_count" in row.keys() else 0,
                    status=row["status"] if "status" in row.keys() else 'completed'
                )
                db_session.add(sess)
                stats["sessions"] += 1
        db_session.commit()

        # 9. Attendance Records
        for row in raw_attendance:
            att = db_session.query(AttendanceRecordModel).filter(AttendanceRecordModel.id == row["id"]).first()
            if not att:
                att = AttendanceRecordModel(
                    id=row["id"],
                    student_id=row["student_id"],
                    timetable_id=row["timetable_id"],
                    status=row["status"] if "status" in row.keys() else 'present',
                    confidence_score=row["confidence_score"] if "confidence_score" in row.keys() else 1.0
                )
                db_session.add(att)
                stats["attendance"] += 1
        db_session.commit()

        # 10. Face JSON metadata
        if os.path.exists(Config.FACE_DB_JSON):
            with open(Config.FACE_DB_JSON, "r") as f:
                face_db = json.load(f)
                for pid, info in face_db.items():
                    gr_num = info.get("gr_number")
                    stu = db_session.query(StudentModel).filter(
                        (StudentModel.face_pid == pid) | (StudentModel.gr_number == gr_num)
                    ).first()
                    if stu:
                        img_paths = info.get("image_paths", [])
                        img_p = img_paths[0] if img_paths else None
                        fp = db_session.query(FaceProfileModel).filter(FaceProfileModel.face_pid == pid).first()
                        if not fp:
                            fp = FaceProfileModel(student_id=stu.id, face_pid=pid, image_path=img_p)
                            db_session.add(fp)
                            stats["face_profiles"] += 1
            db_session.commit()

    except Exception as e:
        db_session.rollback()
        stats["errors"] += 1
        print(f"[Migration Error] {e}")

    print("\n" + "=" * 60)
    print("           MIGRATION SUMMARY REPORT")
    print("=" * 60)
    print(f"  Admin users created:      {stats['admin']}")
    print(f"  Faculty migrated:         {stats['faculty']}")
    print(f"  Semesters migrated:       {stats['semesters']}")
    print(f"  Classes migrated:         {stats['classes']}")
    print(f"  Batches migrated:         {stats['batches']}")
    print(f"  Students migrated:        {stats['students']}")
    print(f"  Timetable records:        {stats['timetables']}")
    print(f"  Attendance sessions:      {stats['sessions']}")
    print(f"  Attendance records:       {stats['attendance']}")
    print(f"  Face profiles migrated:   {stats['face_profiles']}")
    print(f"  Errors encountered:       {stats['errors']}")
    print("=" * 60)

if __name__ == "__main__":
    run_migration()
