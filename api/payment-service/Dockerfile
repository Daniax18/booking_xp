# ──────────────────────────────────────────────────────────
# Dockerfile — Payment Service
# ──────────────────────────────────────────────────────────
# Build : docker build -t booking-xp/payment-service .
# Run   : docker run -p 8004:8004 booking-xp/payment-service
# ──────────────────────────────────────────────────────────

FROM python:3.12-slim

WORKDIR /app

# Copier les requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY . .

# Exposer le port
EXPOSE 8004

# Santé check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import httpx; r=httpx.get('http://localhost:8004/api/v1/payments/health'); exit(0 if r.status_code==200 else 1)"

# Lancer l'application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004"]
