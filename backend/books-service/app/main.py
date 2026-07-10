from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import models, schemas, crud
from .database import engine, get_db
from .auth import get_current_user, require_admin

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Books Service - Bibliothèque Numérique DIT",
    description="Microservice de gestion des livres",
    version="1.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "books-service"}


# ---------------------------------------------------------------------------
# Gestion du catalogue — réservée au personnel administratif
# ---------------------------------------------------------------------------

@app.post("/books", response_model=schemas.BookOut, status_code=201)
def create_book(book: schemas.BookCreate, db: Session = Depends(get_db), current_user: dict = Depends(require_admin)):
    existing = db.query(models.Book).filter(models.Book.isbn == book.isbn).first()
    if existing:
        raise HTTPException(status_code=400, detail="Un livre avec cet ISBN existe déjà")
    return crud.create_book(db, book)


@app.put("/books/{book_id}", response_model=schemas.BookOut)
def update_book(book_id: int, book: schemas.BookUpdate, db: Session = Depends(get_db), current_user: dict = Depends(require_admin)):
    db_book = crud.update_book(db, book_id, book)
    if not db_book:
        raise HTTPException(status_code=404, detail="Livre introuvable")
    return db_book


@app.delete("/books/{book_id}", status_code=204)
def delete_book(book_id: int, db: Session = Depends(get_db), current_user: dict = Depends(require_admin)):
    db_book = crud.delete_book(db, book_id)
    if not db_book:
        raise HTTPException(status_code=404, detail="Livre introuvable")
    return None


# ---------------------------------------------------------------------------
# Consultation du catalogue — ouverte à tout usager authentifié
# ---------------------------------------------------------------------------

@app.get("/books", response_model=list[schemas.BookOut])
def list_books(
    skip: int = 0,
    limit: int = 100,
    search: str | None = Query(default=None, description="Recherche par titre, auteur ou ISBN"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return crud.get_books(db, skip=skip, limit=limit, search=search)


@app.get("/books/{book_id}", response_model=schemas.BookOut)
def get_book(book_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    db_book = crud.get_book(db, book_id)
    if not db_book:
        raise HTTPException(status_code=404, detail="Livre introuvable")
    return db_book


@app.patch("/books/{book_id}/availability", response_model=schemas.BookOut)
def adjust_availability(book_id: int, payload: schemas.AvailabilityUpdate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """Utilisé en interne par loans-service lors d'un emprunt/retour (tout usager authentifié
    peut emprunter, donc cette route reste accessible à tout token valide, pas seulement admin)."""
    result = crud.adjust_availability(db, book_id, payload.delta)
    if result is None:
        raise HTTPException(status_code=404, detail="Livre introuvable")
    if result == "invalid":
        raise HTTPException(status_code=409, detail="Quantité disponible invalide (stock insuffisant)")
    return result
