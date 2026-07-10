-- Exécuté automatiquement au premier démarrage du conteneur postgres.
-- Crée une base de données distincte par microservice, conformément
-- au principe "database per service" des architectures microservices.
CREATE DATABASE books_db;
CREATE DATABASE users_db;
CREATE DATABASE loans_db;

GRANT ALL PRIVILEGES ON DATABASE books_db TO admin;
GRANT ALL PRIVILEGES ON DATABASE users_db TO admin;
GRANT ALL PRIVILEGES ON DATABASE loans_db TO admin;
