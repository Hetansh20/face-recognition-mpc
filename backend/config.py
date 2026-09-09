import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

class Config:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ROOT_DIR = os.path.dirname(BASE_DIR)
    
    # Environment & Server
    ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "t")
    PORT = int(os.getenv("PORT", 5000))
    HOST = os.getenv("HOST", "0.0.0.0")
    
    # Secrets & JWT
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production-faceattend-2026")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secret-key-change-in-production-faceattend-2026")
    JWT_REFRESH_SECRET_KEY = os.getenv("JWT_REFRESH_SECRET_KEY", "jwt-refresh-secret-change-in-production-2026")
    ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.getenv("ACCESS_TOKEN_EXPIRES_HOURS", 8)))
    REFRESH_TOKEN_EXPIRES = timedelta(days=int(os.getenv("REFRESH_TOKEN_EXPIRES_DAYS", 30)))
    
    # Persistent data directory — point this at a mounted volume in
    # production (e.g. Railway Volumes) so uploaded face photos, the trained
    # embedding cache, and the SQLite file (if not using Postgres) survive
    # redeploys. Defaults to the project root for local development.
    DATA_DIR = os.getenv("DATA_DIR", ROOT_DIR)

    # Database Configuration — set DATABASE_URL to a postgres:// URL in
    # production (e.g. Railway's managed Postgres addon); SQLite is fine for
    # local development only, since it lives on disk under DATA_DIR.
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(DATA_DIR, 'attendance_system.db')}"
    )

    # Storage Paths
    FACES_DIR = os.path.join(DATA_DIR, "registered_faces")
    FACE_DB_JSON = os.path.join(DATA_DIR, "face_database.json")
    EMB_CACHE_PKL = os.path.join(DATA_DIR, "face_embeddings_insightface.pkl")
    REPORTS_DIR = os.path.join(DATA_DIR, "attendance_reports")
    YOLO_MODEL_PATH = os.path.join(ROOT_DIR, "yolov8n-face.pt")
    
    # Face Recognition Thresholds
    COSINE_MATCH_THRESHOLD = float(os.getenv("COSINE_MATCH_THRESHOLD", 0.55))
    GROUP_MATCH_THRESHOLD = float(os.getenv("GROUP_MATCH_THRESHOLD", 0.75))
    
    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

    # Email (Brevo API preferred, Gmail SMTP fallback) — used to send
    # present/absent CSVs to faculty after confirming attendance
    SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")
    SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "")
    BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
