from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class BookBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    author: str = Field(..., min_length=1, max_length=255)
    isbn: str = Field(..., min_length=5, max_length=20)
    year: Optional[int] = None
    quantity: int = Field(default=1, ge=0)


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    isbn: Optional[str] = None
    year: Optional[int] = None
    quantity: Optional[int] = None


class BookOut(BookBase):
    id: int
    available_quantity: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AvailabilityUpdate(BaseModel):
    delta: int  # +1 pour un retour, -1 pour un emprunt
