import os
import json
import sqlite3
try:
    import psycopg2
except ImportError:
    psycopg2 = None
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Boolean, DateTime, Float, Text, ForeignKey, Table, Index
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, scoped_session
from backend.config import Config

Base = declarative_base()

# ── ORM Models ─────────────────────────────────────────────────────────

class UserModel(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="STUDENT")  # ADMIN, FACULTY, STUDENT
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class FacultyModel(Base):
    __tablename__ = 'faculties'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    department = Column(String(255), nullable=False)
    passcode_hash = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class SemesterModel(Base):
    __tablename__ = 'semesters'
    id = Column(Integer, primary_key=True, autoincrement=True)
    number = Column(Integer, unique=True, nullable=False)
    label = Column(String(100), nullable=True)
    level = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ClassModel(Base):
    __tablename__ = 'classes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    semester_id = Column(Integer, ForeignKey('semesters.id'), nullable=False)
    name = Column(String(100), nullable=False)
    section = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class BatchModel(Base):
    __tablename__ = 'batches'
    id = Column(Integer, primary_key=True, autoincrement=True)
    class_id = Column(Integer, ForeignKey('classes.id'), nullable=False)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class StudentModel(Base):
    __tablename__ = 'students'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    gr_number = Column(String(100), unique=True, nullable=True, index=True)
    enrollment_number = Column(String(100), unique=True, nullable=True, index=True)
    student_id = Column(String(100), nullable=True)  # legacy alias
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    department = Column(String(255), nullable=False)
    class_id = Column(Integer, ForeignKey('classes.id'), nullable=True)
    batch_id = Column(Integer, ForeignKey('batches.id'), nullable=True)
    roll_number = Column(String(50), nullable=True)
    phone = Column(String(50), nullable=True)
    face_pid = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class TimetableModel(Base):
    __tablename__ = 'timetables'
    id = Column(Integer, primary_key=True, autoincrement=True)
    faculty_id = Column(Integer, ForeignKey('faculties.id'), nullable=False)
    class_name = Column(String(255), nullable=False)
    class_id = Column(Integer, ForeignKey('classes.id'), nullable=True)
    batch_id = Column(Integer, ForeignKey('batches.id'), nullable=True)
    semester = Column(String(50), nullable=True)
    subject_name = Column(String(255), nullable=True)
    day_of_week = Column(String(50), nullable=False)
    start_time = Column(String(20), nullable=False)
    end_time = Column(String(20), nullable=False)
    room_number = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class FaceProfileModel(Base):
    __tablename__ = 'face_profiles'
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    face_pid = Column(String(255), nullable=False)
    image_path = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class FaceEmbeddingModel(Base):
    __tablename__ = 'face_embeddings'
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    face_pid = Column(String(255), nullable=False)
    embedding_json = Column(Text, nullable=False)
    model_name = Column(String(100), default="buffalo_sc")
    model_version = Column(String(50), default="1.0")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AttendanceSessionModel(Base):
    __tablename__ = 'attendance_sessions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_uuid = Column(String(100), unique=True, nullable=True)
    faculty_id = Column(Integer, ForeignKey('faculties.id'), nullable=False)
    timetable_id = Column(Integer, ForeignKey('timetables.id'), nullable=False)
    session_start = Column(DateTime, default=datetime.utcnow)
    session_end = Column(DateTime, nullable=True)
    total_students = Column(Integer, default=0)
    present_count = Column(Integer, default=0)
    status = Column(String(50), default='active') # active, completed, cancelled
    device_id = Column(String(100), nullable=True)

class AttendanceRecordModel(Base):
    __tablename__ = 'attendance'
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    timetable_id = Column(Integer, ForeignKey('timetables.id'), nullable=False)
    session_id = Column(Integer, ForeignKey('attendance_sessions.id'), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default='present')
    confidence_score = Column(Float, nullable=True)

class FacultySubstitutionModel(Base):
    __tablename__ = 'faculty_substitutions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    original_faculty_id = Column(Integer, ForeignKey('faculties.id'), nullable=False)
    substitute_faculty_id = Column(Integer, ForeignKey('faculties.id'), nullable=False)
    timetable_id = Column(Integer, ForeignKey('timetables.id'), nullable=False)
    date = Column(String(50), nullable=False)
    reason = Column(Text, default='')
    status = Column(String(50), default='active')
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLogModel(Base):
    __tablename__ = 'audit_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=True)
    user_email = Column(String(255), nullable=True)
    role = Column(String(50), nullable=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=True)
    entity_id = Column(String(100), nullable=True)
    ip_address = Column(String(100), nullable=True)
    device_id = Column(String(100), nullable=True)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

class SystemLogModel(Base):
    __tablename__ = 'system_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    level = Column(String(20), default="INFO")
    message = Column(Text, nullable=False)
    module = Column(String(100), nullable=True)
    request_id = Column(String(100), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

class DeviceModel(Base):
    __tablename__ = 'devices'
    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String(255), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    device_name = Column(String(255), nullable=True)
    platform = Column(String(50), default="Android")
    app_version = Column(String(50), nullable=True)
    status = Column(String(50), default="ACTIVE") # ACTIVE, BLOCKED
    last_seen = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

class RefreshTokenModel(Base):
    __tablename__ = 'refresh_tokens'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    token = Column(String(512), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# ── Database Initialization ────────────────────────────────────────────

db_url = Config.DATABASE_URL
if db_url.startswith("sqlite"):
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
else:
    engine = create_engine(db_url, pool_size=10, max_overflow=20)

SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db_session = scoped_session(SessionFactory)

def init_db():
    """Create all tables in relational database."""
    Base.metadata.create_all(bind=engine)
