#!/bin/bash
# HuntForge Setup - One Command Installation
# Works on: Linux, macOS, Windows (WSL2/Docker Desktop)

set -e  # Exit on error

echo "========================================"
echo "  HuntForge Setup Wizard v1.0"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo "[*] Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}[!] Docker is not installed${NC}"
    echo "    Please install Docker Desktop or Docker Engine first:"
    echo "    - https://www.docker.com/products/docker-desktop"
    echo "    - or: sudo apt install docker.io docker-compose"
    exit 1
fi

# Check Docker is running
if ! docker info &> /dev/null; then
    echo -e "${RED}[!] Docker is not running${NC}"
    echo "    Please start Docker Desktop or: sudo systemctl start docker"
    exit 1
fi

echo -e "${GREEN}[✓] Docker is installed and running${NC}"

# Check docker-compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}[!] docker-compose not found, trying docker compose...${NC}"
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
        echo -e "${GREEN}[✓] Using 'docker compose'${NC}"
    else
        echo -e "${RED}[!] Neither docker-compose nor docker compose available${NC}"
        exit 1
    fi
else
    COMPOSE_CMD="docker-compose"
    echo -e "${GREEN}[✓] docker-compose is installed${NC}"
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo ""
    echo "[*] Creating .env file from template..."
    cp .env.example .env
    echo -e "${YELLOW}[!] .env file created. You can add your API keys later.${NC}"
    echo "    (Optional: ANTHROPIC_API_KEY for AI features)"
else
    echo "[*] .env file already exists"
fi

# Create necessary directories
echo "[*] Creating output directories..."
mkdir -p output logs data

# Build Docker images
echo ""
echo "[*] Building Docker images (this may take 10-20 minutes on first run)..."
if $COMPOSE_CMD build --progress=plain; then
    echo -e "${GREEN}[✓] Docker images built successfully${NC}"
else
    echo -e "${RED}[!] Build failed. Check the errors above.${NC}"
    exit 1
fi

# Start services
echo ""
echo "[*] Starting HuntForge services..."
if $COMPOSE_CMD up -d; then
    echo -e "${GREEN}[✓] Services started${NC}"
else
    echo -e "${RED}[!] Failed to start services${NC}"
    exit 1
fi

# Wait for health check
echo "[*] Waiting for huntforge to be ready..."
for i in {1..30}; do
    if docker exec huntforge python3 -c "print('ready')" &> /dev/null; then
        echo -e "${GREEN}[✓] HuntForge is ready!${NC}"
        break
    fi
    sleep 2
    echo -n "."
done
echo ""

# Show status
echo ""
echo "========================================"
echo -e "${GREEN}  Setup Complete!${NC}"
echo "========================================"
echo ""
echo "Services running:"
echo "  - CLI inside Docker: docker exec huntforge python3 huntforge.py --help"
echo "  - Dashboard: http://localhost:5000"
echo ""
echo "Next steps:"
echo "  1. Optional: Edit .env to add API keys (Anthropic, Shodan, etc.)"
echo "  2. Optional: Edit ~/.huntforge/scope.json to add your targets"
echo "  3. Run your first scan:"
echo ""
echo "     docker exec huntforge python3 huntforge.py scan testaspnet.vulnweb.com --profile low"
echo ""
echo "  4. View in dashboard: http://localhost:5000"
echo ""
echo "To stop:   docker-compose down"
echo "To view logs: docker-compose logs -f"
echo "To restart: docker-compose restart"
echo ""
echo "Happy hunting! 🎯"
echo ""
