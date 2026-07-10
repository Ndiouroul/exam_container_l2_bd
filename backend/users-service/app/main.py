import os

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import models, schemas, crud
from .database import engine, get_db, SessionLocal
from .auth import verify_password, create_access_token, get_current_user, require_admin, check_self_or_admin

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Users Service - Bibliothèque Numérique DIT",
    description="Microservice de gestion des utilisateurs et de l'authentification",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def bootstrap_admin_account():
    """Le personnel administratif (rôle à privilèges élevés : gestion du catalogue et des
    comptes) ne peut pas être auto-créé par inscription publique — il faut donc qu'un premier
    compte administrateur ("super-utilisateur") existe dès le démarrage pour pouvoir en créer
    d'autres. On le crée automatiquement s'il n'existe encore aucun compte
    PERSONNEL_ADMINISTRATIF. Les comptes étudiant/professeur, eux, peuvent être créés soit par
    auto-inscription publique (POST /auth/register), soit par ce super-utilisateur."""
    db = SessionLocal()
    try:
        existing_admin = (
            db.query(models.User)
            .filter(models.User.user_type == models.UserType.PERSONNEL_ADMINISTRATIF)
            .first()
        )
        if existing_admin:
            return
        admin_email = os.getenv("ADMIN_EMAIL", "admin@dit-library.sn")
        admin_password = os.getenv("ADMIN_PASSWORD", "passwrd123")
        admin_name = os.getenv("ADMIN_FULL_NAME", "Personnel Administratif DIT")
        crud.create_user(db, schemas.UserCreate(
            full_name=admin_name,
            email=admin_email,
            user_type=models.UserType.PERSONNEL_ADMINISTRATIF,
            password=admin_password,
        ))
        print(f"[bootstrap] Compte administrateur créé : {admin_email}")
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok", "service": "users-service"}


# ---------------------------------------------------------------------------
# Authentification
# ---------------------------------------------------------------------------

@app.post("/auth/register", response_model=schemas.UserOut, status_code=201)
def register(payload: schemas.SelfRegisterRequest, db: Session = Depends(get_db)):
    """Inscription publique (aucune authentification requise).

    Volontairement sans champ de rôle : un étudiant et un professeur disposent des mêmes
    privilèges dans l'application, donc tout compte auto-créé ici est de type ETUDIANT par
    défaut. Un compte PROFESSEUR (à titre indicatif) ou PERSONNEL_ADMINISTRATIF (avec des
    privilèges élevés) ne peut être créé que par un membre du personnel administratif déjà
    existant, via POST /users."""
    if crud.get_user_by_email(db, payload.email):
        raise HTTPException(status_code=400, detail="Un utilisateur avec cet email existe déjà")
    user_create = schemas.UserCreate(
        full_name=payload.full_name,
        email=payload.email,
        user_type=models.UserType.ETUDIANT,
        password=payload.password,
    )
    return crud.create_user(db, user_create)


@app.post("/auth/login", response_model=schemas.TokenResponse)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    """Connexion : retourne un token JWT valable sur les 3 microservices."""
    db_user = crud.get_user_by_email(db, payload.email)
    if not db_user or not verify_password(payload.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")

    token = create_access_token({
        "sub": str(db_user.id),
        "email": db_user.email,
        "full_name": db_user.full_name,
        "user_type": db_user.user_type.value,
    })
    return schemas.TokenResponse(access_token=token, user=db_user)


@app.get("/auth/me", response_model=schemas.UserOut)
def me(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    db_user = crud.get_user(db, int(current_user["sub"]))
    if not db_user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return db_user


# ---------------------------------------------------------------------------
# Gestion des comptes — création, liste et suppression réservées au personnel
# administratif ; consultation et modification d'un profil ouvertes au
# titulaire du compte ou à un administrateur.
# ---------------------------------------------------------------------------

@app.post("/users", response_model=schemas.UserOut, status_code=201)
def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    if crud.get_user_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="Un utilisateur avec cet email existe déjà")
    return crud.create_user(db, user)


@app.get("/users", response_model=list[schemas.UserOut])
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    return crud.get_users(db, skip=skip, limit=limit)


@app.get("/users/{user_id}", response_model=schemas.UserOut)
def get_user(user_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    check_self_or_admin(user_id, current_user)
    db_user = crud.get_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return db_user


@app.put("/users/{user_id}", response_model=schemas.UserOut)
def update_user(
    user_id: int,
    user: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    check_self_or_admin(user_id, current_user)
    # Seul le personnel administratif peut changer le type d'un utilisateur (rôle/privilèges)
    if user.user_type is not None and current_user.get("user_type") != "PERSONNEL_ADMINISTRATIF":
        raise HTTPException(status_code=403, detail="Seul le personnel administratif peut modifier le type de compte")
    db_user = crud.update_user(db, user_id, user)
    if not db_user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return db_user


@app.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: dict = Depends(require_admin)):
    db_user = crud.delete_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return None
