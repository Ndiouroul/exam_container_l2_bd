from datetime import datetime, timezone
from sqlalchemy.orm import Session
from . import models


def create_loan(db: Session, book_id: int, user_id: int):
    db_loan = models.Loan(book_id=book_id, user_id=user_id, status=models.LoanStatus.EN_COURS)
    db.add(db_loan)
    db.commit()
    db.refresh(db_loan)
    return db_loan


def get_loan(db: Session, loan_id: int):
    return db.query(models.Loan).filter(models.Loan.id == loan_id).first()


def get_active_loan(db: Session, book_id: int, user_id: int):
    return (
        db.query(models.Loan)
        .filter(
            models.Loan.book_id == book_id,
            models.Loan.user_id == user_id,
            models.Loan.status == models.LoanStatus.EN_COURS,
        )
        .first()
    )


def return_loan(db: Session, loan_id: int):
    db_loan = get_loan(db, loan_id)
    if not db_loan or db_loan.status == models.LoanStatus.RETOURNE:
        return None
    db_loan.status = models.LoanStatus.RETOURNE
    db_loan.return_date = datetime.now(timezone.utc)
    db.commit()
    db.refresh(db_loan)
    return db_loan


def get_history(db: Session, user_id: int | None = None, book_id: int | None = None, skip: int = 0, limit: int = 100):
    query = db.query(models.Loan)
    if user_id is not None:
        query = query.filter(models.Loan.user_id == user_id)
    if book_id is not None:
        query = query.filter(models.Loan.book_id == book_id)
    return query.order_by(models.Loan.borrow_date.desc()).offset(skip).limit(limit).all()
