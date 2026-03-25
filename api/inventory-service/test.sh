#!/bin/bash
# test.sh - Script de test simple pour Linux/Mac

echo "╔════════════════════════════════════════════════════╗"
echo "║     🧪 INVENTORY SERVICE - TEST SCRIPT             ║"
echo "╚════════════════════════════════════════════════════╝"

# Vérifier que le service tourne
echo ""
echo "1️⃣ Vérifier que le service tourne..."
response=$(curl -s http://localhost:8002/health)

if echo "$response" | grep -q "healthy"; then
    echo "✅ Service est actif"
else
    echo "❌ Service n'est pas accessible à http://localhost:8002"
    echo "Lancez d'abord: python main.py"
    exit 1
fi

# Health check
echo ""
echo "2️⃣ Health Check..."
curl -s http://localhost:8002/health | python -m json.tool

# Créer une ressource
echo ""
echo "3️⃣ Créer une ressource..."
RESPONSE=$(curl -s -X POST "http://localhost:8002/resources" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Salle 101",
    "type": "room",
    "description": "Salle de réunion",
    "capacity": 20,
    "location": "Building A",
    "price": 100.0
  }')

echo "$RESPONSE" | python -m json.tool

# Extraire l'ID
RESOURCE_ID=$(echo "$RESPONSE" | grep -o '"id":"[^"]*' | head -1 | cut -d'"' -f4)
echo "🆔 ID créé: $RESOURCE_ID"

# Récupérer la ressource
echo ""
echo "4️⃣ Récupérer la ressource..."
curl -s "http://localhost:8002/resources/$RESOURCE_ID" | python -m json.tool

# Lister les ressources
echo ""
echo "5️⃣ Lister toutes les ressources..."
curl -s "http://localhost:8002/resources" | python -m json.tool

# Créer un créneau
echo ""
echo "6️⃣ Créer un créneau de disponibilité..."
START_TIME=$(date -u -d '+1 day' '+%Y-%m-%dT09:00:00')
END_TIME=$(date -u -d '+1 day 17 hours' '+%Y-%m-%dT17:00:00')

SLOT_RESPONSE=$(curl -s -X POST "http://localhost:8002/resources/$RESOURCE_ID/availability" \
  -H "Content-Type: application/json" \
  -d "{
    \"resource_id\": \"$RESOURCE_ID\",
    \"start_time\": \"$START_TIME\",
    \"end_time\": \"$END_TIME\",
    \"quantity\": 2
  }")

echo "$SLOT_RESPONSE" | python -m json.tool

# Vérifier la disponibilité
echo ""
echo "7️⃣ Vérifier la disponibilité..."
CHECK_START=$(date -u -d '+1 day 10 hours' '+%Y-%m-%dT10:00:00')
CHECK_END=$(date -u -d '+1 day 12 hours' '+%Y-%m-%dT12:00:00')

curl -s "http://localhost:8002/resources/$RESOURCE_ID/availability/check?start_time=$CHECK_START&end_time=$CHECK_END&quantity=1" | python -m json.tool

echo ""
echo "╔════════════════════════════════════════════════════╗"
echo "║          ✅ TESTS COMPLÉTÉS!                       ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""
echo "📖 Voir la documentation: http://localhost:8002/docs"
