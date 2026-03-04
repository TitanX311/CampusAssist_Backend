from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from auth.config.settings import get_settings

settings = get_settings()


class TokenService:
    @staticmethod
    def create_access_token(user_id: str) -> tuple[str, int]:
        """Returns (access_token, expires_in_seconds)."""
        expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        expire = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access",
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return token, expires_in

    @staticmethod
    def verify_access_token(token: str) -> str | None:
        """Returns user_id if the token is valid, else None."""
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            if payload.get("type") != "access":
                return None
            return payload.get("sub")
        except JWTError:
            return None
