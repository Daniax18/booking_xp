# 🚀 INSTALLATION GUIDE - Choisissez votre scenario

## SCENARIO 1️⃣: DÉMARRAGE RAPIDE (Dev local avec SQLite)
**Parfait pour:** Débuter, comprendre le code, tester l'API

```bash
# 1. Cloner/Naviguer
cd api/inventory-service

# 2. Créer l'environnement virtuel
python -m venv venv
venv\Scripts\activate

# 3. Installer les dépendances MINIMUM
pip install fastapi uvicorn sqlalchemy pydantic python-dotenv

# 4. Lancer
python main.py

# ✅ Accéder à: http://localhost:8002/docs
```

**Temps:** 5 minutes
**BD:** SQLite (auto-créée: inventory_service.db)
**Packages:** 5 (15 MB)

---

## SCENARIO 2️⃣: INSTALLATION COMPLÈTE (Dev + Tests)
**Parfait pour:** Développement sérieux, écrire des tests, formatter le code

```bash
# 1-2. Setup pareil que Scenario 1
cd api/inventory-service
python -m venv venv
venv\Scripts\activate

# 3. Installer TOUTES les dépendances (core + dev tools)
pip install -r requirements-dev.txt

# 4. Lancer
python main.py

# ✅ Accéder à: http://localhost:8002/docs

# 📊 Maintenant vous pouvez aussi:
pytest tests/                     # Lancer les tests
pytest --cov=application tests/  # Tests + coverage
black .                          # Formatter le code
flake8 .                         # Linter
mypy .                           # Type checking
```

**Temps:** 10 minutes
**BD:** SQLite par défaut
**Packages:** 20+ (150 MB)

---

## SCENARIO 3️⃣: PRODUCTION AVEC PostgreSQL
**Parfait pour:** Déployer en production, avec une vraie base de données

```bash
# A. INSTALLER PostgreSQL d'abord (choix 1 ou 2):

# Option A1: Manuel
# Windows: Télécharger https://www.postgresql.org/download/windows/
# macOS: brew install postgresql
# Linux: apt-get install postgresql postgresql-contrib

# Option A2: Docker (plus facile)
docker run --name inventory-postgres \
  -e POSTGRES_USER=inventory \
  -e POSTGRES_PASSWORD=securepassword \
  -e POSTGRES_DB=inventory_db \
  -p 5432:5432 \
  -d postgres:15

# B. INSTALLER les packages Python
cd api/inventory-service
python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt
pip install -r requirements-postgres.txt
pip install -r requirements-prod.txt

# C. CONFIGURER .env
# Créer un fichier .env avec:
cat > .env << EOF
ENVIRONMENT=production
DEBUG=False
DATABASE_URL=postgresql://inventory:securepassword@localhost:5432/inventory_db
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8002
CORS_ORIGINS=https://yourdomain.com
EOF

# D. LANCER EN PRODUCTION
gunicorn -w 4 -b 0.0.0.0:8002 main:app

# ✅ Accéder à: http://localhost:8002/docs
```

**Temps:** 20 minutes (plus PostgreSQL install)
**BD:** PostgreSQL (externe)
**Packages:** 25+ (200 MB)

---

## SCENARIO 4️⃣: FICHIER DE COMMANDES RAPIDES

Créer un fichier `Makefile` ou `setup.sh` pour automatiser:

### Windows: `setup.bat`
```batch
@echo off
echo Creating virtual environment...
python -m venv venv
call venv\Scripts\activate

echo Installing dependencies...
pip install -r requirements-dev.txt

echo Setup complete! Run: python main.py
```

### Linux/Mac: `setup.sh`
```bash
#!/bin/bash
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements-dev.txt

echo "Setup complete! Run: python main.py"
```

Utiliser:
```bash
./setup.sh      # Linux/Mac
setup.bat       # Windows
```

---

## 📦 RÉSUMÉ DES FICHIERS REQUIREMENTS

| Fichier | Contenu | Quand l'utiliser |
|---------|---------|-----------------|
| `requirements.txt` | Core + DB drivers | Production, toujours |
| `requirements-dev.txt` | Core + tests + linters | Développement local |
| `requirements-prod.txt` | Core + gunicorn + monitoring | Déploiement prod |
| `requirements-postgres.txt` | Driver PostgreSQL | Avec PostgreSQL |
| `requirements-mysql.txt` | Driver MySQL | Avec MySQL |

---

## 🔍 DÉPENDRE VERSUS SANS DÉPENDRE

### ✅ AVEC Dépendances externes (PostgreSQL)

**Avantages:**
- ✅ Vraie base de données
- ✅ Persist les données sur redémarrage
- ✅ Supporte la concurrence
- ✅ Prêt pour production

**Installation:**
1. Installer PostgreSQL
2. Configurer DATABASE_URL dans .env
3. `pip install psycopg2-binary`
4. Lancer l'app

**Commande:**
```bash
pip install -r requirements.txt requirements-postgres.txt
```

---

### ✅ SANS Dépendances externes (SQLite)

**Avantages:**
- ✅ Zéro config
- ✅ Installations rapide
- ✅ Fichier unique (inventory_service.db)
- ✅ Parfait pour dev

**Limitation:**
- ❌ Pas bon pour production
- ❌ Problèmes de concurrence
- ❌ Données perdues si fichier supprimé

**Commande:**
```bash
pip install fastapi uvicorn sqlalchemy pydantic python-dotenv
```

---

## 🎯 RECOMMANDATION FINALE

### Pour démarrer MAINTENANT:
```bash
pip install fastapi uvicorn sqlalchemy pydantic python-dotenv
```

### Pour développer sérieusement:
```bash
pip install -r requirements-dev.txt
```

### Pour production:
```bash
# PostgreSQL + Gunicorn
pip install -r requirements.txt -r requirements-postgres.txt -r requirements-prod.txt
```

---

## 🆘 DÉPANNAGE

### Erreur: "pip: command not found"
```bash
python -m pip install --upgrade pip
python -m pip install fastapi
```

### Erreur: "No module named fastapi"
```bash
python -m pip install -r requirements.txt
```

### Erreur: "psycopg2: cannot find static libc"
```bash
pip install --only-binary :all: psycopg2-binary
```

### Vérifier l'installation:
```bash
python -c "import fastapi, sqlalchemy, pydantic; print('✅ OK')"
```

---

✨ **Choisissez votre scenario et démarrez!** ✨
