import os
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me-in-production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))  # 8h

bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(subject: dict) -> str:
    to_encode = subject.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


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
    payload = decode_token(credentials.credentials)
    return payload


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Réservé au personnel administratif : création/suppression de comptes, annuaire complet."""
    if current_user.get("user_type") != "PERSONNEL_ADMINISTRATIF":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Action réservée au personnel administratif",
        )
    return current_user


def is_admin(current_user: dict) -> bool:
    return current_user.get("user_type") == "PERSONNEL_ADMINISTRATIF"


def check_self_or_admin(target_user_id: int, current_user: dict) -> None:
    """Autorise l'accès si l'utilisateur consulte/modifie son propre profil, ou s'il est
    membre du personnel administratif (qui peut gérer tous les comptes)."""
    if is_admin(current_user):
        return
    if str(current_user.get("sub")) != str(target_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous ne pouvez consulter ou modifier que votre propre profil",
        )
