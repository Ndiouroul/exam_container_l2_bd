import enum
from sqlalchemy import Column, Integer, DateTime, Enum, func
from .database import Base


class LoanStatus(str, enum.Enum):
    EN_COURS = "EN_COURS"
    RETOURNE = "RETOURNE"


class Loan(Base):
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    borrow_date = Column(DateTime(timezone=True), server_default=func.now())
    return_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(LoanStatus), nullable=False, default=LoanStatus.EN_COURS)
