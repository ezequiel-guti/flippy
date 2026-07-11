import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from pydantic import BaseModel

from app.core.config import settings

_bearer = HTTPBearer()

_jwks_client: PyJWKClient | None = None


def _get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        _jwks_client = PyJWKClient(f"{settings.supabase_url}/auth/v1/.well-known/jwks.json")
    return _jwks_client


class TokenData(BaseModel):
    user_id: str
    email: str

    @property
    def is_admin(self) -> bool:
        return self.email.lower() in settings.admin_email_list


def decode_access_token(token: str) -> dict:
    """Validate a Supabase Auth access token against the project's public JWKS.

    Supabase signs tokens with an asymmetric key (ES256) rotated automatically;
    verifying against JWKS avoids depending on a shared secret."""
    try:
        signing_key = _get_jwks_client().get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256", "RS256"],
            audience="authenticated",
            leeway=10,
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido o expirado",
        ) from exc


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> TokenData:
    payload = decode_access_token(credentials.credentials)
    return TokenData(user_id=payload["sub"], email=payload["email"])


def require_admin(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Se requiere rol administrador")
    return current_user
