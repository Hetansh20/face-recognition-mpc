from sqlalchemy import text
from flask import Blueprint, jsonify
from backend.models.database import db_session, UserModel
from backend.face_engine.face_engine import face_service
from backend.utils.response import api_response

health_bp = Blueprint("health_bp", __name__, url_prefix="/api/v1/health")

@health_bp.route("", methods=["GET"])
def health_check():
    db_status = "healthy"
    try:
        db_session.execute(text("SELECT 1"))
    except Exception:
        db_status = "unhealthy"

    face_status = "ready" if face_service.is_initialized else "uninitialized"

    return api_response(data={
        "status": "healthy" if db_status == "healthy" else "degraded",
        "service": "FaceAttend API Backend",
        "version": "1.0.0",
        "database": db_status,
        "face_engine": face_status
    })

@health_bp.route("/database", methods=["GET"])
def database_health():
    try:
        count = db_session.query(UserModel).count()
        return api_response(data={"database": "healthy", "users_count": count})
    except Exception as e:
        return jsonify({"success": False, "error": {"code": "DATABASE_ERROR", "message": str(e)}}), 500

@health_bp.route("/face-engine", methods=["GET"])
def face_engine_health():
    face_service.initialize()
    return api_response(data={
        "status": "ready",
        "model": "buffalo_sc",
        "detector": "InsightFace (RetinaFace)",
        "yolo_sweep": "yolov8n-face.pt"
    })
