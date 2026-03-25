# 📦 ANALYSE COMPLÈTE DES DÉPENDANCES

## 🎯 Résumé rapide

Les **5 dépendances minimales** pour démarrer:
```bash
pip install fastapi uvicorn sqlalchemy pydantic python-dotenv
```

Avec **le driver de base de données** (choisir 1):
```bash
# SQLite (défaut, inclus avec Python)
# Aucune dépendance supplémentaire

# PostgreSQL (recommandé pour production)
pip install psycopg2-binary

# MySQL
pip install mysql-connector-python
```

---

## 📋 DÉPENDANCES DÉTAILLÉES

### ✅ CORE (Obligatoires)

| Package | Version | Pourquoi | Utilisé dans |
|---------|---------|---------|-------------|
| **fastapi** | 0.104.1 | Framework API REST moderne | main.py, tous les endpoints |
| **uvicorn** | 0.24.0 | Serveur ASGI pour FastAPI | Lancer le service (`python main.py`) |
| **sqlalchemy** | 2.0.23 | ORM pour la base de données | infrastructure/databases/ |
| **pydantic** | 2.5.0 | Validation des données (DTOs) | application/dtos.py |
| **python-dotenv** | 1.0.0 | Charger variables d'environnement | config.py, .env |

**Taille totale**: ~15 MB

---

### 🔄 MIGRATIONS (Recommandé)

| Package | Version | Pourquoi | Utilisé dans |
|---------|---------|---------|-------------|
| **alembic** | 1.13.1 | Gestion des migrations de BD | Futur: gestion du schéma BD |
| **pydantic-settings** | 2.1.0 | Config avancée avec validation | config.py |

**Installation:**
```bash
pip install alembic pydantic-settings
```

---

### 🗄️ DATABASE DRIVERS (Selon votre BD)

#### **Option 1: SQLite (Default - Zéro config)**
✅ Inclus avec Python - Parfait pour développement
- Aucune installation supplémentaire
- Fichier unique `inventory_service.db`

```python
DATABASE_URL = "sqlite:///./inventory_service.db"
```

#### **Option 2: PostgreSQL (⭐ Recommandé production)**
Meilleur choix pour scalabilité et performance
```bash
pip install psycopg2-binary==2.9.9
```

Configuration:
```python
DATABASE_URL = "postgresql://user:password@localhost:5432/inventory_db"
```

#### **Option 3: MySQL**
Alternative populaire
```bash
pip install mysql-connector-python==8.2.0
```

Configuration:
```python
DATABASE_URL = "mysql+pymysql://user:password@localhost:3306/inventory_db"
```

---

### 📊 LOGGING & MONITORING

| Package | Version | Pourquoi | Optionnel |
|---------|---------|---------|----------|
| **python-json-logger** | 2.0.7 | Logs structurés JSON | Oui |
| **requests** | 2.31.0 | HTTP client (appeler autres services) | Oui |

**Installation:**
```bash
pip install python-json-logger requests
```

---

### 🚀 PRODUCTION ONLY

Ces packages sont pour **déploiement en production**:

| Package | Quand l'utiliser |
|---------|-----------------|
| **gunicorn** | Remplace uvicorn pour la production (plus robuste, multi-worker) |
| **prometheus-client** | Métriques pour monitoring |

```bash
# Installation
pip install gunicorn prometheus-client

# Lancer en production
gunicorn -w 4 -b 0.0.0.0:8002 main:app
```

---

### 🧪 DÉVELOPPEMENT ONLY

Ces packages sont utiles pour le **développement et les tests**:

| Package | Utilisé pour |
|---------|-------------|
| **pytest** | Tests unitaires |
| **pytest-cov** | Coverage (% de code testé) |
| **pytest-asyncio** | Tests async |
| **black** | Auto-formatter le code |
| **flake8** | Linter (détecter les erreurs) |
| **mypy** | Type checker |
| **isort** | Tri automatique des imports |
| **httpx** | HTTP client async pour tests |

**Installation (dev uniquement):**
```bash
pip install pytest pytest-cov pytest-asyncio black flake8 mypy isort httpx
```

---

## 🛠️ CONFIGURATIONS RECOMMANDÉES

### 📌 Pour DÉMARRAGE (Développement)
```bash
pip install -r requirements.txt
```

### 📌 Pour PRODUCTION
```bash
# Installer core + database driver + monitoring
pip install fastapi uvicorn[standard] sqlalchemy pydantic python-dotenv
pip install psycopg2-binary           # Si vous utilisez PostgreSQL
pip install gunicorn prometheus-client
pip install python-json-logger requests
```

### 📌 Pour DÉVELOPPEMENT (avec tests)
```bash
# Installer tout
pip install fastapi uvicorn[standard] sqlalchemy pydantic python-dotenv
pip install alembic pydantic-settings
pip install pytest pytest-cov pytest-asyncio
pip install black flake8 mypy isort httpx
pip install python-json-logger requests
pip install psycopg2-binary  # Pour tester avec PostgreSQL
```

