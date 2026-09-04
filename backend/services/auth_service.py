from datetime import datetime, timezone, timedelta
from backend.models.database import db_session, UserModel, FacultyModel, StudentModel, RefreshTokenModel
from backend.utils.security import (
    hash_password, verify_password, generate_access_token, generate_refresh_token, decode_refresh_token
)
from backend.services.logging_service import logging_service
from backend.config import Config

class AuthService:
    def login(self, email_or_username: str, password: str):
        email_clean = email_or_username.strip().lower()

        # 1. Admin Fallback Check
        if (email_clean == "admin123@gmail.com" or email_clean == "admin") and password == "admin123":
            # Ensure admin user exists in DB
            admin = db_session.query(UserModel).filter(UserModel.email == "admin123@gmail.com").first()
            if not admin:
                admin = UserModel(
                    email="admin123@gmail.com",
                    password_hash=hash_password("admin123"),
                    full_name="System Administrator",
                    role="ADMIN",
                    is_active=True
                )
                db_session.add(admin)
                db_session.commit()

            access_token = generate_access_token(admin.id, admin.role, admin.email)
            refresh_token = generate_refresh_token(admin.id)
            self._save_refresh_token(admin.id, refresh_token)

            logging_service.log_audit("LOGIN", "user", admin.id, "Admin login successful", user={"id": admin.id, "email": admin.email, "role": admin.role})
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer",
                "expires_in": int(Config.ACCESS_TOKEN_EXPIRES.total_seconds()),
                "user": {
                    "id": admin.id,
                    "email": admin.email,
                    "full_name": admin.full_name,
                    "role": admin.role
                }
            }, None

        # 2. Check User Table
        user = db_session.query(UserModel).filter(UserModel.email == email_clean).first()
        if user and user.is_active:
            if verify_password(password, user.password_hash):
                access_token = generate_access_token(user.id, user.role, user.email)
                refresh_token = generate_refresh_token(user.id)
                self._save_refresh_token(user.id, refresh_token)

                user_info = {
                    "id": user.id,
                    "email": user.email,
                    "full_name": user.full_name,
                    "role": user.role
                }

                fac = db_session.query(FacultyModel).filter(FacultyModel.email == user.email).first()
                if fac:
                    user_info["faculty_id"] = fac.id
                    user_info["department"] = fac.department

                logging_service.log_audit("LOGIN", "user", user.id, f"User {user.email} logged in", user={"id": user.id, "email": user.email, "role": user.role})
                return {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_type": "Bearer",
                    "expires_in": int(Config.ACCESS_TOKEN_EXPIRES.total_seconds()),
                    "user": user_info
                }, None

        # 3. Check Faculty table passcode fallback
        fac = db_session.query(FacultyModel).filter(FacultyModel.email == email_clean).first()
        if not fac:
            # Try searching by passcode match
            all_facs = db_session.query(FacultyModel).filter(FacultyModel.is_active == True).all()
            for f in all_facs:
                if f.passcode_hash and verify_password(password, f.passcode_hash):
                    fac = f
                    break

        if fac and fac.is_active:
            # Find or create corresponding user
            user = db_session.query(UserModel).filter(UserModel.email == fac.email).first()
            if not user:
                user = UserModel(
                    email=fac.email,
                    password_hash=fac.passcode_hash or hash_password(password),
                    full_name=fac.name,
                    role="FACULTY",
                    is_active=True
                )
                db_session.add(user)
                db_session.commit()
                fac.user_id = user.id
                db_session.commit()

            access_token = generate_access_token(user.id, "FACULTY", user.email, extra={"faculty_id": fac.id})
            refresh_token = generate_refresh_token(user.id)
            self._save_refresh_token(user.id, refresh_token)

            logging_service.log_audit("LOGIN", "faculty", fac.id, f"Faculty {fac.name} logged in", user={"id": user.id, "email": user.email, "role": "FACULTY"})
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer",
                "expires_in": int(Config.ACCESS_TOKEN_EXPIRES.total_seconds()),
                "user": {
                    "id": user.id,
                    "faculty_id": fac.id,
                    "email": user.email,
                    "full_name": fac.name,
                    "role": "FACULTY",
                    "department": fac.department
                }
            }, None

        return None, "Invalid email, username, or password/passcode"

    def refresh_token(self, token_str: str):
        payload = decode_refresh_token(token_str)
        if not payload:
            return None, "Invalid or expired refresh token"

        user_id = payload.get("sub")
        saved = db_session.query(RefreshTokenModel).filter(
            RefreshTokenModel.token == token_str,
            RefreshTokenModel.user_id == user_id,
            RefreshTokenModel.revoked == False
        ).first()

        if not saved or saved.expires_at < datetime.utcnow():
            return None, "Refresh token revoked or expired"

        user = db_session.query(UserModel).filter(UserModel.id == user_id).first()
        if not user or not user.is_active:
            return None, "User account inactive"

        new_access_token = generate_access_token(user.id, user.role, user.email)
        return {
            "access_token": new_access_token,
            "token_type": "Bearer",
            "expires_in": int(Config.ACCESS_TOKEN_EXPIRES.total_seconds())
        }, None

    def logout(self, user_id: int, refresh_token_str: str = None):
        if refresh_token_str:
            saved = db_session.query(RefreshTokenModel).filter(RefreshTokenModel.token == refresh_token_str).first()
            if saved:
                saved.revoked = True
                db_session.commit()
        logging_service.log_audit("LOGOUT", "user", user_id, "User logged out")
        return True

    def get_user_profile(self, user_id: int):
        user = db_session.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            return None
        prof = {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }

        if user.role == "FACULTY":
            fac = db_session.query(FacultyModel).filter(FacultyModel.email == user.email).first()
            if fac:
                prof["faculty_id"] = fac.id
                prof["department"] = fac.department
        elif user.role == "STUDENT":
            stu = db_session.query(StudentModel).filter(StudentModel.email == user.email).first()
            if stu:
                prof["student_db_id"] = stu.id
                prof["gr_number"] = stu.gr_number
                prof["department"] = stu.department

        return prof

    def change_password(self, user_id: int, old_password: str, new_password: str):
        user = db_session.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            return False, "User not found"

        if not verify_password(old_password, user.password_hash):
            return False, "Current password incorrect"

        user.password_hash = hash_password(new_password)
        db_session.commit()
        logging_service.log_audit("PASSWORD_CHANGED", "user", user_id, "User changed password")
        return True, "Password updated successfully"

    def _save_refresh_token(self, user_id: int, token_str: str):
        try:
            expires_at = datetime.utcnow() + Config.REFRESH_TOKEN_EXPIRES
            rf = RefreshTokenModel(user_id=user_id, token=token_str, expires_at=expires_at)
            db_session.add(rf)
            db_session.commit()
        except Exception as e:
            db_session.rollback()

auth_service = AuthService()
