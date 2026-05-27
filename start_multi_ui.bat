@echo off
REM JARVIS Multi-UI Quick Start Script (Windows)
REM Starts all three components: Backend, Web Dashboard, Terminal UI

echo.
echo ======================================================================
echo  JARVIS Multi-UI Launcher
echo ======================================================================
echo.

REM Check if running as admin (optional but helpful)
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Note: Run as Administrator for best experience
    echo.
)

REM Get directory
set JARVIS_DIR=%~dp0

echo Preparing JARVIS Multi-UI Setup...
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please install Python 3.8+
    pause
    exit /b 1
)
echo ✓ Python found

REM Check Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Node.js not found. Web dashboard will not work.
    echo Please install Node.js 16+ from https://nodejs.org/
)
echo ✓ Node.js found

echo.
echo ======================================================================
echo Next Steps:
echo ======================================================================
echo.
echo Opening 3 terminals...
echo.
echo 1. Backend:      http://localhost:8000
echo 2. Web Dashboard: http://localhost:3000
echo 3. Terminal UI:  In terminal window
echo.
echo Wait for all three to start (30-60 seconds)
echo.

REM Start Backend
echo Starting Backend...
start cmd /k "cd /d %JARVIS_DIR% && python jarvis_backend.py"
timeout /t 3 >nul

REM Start Web Dashboard
echo Starting Web Dashboard...
if exist "%JARVIS_DIR%jarvis-dashboard\" (
    start cmd /k "cd /d %JARVIS_DIR%jarvis-dashboard && npm run dev"
) else (
    echo Creating Next.js project...
    cd /d %JARVIS_DIR%
    call npx create-next-app@latest jarvis-dashboard --typescript --tailwind --eslint --app --no-git
    cd jarvis-dashboard
    call npm install axios recharts lucide-react
    echo Please copy component files from WEB_DASHBOARD_SETUP.md
    start cmd /k "npm run dev"
)
timeout /t 3 >nul

REM Start Terminal UI
echo Starting Terminal UI...
start cmd /k "cd /d %JARVIS_DIR% && python jarvis_terminal_ui.py"

echo.
echo ======================================================================
echo All services starting...
echo ======================================================================
echo.
echo Services:
echo   Backend:       http://localhost:8000
echo   API Docs:      http://localhost:8000/docs
echo   Web Dashboard: http://localhost:3000
echo   Terminal UI:   Check terminal window
echo.
echo Give services 10-15 seconds to fully start
echo.
pause
