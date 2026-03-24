# ──────────────────────────────────────────────────
# Dockerfile — Log Service (Multi-stage build)
# ──────────────────────────────────────────────────
# 📚 Multi-stage build : sépare construction et exécution
# Stage 1 (builder) : installe les dépendances Python
# Stage 2 (runtime) : ne garde que le nécessaire → image légère
# ──────────────────────────────────────────────────

# ── Stage 1 : Builder ──
FROM python:3.12-slim AS builder

WORKDIR /build

# Copier et installer les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2 : Runtime ──
FROM python:3.12-slim AS runtime

# Métadonnées
LABEL maintainer="El Nadje <londjide@gmail.com>"
LABEL service="log-service"
LABEL project="booking-xp"

# Créer un utilisateur non-root (sécurité)
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copier les dépendances depuis le builder
COPY --from=builder /install /usr/local

# Copier le code source
COPY . .

# Changer le propriétaire
RUN chown -R appuser:appuser /app

# Utiliser l'utilisateur non-root
USER appuser

# Port exposé
EXPOSE 8005

# Health check intégré au conteneur Docker
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; r=httpx.get('http://localhost:8005/api/v1/health'); exit(0 if r.status_code==200 else 1)" || exit 1

# Démarrage
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005"]
