from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from .models import LoanStatus


class LoanCreate(BaseModel):
    book_id: int
    user_id: int


class LoanOut(BaseModel):
    id: int
    book_id: int
    user_id: int
    borrow_date: datetime
    return_date: Optional[datetime]
    status: LoanStatus

    class Config:
        from_attributes = True
