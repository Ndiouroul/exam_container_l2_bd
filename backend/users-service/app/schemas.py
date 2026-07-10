from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from .models import UserType


class UserBase(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    user_type: UserType = UserType.ETUDIANT


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=128)


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    user_type: Optional[UserType] = None


class SelfRegisterRequest(BaseModel):
    """Inscription publique (étudiant/professeur) : pas de champ de rôle, car les deux
    profils disposent des mêmes privilèges dans l'application. Un compte créé par
    auto-inscription est toujours de type ETUDIANT par défaut ; seul le personnel
    administratif peut créer directement un compte PROFESSEUR ou PERSONNEL_ADMINISTRATIF
    via POST /users."""
    full_name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)


class UserOut(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
