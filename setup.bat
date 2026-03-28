@echo off
REM HuntForge Setup for Windows (with Docker Desktop)

echo ========================================
echo   HuntForge Setup Wizard v1.0
echo ========================================
echo.

REM Check Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo [!] Docker is not installed
    echo.    Please install Docker Desktop first:
    echo.    https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

echo [*] Docker is installed

REM Check if docker-compose exists
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo [!] docker-compose not found, trying docker compose...
    docker compose version >nul 2>&1
    if errorlevel 1 (
        echo [!] Neither docker-compose nor docker compose available
        pause
        exit /b 1
    )
    set COMPOSE_CMD=docker compose
    echo [*] Using 'docker compose'
) else (
    set COMPOSE_CMD=docker-compose
    echo [*] docker-compose is installed
)

REM Create .env if not exists
if not exist .env (
    echo [*] Creating .env file from template...
    copy .env.example .env >nul
    echo [!] .env file created. You can add your API keys later.
    echo     (Optional: ANTHROPIC_API_KEY for AI features)
) else (
    echo [*] .env file already exists
)

REM Create directories
if not exist output mkdir output
if not exist logs mkdir logs

REM Build images
echo.
echo [*] Building Docker images ^(first time may take 10-20 minutes^)...
%COMPOSE_CMD% build --progress=plain
if errorlevel 1 (
    echo [!] Build failed. Check the errors above.
    pause
    exit /b 1
)

REM Start services
echo.
echo [*] Starting HuntForge services...
%COMPOSE_CMD% up -d
if errorlevel 1 (
    echo [!] Failed to start services
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo Services running:
echo   - CLI inside Docker: docker exec huntforge python huntforge.py --help
echo   - Dashboard: http://localhost:5000
echo.
echo Next steps:
echo   1. Optional: Edit .env to add API keys ^(Anthropic, Shodan, etc.^)
echo   2. Optional: Edit %USERPROFILE%\.huntforge\scope.json to add your targets
echo   3. Run your first scan:
echo.
echo      docker exec huntforge python huntforge.py scan testaspnet.vulnweb.com --profile low
echo.
echo   4. View in dashboard: http://localhost:5000
echo.
echo To stop:   docker-compose down
echo To view logs: docker-compose logs -f
echo.
echo Happy hunting! ^^
echo.
pause
