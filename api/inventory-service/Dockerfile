# Dockerfile pour l'Inventory Service
FROM python:3.11-slim

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copier les requirements
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code
COPY . .

# Créer un répertoire pour les logs
RUN mkdir -p /app/logs

# Port exposé
EXPOSE 8002

# Commande de démarrage
CMD ["python", "main.py"]
