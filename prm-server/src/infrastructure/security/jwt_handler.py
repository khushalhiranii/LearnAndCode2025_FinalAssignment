from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from src.config import settings
from src.domain.exceptions import AuthorizationError


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


def create_access_token(user_id: int, role_name: str) -> str:
    expire = _utcnow() + timedelta(minutes=settings.jwt_access_token_ttl_minutes)
    payload = {
        "sub": str(user_id),
        "role": role_name,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_temp_token(user_id: int) -> str:
    """Short-lived token valid ONLY for the change-password endpoint."""
    expire = _utcnow() + timedelta(minutes=5)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "temp_password_change",
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:  # type: ignore[type-arg]
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        if payload.get("type") != "access":
            raise AuthorizationError("Invalid token type.")
        return payload
    except JWTError as exc:
        raise AuthorizationError("Token is invalid or expired.") from exc


def decode_temp_token(token: str) -> int:
    """Returns user_id. Raises AuthorizationError if token is not a valid temp token."""
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        if payload.get("type") != "temp_password_change":
            raise AuthorizationError("Invalid token type for password change.")
        return int(payload["sub"])
    except JWTError as exc:
        raise AuthorizationError("Token is invalid or expired.") from exc
