@echo off
REM test.bat - Script de test pour Windows

cls
echo ╔════════════════════════════════════════════════════╗
echo ║     🧪 INVENTORY SERVICE - TEST SCRIPT             ║
echo ╚════════════════════════════════════════════════════╝

REM Vérifier que le service tourne
echo.
echo 1️⃣ Vérifier que le service tourne...
curl -s http://localhost:8002/health >nul 2>&1

if %errorlevel% == 0 (
    echo ✅ Service est actif
) else (
    echo ❌ Service n'est pas accessible
    echo Lancez d'abord: python main.py
    pause
    exit /b 1
)

REM Health check
echo.
echo 2️⃣ Health Check...
call curl -s http://localhost:8002/health

REM Créer une ressource
echo.
echo.
echo 3️⃣ Créer une ressource...
for /f "delims=" %%i in ('curl -s -X POST "http://localhost:8002/resources" -H "Content-Type: application/json" -d "{\"name\":\"Salle 101\",\"type\":\"room\",\"description\":\"Salle de réunion\",\"capacity\":20,\"location\":\"Building A\",\"price\":100.0}"') do set RESPONSE=%%i

echo %RESPONSE%

REM Lister les ressources
echo.
echo 4️⃣ Lister les ressources...
curl -s "http://localhost:8002/resources"

REM Vérifier la disponibilité
echo.
echo 5️⃣ Vérifier la disponibilité...
curl -s "http://localhost:8002/resources?type=room"

echo.
echo.
echo ╔════════════════════════════════════════════════════╗
echo ║          ✅ TESTS COMPLÉTÉS!                       ║
echo ╚════════════════════════════════════════════════════╝
echo.
echo 📖 Voir la documentation: http://localhost:8002/docs
echo.
pause
