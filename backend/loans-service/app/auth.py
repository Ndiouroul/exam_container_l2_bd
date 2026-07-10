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


def get_raw_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> str:
    """Retourne le token brut, utilisé par loans-service pour le relayer vers
    books-service et users-service lors des appels inter-services."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentification requise",
        )
    return credentials.credentials


def is_admin(current_user: dict) -> bool:
    return current_user.get("user_type") == "PERSONNEL_ADMINISTRATIF"


def check_self_or_admin(target_user_id: int, current_user: dict, message: str) -> None:
    """Un étudiant ou un professeur ne peut agir que sur ses propres emprunts ; le
    personnel administratif peut agir au nom de n'importe quel usager (prêt au guichet)."""
    if is_admin(current_user):
        return
    if str(current_user.get("sub")) != str(target_user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message)
