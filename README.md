# Bibliothèque Numérique DIT — Plateforme Microservices

Projet réalisé dans le cadre de l'**Examen Pratique Containers et Virtualisation — L2 DIT**.
Plateforme de gestion de bibliothèque académique basée sur une architecture microservices,
conteneurisée avec Docker et déployée automatiquement via un pipeline CI/CD Jenkins.

## 1. Architecture du système

```
                         ┌───────────────────┐
                         │     Frontend       │
                         │  React + Nginx     │
                         │   (port 3000)      │
                         └─────────┬──────────┘
                                   │ REST/HTTP (JSON)
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
┌───────▼────────┐       ┌─────────▼────────┐       ┌─────────▼────────┐
│  books-service  │       │  users-service    │       │  loans-service    │
│  FastAPI        │       │  FastAPI          │◄──────┤  FastAPI          │
│  port 8001      │◄──────┼───────────────────┼───────┤  port 8003        │
└───────┬─────────┘       └─────────┬─────────┘       └─────────┬─────────┘
        │                           │                           │
        │        appels HTTP inter-services (httpx)             │
        │                                                        │
┌───────▼──────────────────────────▼────────────────────────────▼────────┐
│                          PostgreSQL (1 instance)                        │
│         books_db          |         users_db        |     loans_db     │
└───────────────────────────────────────────────────────────────────────┘
```

**Principe "database per service"** : chaque microservice possède sa propre base de
données logique (`books_db`, `users_db`, `loans_db`) sur une instance PostgreSQL
partagée, ce qui garantit l'indépendance des schémas tout en simplifiant l'exploitation
pour un contexte pédagogique. Aucun service n'accède directement à la base d'un autre :
toute communication passe par les API REST.

### Authentification et rôles

L'accès à l'application est protégé par authentification **JWT** (JSON Web Token), avec un
contrôle d'accès par rôle (RBAC) fidèle au fonctionnement d'une vraie bibliothèque
universitaire. Étudiants et professeurs disposent exactement des **mêmes privilèges**
(tous deux sont de simples usagers de la bibliothèque) ; seul le **personnel
administratif** dispose de privilèges élevés (gestion du catalogue et des comptes),
un rôle qui ne peut jamais être obtenu par auto-inscription.

