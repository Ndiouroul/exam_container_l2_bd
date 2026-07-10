import enum
from sqlalchemy import Column, Integer, String, DateTime, Enum, func
from .database import Base


class UserType(str, enum.Enum):
    ETUDIANT = "ETUDIANT"
    PROFESSEUR = "PROFESSEUR"
    PERSONNEL_ADMINISTRATIF = "PERSONNEL_ADMINISTRATIF"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    user_type = Column(Enum(UserType), nullable=False, default=UserType.ETUDIANT)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
