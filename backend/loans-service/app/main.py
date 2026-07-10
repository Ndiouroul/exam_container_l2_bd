from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import models, schemas, crud, clients
from .database import engine, get_db
from .auth import get_current_user, get_raw_token, is_admin, check_self_or_admin

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Loans Service - Bibliothèque Numérique DIT",
    description="Microservice de gestion des emprunts (communique avec books-service et users-service)",
    version="1.1.0",
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
    return {"status": "ok", "service": "loans-service"}


@app.post("/loans", response_model=schemas.LoanOut, status_code=201)
def borrow_book(
    payload: schemas.LoanCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    token: str = Depends(get_raw_token),
):
    # Un étudiant ou un professeur ne peut emprunter que pour lui-même ; le personnel
    # administratif peut enregistrer un emprunt au nom de n'importe quel usager (guichet).
    check_self_or_admin(payload.user_id, current_user, "Vous ne pouvez emprunter un livre que pour vous-même")

    # 1. Vérifier que l'utilisateur et le livre existent (appels HTTP vers les autres services)
    try:
        user = clients.get_user(payload.user_id, token)
        book = clients.get_book(payload.book_id, token)
    except clients.ServiceUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    if user is None:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable (users-service)")
    if book is None:
        raise HTTPException(status_code=404, detail="Livre introuvable (books-service)")
    if book["available_quantity"] <= 0:
        raise HTTPException(status_code=409, detail="Aucun exemplaire disponible pour ce livre")

    # 2. Empêcher un double emprunt du même livre par le même utilisateur
    if crud.get_active_loan(db, payload.book_id, payload.user_id):
        raise HTTPException(status_code=409, detail="Cet utilisateur a déjà emprunté ce livre")

    # 3. Décrémenter la disponibilité côté books-service
    result = clients.adjust_book_availability(payload.book_id, delta=-1, token=token)
    if result["status_code"] >= 400:
        raise HTTPException(status_code=409, detail="Impossible de réserver un exemplaire du livre")

    # 4. Créer l'enregistrement d'emprunt
    return crud.create_loan(db, book_id=payload.book_id, user_id=payload.user_id)


@app.post("/loans/{loan_id}/return", response_model=schemas.LoanOut)
def return_book(
    loan_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    token: str = Depends(get_raw_token),
):
    db_loan = crud.get_loan(db, loan_id)
    if not db_loan:
        raise HTTPException(status_code=404, detail="Emprunt introuvable")
    check_self_or_admin(db_loan.user_id, current_user, "Vous ne pouvez retourner que vos propres emprunts")
    if db_loan.status == models.LoanStatus.RETOURNE:
        raise HTTPException(status_code=409, detail="Ce livre a déjà été retourné")

    # Ré-incrémenter la disponibilité côté books-service
    try:
        result = clients.adjust_book_availability(db_loan.book_id, delta=1, token=token)
    except clients.ServiceUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    if result["status_code"] >= 400:
        raise HTTPException(status_code=502, detail="Erreur lors de la mise à jour de la disponibilité")

    return crud.return_loan(db, loan_id)


@app.get("/loans/history", response_model=list[schemas.LoanOut])
def loan_history(
    user_id: int | None = None,
    book_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    # Un étudiant ou un professeur ne voit que son propre historique ; le personnel
    # administratif peut consulter l'historique de n'importe quel usager, ou tout l'historique.
    if not is_admin(current_user):
        user_id = int(current_user["sub"])
    return crud.get_history(db, user_id=user_id, book_id=book_id, skip=skip, limit=limit)


@app.get("/loans/{loan_id}", response_model=schemas.LoanOut)
def get_loan(loan_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    db_loan = crud.get_loan(db, loan_id)
    if not db_loan:
        raise HTTPException(status_code=404, detail="Emprunt introuvable")
    check_self_or_admin(db_loan.user_id, current_user, "Vous ne pouvez consulter que vos propres emprunts")
    return db_loan