- `users-service` émet les tokens (`POST /auth/login`) et gère le hachage des mots de passe (bcrypt).
- **`POST /auth/register`** permet à tout étudiant ou professeur de créer lui-même son
  compte — **sans champ de rôle** dans le formulaire, puisque les deux profils ont les
  mêmes privilèges : un compte auto-inscrit est toujours créé avec le type `ETUDIANT`
  côté serveur, quelle que soit la valeur envoyée par le client (le schéma d'entrée de
  cette route n'accepte tout simplement pas de champ `user_type`, ce qui rend impossible
  toute tentative d'auto-promotion en personnel administratif).
- Un compte **PERSONNEL_ADMINISTRATIF** (rôle à privilèges élevés, sorte de
  super-utilisateur pouvant tout faire : gérer le catalogue, créer/supprimer des comptes
  de n'importe quel type) ne peut être créé que par un membre du personnel administratif
  déjà existant, via `POST /users`.
- Au premier démarrage, `users-service` crée automatiquement un **compte administrateur
  de démarrage** (bootstrap, super-utilisateur initial) s'il n'existe encore aucun compte
  PERSONNEL_ADMINISTRATIF, avec les identifiants définis par les variables d'environnement
  `ADMIN_EMAIL` / `ADMIN_PASSWORD` (par défaut `admin@dit-library.sn` / `passwrd123`, à
  changer en production). C'est ce compte qui permet ensuite de créer tous les autres
  comptes administratifs.
- Les 3 microservices partagent le **même secret** (`JWT_SECRET`) et vérifient chacun
  indépendamment la validité du token reçu dans l'en-tête `Authorization: Bearer <token>`
  (JWT stateless, sans appel réseau supplémentaire).
- `loans-service` relaie le token reçu du frontend lors de ses appels internes vers
  `books-service` et `users-service`, afin que ces appels soient eux aussi authentifiés.
- Côté frontend, toute tentative d'accès à une page sans session valide redirige
  automatiquement vers l'écran de connexion (`/login`), qui propose un bouton
  **« S'inscrire »** pour basculer vers le formulaire d'auto-inscription.

**Matrice des permissions :**

| Action | Étudiant / Professeur | Personnel administratif |
|---|---|---|
| Créer son propre compte (auto-inscription) | ✅ | ❌ *(créé uniquement par un autre administratif)* |
| Rechercher / consulter le catalogue | ✅ | ✅ |
| Emprunter un livre | ✅ *(pour soi-même uniquement)* | ✅ *(pour soi ou pour un usager, prêt au guichet)* |
| Retourner un livre | ✅ *(ses propres emprunts)* | ✅ *(tout emprunt)* |
| Consulter l'historique des emprunts | ✅ *(le sien uniquement)* | ✅ *(tous les usagers)* |
| Ajouter / modifier / supprimer un livre | ❌ | ✅ |
| Créer / supprimer un compte utilisateur (tout type, y compris administratif) | ❌ | ✅ |
| Lister l'annuaire complet des usagers | ❌ | ✅ |
| Consulter / modifier son propre profil | ✅ | ✅ |

Ces règles sont appliquées **côté backend** (chaque microservice vérifie le rôle contenu
dans le JWT avant d'exécuter l'action, indépendamment de ce que montre l'interface) et
**côté frontend** (les formulaires et boutons d'administration ne s'affichent que pour le
personnel administratif, et la page `/utilisateurs` est inaccessible aux autres rôles).

## 2. Description des microservices

### 2.1 `books-service` (port 8001)
Gère le catalogue des livres. *Toutes les routes nécessitent un token JWT.*
- `GET /books?search=...` — lister / rechercher par titre, auteur ou ISBN *(tout usager)*
- `GET /books/{id}` — détail d'un livre *(tout usager)*
- `POST /books` — ajouter un livre *(personnel administratif uniquement)*
- `PUT /books/{id}` — modifier un livre *(personnel administratif uniquement)*
- `DELETE /books/{id}` — supprimer un livre *(personnel administratif uniquement)*
- `PATCH /books/{id}/availability` — ajuster la disponibilité (utilisé en interne par `loans-service`)

### 2.2 `users-service` (port 8002)
Gère les comptes de la bibliothèque (étudiants, professeurs, personnel administratif)
ainsi que l'authentification.
- `POST /auth/register` — auto-inscription étudiant/professeur, sans champ de rôle *(public)*
- `POST /auth/login` — connexion, retourne un token JWT *(public)*
- `GET /auth/me` — profil de l'utilisateur connecté *(tout usager authentifié)*
- `POST /users` — créer un compte de n'importe quel type, y compris administratif *(personnel administratif uniquement)*
- `GET /users` — lister l'annuaire complet *(personnel administratif uniquement)*
- `GET /users/{id}` — consulter un profil *(le titulaire du compte, ou le personnel administratif)*
- `PUT /users/{id}` — modifier un profil *(le titulaire, ou le personnel administratif ; seul
  le personnel administratif peut changer le type de compte d'un usager)*
- `DELETE /users/{id}` — supprimer un compte *(personnel administratif uniquement)*

### 2.3 `loans-service` (port 8003)
Gère les emprunts. *Toutes les routes nécessitent un token JWT.* C'est le service qui
illustre le mieux la communication inter-microservices : avant de créer un emprunt,
il interroge `users-service` (l'utilisateur existe-t-il ?) et `books-service` (le livre
est-il disponible ?), en relayant le token JWT du client, puis décrémente la disponibilité
via un appel HTTP `PATCH` vers `books-service`.
- `POST /loans` — emprunter un livre (`book_id`, `user_id`) — un étudiant/professeur ne
  peut emprunter que pour lui-même ; le personnel administratif peut emprunter au nom de
  n'importe quel usager (prêt au guichet)
- `POST /loans/{id}/return` — retourner un livre *(le titulaire de l'emprunt, ou le personnel administratif)*
- `GET /loans/history` — historique des emprunts — un étudiant/professeur ne voit que le
  sien ; le personnel administratif voit celui de tous les usagers
- `GET /loans/{id}` — détail d'un emprunt *(le titulaire, ou le personnel administratif)*

Chaque service expose `GET /health` pour les health checks Docker/Jenkins, ainsi
qu'une documentation interactive Swagger auto-générée sur `/docs`.

### 2.4 `frontend`
Application React (Vite) servie par Nginx en production. Trois écrans : Livres,
Utilisateurs (réservé au personnel administratif), Emprunts, chacun consommant
directement le microservice concerné et adaptant son affichage au rôle de l'usager connecté.

## 3. Conteneurisation

Chaque composant possède son propre `Dockerfile` :
- `backend/books-service/Dockerfile` — image Python 3.11-slim
- `backend/users-service/Dockerfile` — image Python 3.11-slim
- `backend/loans-service/Dockerfile` — image Python 3.11-slim
- `frontend/Dockerfile` — build multi-stage Node 20 → Nginx alpine

Le fichier `docker-compose.yml` orchestre l'ensemble : PostgreSQL, les 3
microservices backend et le frontend, avec un réseau Docker dédié (`dit-network`),
des `healthcheck` et un volume persistant pour la base de données.

## 4. Installation et lancement

### Prérequis
- Docker ≥ 24
- Docker Compose v2 (`docker compose`)

### Étapes

```bash
# 1. Cloner le dépôt
git clone <URL_DU_DEPOT>
cd dit-library

# 2. Construire et lancer l'ensemble de la plateforme
docker compose up -d --build

# 3. Vérifier l'état des conteneurs
docker compose ps
```

### Accès aux services

| Composant        | URL                              |
|-------------------|-----------------------------------|
| Frontend           | http://localhost:3000            |
| books-service (Swagger) | http://localhost:8001/docs  |
| users-service (Swagger) | http://localhost:8002/docs  |
| loans-service (Swagger) | http://localhost:8003/docs  |
| PostgreSQL          | localhost:5432 (admin / passwrd123) |

> ⚠️ **Note de sécurité** : `admin` / `passwrd123` (PostgreSQL), le compte administrateur de
> démarrage (`admin@dit-library.sn` / `passwrd123`) et le `JWT_SECRET` par défaut
> (`dev-secret-change-me-in-production`) sont des valeurs **de développement/démonstration**
> uniquement. Pour un déploiement en production, il faut impérativement les remplacer — par
> exemple via les variables d'environnement `ADMIN_EMAIL`, `ADMIN_PASSWORD` et `JWT_SECRET`
> avant `docker compose up` (`export JWT_SECRET=$(openssl rand -hex 32)`) — et ne jamais les
> committer en clair dans un dépôt public. **Le mot de passe du compte administrateur de
> démarrage doit être changé dès la première connexion.**

### Tester l'authentification et les rôles en ligne de commande

```bash
# Connexion avec le compte administrateur de démarrage (super-utilisateur initial)
curl -X POST http://localhost:8002/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@dit-library.sn","password":"passwrd123"}'
# -> renvoie un access_token, à réutiliser dans les appels suivants

# Auto-inscription publique d'un étudiant ou professeur (aucun champ de rôle : le compte
# créé est toujours de type ETUDIANT)
curl -X POST http://localhost:8002/auth/register \
  -H "Content-Type: application/json" \
  -d '{"full_name":"Osemes Diop","email":"osemes@dit.sn","password":"motdepasse123"}'

# L'administrateur crée directement un compte PERSONNEL_ADMINISTRATIF supplémentaire
curl -X POST http://localhost:8002/users \
  -H "Content-Type: application/json" -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -d '{"full_name":"Fatou Sarr","email":"fatou@dit.sn","user_type":"PERSONNEL_ADMINISTRATIF","password":"motdepasse123"}'

# L'administrateur ajoute un livre au catalogue
curl -X POST http://localhost:8001/books \
  -H "Content-Type: application/json" -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -d '{"title":"Clean Code","author":"Robert C. Martin","isbn":"9780132350884","year":2008,"quantity":3}'

# L'étudiant se connecte
curl -X POST http://localhost:8002/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"osemes@dit.sn","password":"motdepasse123"}'

# L'étudiant tente d'ajouter un livre -> 403 Forbidden (réservé au personnel administratif)
curl -i -X POST http://localhost:8001/books \
  -H "Content-Type: application/json" -H "Authorization: Bearer <STUDENT_TOKEN>" \
  -d '{"title":"Test","author":"Test","isbn":"0000000000","year":2020,"quantity":1}'

# Sans token -> 401 Unauthorized
curl -i http://localhost:8001/books
```

### Commandes utiles

```bash
# Lancer uniquement un service précis (ex. reconstruire seulement le frontend)
docker compose up -d --build frontend

# Suivre les logs d'un service en temps réel
docker compose logs -f books-service
docker compose logs -f users-service
docker compose logs -f loans-service
docker compose logs -f frontend

# Redémarrer un service sans le reconstruire
docker compose restart loans-service

# Ouvrir un shell PostgreSQL dans le conteneur
docker exec -it dit-postgres psql -U admin -d books_db

# Reconstruire une seule image sans cache
docker compose build --no-cache users-service

# Voir l'état de santé de tous les conteneurs
docker compose ps
```

### Arrêt de la plateforme

```bash
docker compose down          # arrête les conteneurs
docker compose down -v       # arrête et supprime aussi le volume PostgreSQL
```

## 5. Fonctionnement du pipeline Jenkins

Le fichier `Jenkinsfile` (à la racine) définit un pipeline déclaratif en 6 étapes :

1. **Checkout** — récupération du code source depuis GitHub.
2. **Lint & Vérifications** (parallèle) — compilation syntaxique des modules Python
   de chaque microservice, et build du frontend (`npm install` + `npm run build`).
3. **Build des images Docker** — `docker compose build --parallel`.
4. **Tests des microservices** — démarrage de PostgreSQL et des 3 backends,
   puis appel de `/health` sur chacun pour valider leur démarrage.
5. **Déploiement** — `docker compose up -d` pour déployer l'ensemble de la stack.
6. **Vérification post-déploiement** — contrôle que le frontend répond bien sur le port 3000.

En cas d'échec, le bloc `post { failure { ... } }` nettoie automatiquement les
conteneurs (`docker compose down`). Le bloc `always` exécute un `docker system prune`
pour limiter l'accumulation d'images intermédiaires sur l'agent Jenkins.

### Configuration du job Jenkins
1. Créer un item de type **Pipeline** dans Jenkins.
2. Dans "Pipeline", choisir **Pipeline script from SCM** → Git → renseigner
   l'URL du dépôt GitHub et la branche (`main`).
3. Spécifier `Jenkinsfile` comme "Script Path".
4. S'assurer que l'agent Jenkins dispose de Docker, Docker Compose, Python 3 et Node.js.

## 6. Structure du projet

```
dit-library/
├── Jenkinsfile
├── docker-compose.yml
├── postgres/
│   └── init-multiple-dbs.sql
├── backend/
│   ├── books-service/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── crud.py
│   │   │   ├── auth.py        (vérification du token JWT)
│   │   │   └── database.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── users-service/        (même structure + auth.py émet les tokens JWT, hash bcrypt)
│   └── loans-service/        (structure + clients.py pour les appels inter-services)
├── frontend/
│   ├── src/
│   │   ├── pages/ (BooksPage, UsersPage, LoansPage, LoginPage)
│   │   ├── components/ProtectedRoute.jsx
│   │   ├── api/client.js, api/auth.jsx
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
└── README.md
```

## 7. Choix techniques et justifications

- **FastAPI** pour les 3 microservices : typage fort via Pydantic, documentation
  Swagger automatique, performances élevées, cohérent avec l'écosystème Python déjà
  utilisé dans les autres projets académiques.
- **PostgreSQL** plutôt que MySQL : meilleur support des types avancés (enum natif)
  et large adoption en production.
- **httpx** pour les appels HTTP synchrones inter-services dans `loans-service`,
  illustrant explicitement le couplage faible entre microservices via REST plutôt
  que par accès direct aux bases de données.
- **React + Vite + Nginx** pour le frontend : build statique léger, servi en
  production par un conteneur Nginx séparé du serveur de développement.
- **Un seul PostgreSQL avec 3 bases logiques** plutôt que 3 instances PostgreSQL
  séparées : compromis pédagogique raisonnable qui conserve l'isolation des schémas
  tout en limitant la consommation de ressources sur la machine de build.

## Auteur
Osemes — Licence 2 Big Data / Informatique, Dakar Institute of Technology (DIT).
