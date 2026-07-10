import os

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me-in-production")
JWT_ALGORITHM = "HS256"

bearer_scheme = HTTPBearer(auto_error=False)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session invalide ou expirée, veuillez vous reconnecter",
        )


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentification requise",
        )
    return decode_token(credentials.credentials)


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Réservé au personnel administratif : gestion du catalogue (ajout/suppression de livres)."""
    if current_user.get("user_type") != "PERSONNEL_ADMINISTRATIF":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Action réservée au personnel administratif",
        )
    return current_user