---

## 📊 COMPARAISON DES BASES DE DONNÉES

| Critère | SQLite | PostgreSQL | MySQL |
|---------|--------|-----------|-------|
| **Installation** | Zéro config | Docker/Installer | Docker/Installer |
| **Développement** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Production** | ❌ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Scalabilité** | Faible | Très haute | Haute |
| **Concurrence** | Faible | Très haute | Haute |
| **Transactions** | Basiques | Avancées | Basiques |

**Recommandation:** 
- **Dev**: SQLite
- **Production**: PostgreSQL

---

## 🚀 INSTRUCTIONS D'INSTALLATION ÉTAPE PAR ÉTAPE

### 1️⃣ Installation MINIMALE (5 min)
```bash
cd api/inventory-service
python -m venv venv
venv\Scripts\activate
pip install fastapi uvicorn sqlalchemy pydantic python-dotenv
python main.py
```

### 2️⃣ Installation COMPLÈTE (10 min)
```bash
cd api/inventory-service
python -m venv venv
venv\Scripts\activate

# Copier requirements.txt amélioré que j'ai créé
pip install -r requirements.txt
```

### 3️⃣ Avec PostgreSQL (Production)
```bash
# Installer PostgreSQL sur votre système
# ou lancer avec Docker:
docker run --name mypostgres -e POSTGRES_PASSWORD=mypassword -p 5432:5432 postgres

# Installer le driver Python
pip install psycopg2-binary

# Configurer .env
DATABASE_URL=postgresql://postgres:mypassword@localhost:5432/inventory_db

python main.py
```

---

## ✅ VÉRIFICATION DE L'INSTALLATION

```bash
# Vérifier que tout est installé
python -c "import fastapi, uvicorn, sqlalchemy, pydantic; print('✅ All dependencies installed!')"

# Ou lancer directement
python main.py

# Accéder à l'API
# http://localhost:8002/docs
```

---

## 🔍 FICHIERS REQUIREMENTS PAR CAS D'USAGE

### requirements.txt (Actuel)
- ✅ Commenté et organisé
- ✅ Production-ready
- ✅ Dépendances optionnelles documentées

### requirements-dev.txt (À créer)
```bash
# ALL dependencies including dev tools
-r requirements.txt  # Hériter du fichier principal
pytest==7.4.3
pytest-cov==4.1.0
pytest-asyncio==0.21.1
black==23.12.0
flake8==6.1.0
mypy==1.7.1
isort==5.13.2
httpx==0.25.2
```

### requirements-prod.txt (À créer)
```bash
# Production only
-r requirements.txt  # Hériter du fichier principal
gunicorn==21.2.0
prometheus-client==0.19.0
```

---

## 📝 RÉSUMÉ: QUE FAUT-IL INSTALLER?

### 🟢 OBLIGATOIRE (Minimum)
```
FastAPI 0.104.1
Uvicorn 0.24.0
SQLAlchemy 2.0.23
Pydantic 2.5.0
Python-dotenv 1.0.0
```

### 🟡 RECOMMANDÉ (Pour commencer)
```
+ Alembic (migrations)
+ Psycopg2-binary (PostgreSQL)
+ Python-json-logger (logging)
+ Requests (HTTP client)
```

### 🟠 PRODUCTION
```
+ Gunicorn (serveur production)
+ Prometheus-client (monitoring)
```

### 🔵 DÉVELOPPEMENT
```
+ Pytest (tests)
+ Black, Flake8, Mypy (code quality)
+ Httpx (test client)
```

---

## 🎓 PROCHAINES ÉTAPES

1. ✅ Installer les **5 dépendances core**
2. ✅ Tester: `python main.py`
3. ✅ Accéder à http://localhost:8002/docs
4. ✅ Si tout fonctionne, ajouter les dépendances supplémentaires selon vos besoins
5. ✅ Pour PostgreSQL: installer `psycopg2-binary` ET configurer DATABASE_URL

---

## ❓ QUESTIONS FRÉQUENTES

**Q: Dois-je installer Gunicorn?**
A: Non pour le dev (uvicorn suffit). Oui pour la production.

**Q: PostgreSQL est obligatoire?**
A: Non. SQLite suffit pour dev. PostgreSQL recommandé pour production.

**Q: Que sont les versions (0.104.1)?**
A: Ce sont les versions spécifiques testées. `==` = version exacte, `~=` = compatible, `>=` = minimum.

**Q: Peux-je utiliser des versions plus récentes?**
A: Oui, généralement. Mais testez d'abord pour éviter les breaking changes.

**Q: Que faire si une dépendance ne s'installe pas?**
A: 
```bash
pip install --upgrade pip setuptools wheel
pip install <package_name>
```

---

✨ **Vous êtes maintenant prêt à développer!** ✨
