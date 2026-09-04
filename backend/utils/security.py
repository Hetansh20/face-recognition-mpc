import jwt
import bcrypt
from datetime import datetime, timezone, timedelta
from backend.config import Config

def hash_password(password: str) -> str:
    if isinstance(password, str):
        password = password.encode('utf-8')
    return bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        if isinstance(plain_password, str):
            plain_password = plain_password.encode('utf-8')
        if isinstance(hashed_password, str):
            hashed_password = hashed_password.encode('utf-8')
        return bcrypt.checkpw(plain_password, hashed_password)
    except Exception:
        return False

def generate_access_token(user_id: int, role: str, email: str, extra: dict = None) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "email": email,
        "iat": now,
        "exp": now + Config.ACCESS_TOKEN_EXPIRES,
        "type": "access"
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm="HS256")

def generate_refresh_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + Config.REFRESH_TOKEN_EXPIRES,
        "type": "refresh"
    }
    return jwt.encode(payload, Config.JWT_REFRESH_SECRET_KEY, algorithm="HS256")

def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "access":
            return None
        if "sub" in payload and str(payload["sub"]).isdigit():
            payload["sub"] = int(payload["sub"])
        return payload
    except Exception as e:
        return None

def decode_refresh_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, Config.JWT_REFRESH_SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "refresh":
            return None
        if "sub" in payload and str(payload["sub"]).isdigit():
            payload["sub"] = int(payload["sub"])
        return payload
    except Exception as e:
        return None
