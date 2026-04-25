@echo off
REM Child Guardian App - Complete Setup & Run Script
REM This script installs dependencies and starts the Flask app

echo.
echo ================================================
echo  Child Guardian App - Setup & Launch
echo ================================================
echo.

REM Check if virtual environment exists
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    echo ✓ Virtual environment created
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Install/upgrade dependencies
echo.
echo Installing dependencies...
pip install --upgrade pip > nul 2>&1
pip install -r requirements.txt > nul 2>&1
echo ✓ Dependencies installed

REM Check if database needs initialization
if not exist "instance\site.db" (
    echo.
    echo ⚠️  Database not found. Initializing...
    python init_db.py
    echo ✓ Database initialized
) else (
    echo ✓ Database found
)

REM Show database status
echo.
echo Database Status:
python check_db.py
echo.

REM Start the Flask app
echo.
echo ================================================
echo  🚀 Starting Flask App...
echo ================================================
echo.
echo 📱 Open your browser and go to:
echo    http://127.0.0.1:5000
echo.
echo 🔑 Test Credentials:
echo    Username: demo_parent
echo    Password: password123
echo.
echo Press Ctrl+C to stop the server
echo.

python app.py
