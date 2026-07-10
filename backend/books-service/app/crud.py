from sqlalchemy.orm import Session
from sqlalchemy import or_
from . import models, schemas


def get_book(db: Session, book_id: int):
    return db.query(models.Book).filter(models.Book.id == book_id).first()


def get_books(db: Session, skip: int = 0, limit: int = 100, search: str | None = None):
    query = db.query(models.Book)
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                models.Book.title.ilike(like),
                models.Book.author.ilike(like),
                models.Book.isbn.ilike(like),
            )
        )
    return query.offset(skip).limit(limit).all()


def create_book(db: Session, book: schemas.BookCreate):
    db_book = models.Book(
        title=book.title,
        author=book.author,
        isbn=book.isbn,
        year=book.year,
        quantity=book.quantity,
        available_quantity=book.quantity,
    )
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book


def update_book(db: Session, book_id: int, book: schemas.BookUpdate):
    db_book = get_book(db, book_id)
    if not db_book:
        return None
    data = book.dict(exclude_unset=True)
    if "quantity" in data:
        # ajuste la disponibilité proportionnellement au changement de quantité totale
        diff = data["quantity"] - db_book.quantity
        db_book.available_quantity = max(0, db_book.available_quantity + diff)
    for key, value in data.items():
        setattr(db_book, key, value)
    db.commit()
    db.refresh(db_book)
    return db_book


def delete_book(db: Session, book_id: int):
    db_book = get_book(db, book_id)
    if not db_book:
        return None
    db.delete(db_book)
    db.commit()
    return db_book


def adjust_availability(db: Session, book_id: int, delta: int):
    db_book = get_book(db, book_id)
    if not db_book:
        return None
    new_value = db_book.available_quantity + delta
    if new_value < 0 or new_value > db_book.quantity:
        return "invalid"
    db_book.available_quantity = new_value
    db.commit()
    db.refresh(db_book)
    return db_book
