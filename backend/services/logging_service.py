from backend.models.database import db_session, AuditLogModel, SystemLogModel
from flask import request, g
from datetime import datetime

class LoggingService:
    @staticmethod
    def log_audit(action: str, entity_type: str = None, entity_id: str = None, details: str = None, user: dict = None):
        try:
            if not user and hasattr(g, 'current_user') and g.current_user:
                user = g.current_user

            user_id = user.get('id') if user else None
            user_email = user.get('email') if user else None
            role = user.get('role') if user else None

            ip_address = request.remote_addr if request else "internal"
            device_id = request.headers.get("X-Device-ID") if request else None

            log = AuditLogModel(
                user_id=user_id,
                user_email=user_email,
                role=role,
                action=action,
                entity_type=entity_type,
                entity_id=str(entity_id) if entity_id is not None else None,
                ip_address=ip_address,
                device_id=device_id,
                details=details,
                timestamp=datetime.utcnow()
            )
            db_session.add(log)
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            print(f"[LoggingService Audit Error] {e}")

    @staticmethod
    def log_system(message: str, level: str = "INFO", module: str = "backend"):
        try:
            req_id = getattr(g, 'request_id', None)
            sys_log = SystemLogModel(
                level=level,
                message=message,
                module=module,
                request_id=req_id,
                timestamp=datetime.utcnow()
            )
            db_session.add(sys_log)
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            print(f"[LoggingService System Error] {e}")

logging_service = LoggingService()
