.PHONY: help setup start stop logs clean test build dashboard validate quick-test

help: ## Show this help
	@echo "HuntForge - Quick Commands"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Setup:"
	@echo "  setup        First-time setup (Linux/macOS only, Windows: run setup.bat)"
	@echo "  validate     Run validation checks to ensure everything works"
	@echo ""
	@echo "Running:"
	@echo "  start        Start all services (alias for docker-compose up -d)"
	@echo "  stop         Stop all services"
	@echo "  restart      Restart all services"
	@echo "  status       Show service status"
	@echo "  logs         View huntforge logs"
	@echo "  logs-dashboard View dashboard logs"
	@echo ""
	@echo "Testing:"
	@echo "  quick-test   Run smoke test (fast, 5-15 min) - recommended first"
	@echo "  test         Run full scan on test target (1-2 hours)"
	@echo "  shell        Enter huntforge container shell"
	@echo ""
	@echo "Maintenance:"
	@echo "  build        Rebuild Docker images"
	@echo "  clean        Remove containers, images, volumes"
	@echo "  update-tools Update nuclei templates and tool versions"
	@echo ""
	@echo "Info:"
	@echo "  dashboard-url Print dashboard URL"
	@echo "  scans        List previous scan results"
	@echo "  help-commands Show raw docker-compose commands reference"
	@echo ""
	@echo "Examples:"
	@echo "  make quick-test      # Run quick validation scan"
	@echo "  make start && make dashboard-url  # Start and open dashboard"
	@echo ""

start: ## Start all services (alias for docker-compose up -d)
	docker-compose up -d

stop: ## Stop all services
	docker-compose down

logs: ## View logs from huntforge service
	docker-compose logs -f huntforge

logs-dashboard: ## View logs from dashboard
	docker-compose logs -f dashboard

restart: ## Restart all services
	docker-compose restart

build: ## Rebuild Docker images
	docker-compose build

clean: ## Remove containers, images, and volumes
	docker-compose down -v
	docker rmi huntforge_kali huntforge-dashboard 2>/dev/null || true
	docker volume prune -f

test: ## Test against built-in vulnerable target
	@echo "Starting test scan on testaspnet.vulnweb.com..."
	docker exec huntforge python3 huntforge.py scan testaspnet.vulnweb.com --profile low

test-full: ## Test with full methodology (longer)
	@echo "Starting FULL test scan..."
	docker exec huntforge python3 huntforge.py scan testaspnet.vulnweb.com

shell: ## Open shell inside huntforge container
	docker exec -it huntforge bash

shell-dashboard: ## Open shell inside dashboard container
	docker exec -it huntforge-dashboard bash

dashboard-url: ## Print dashboard URL
	@echo "Dashboard: http://localhost:5000"

status: ## Show running services
	docker-compose ps

scans: ## List output directories (scans)
	@echo "Previous scans in output/:"
	@ls -1 output/ 2>/dev/null || echo "No scans yet. Run: make quick-test"

validate: ## Run validation script to check setup
	@echo "Running validation checks..."
	@python3 scripts/validate_setup.py

quick-test: ## Run smoke test (fast validation, 5-15 min)
	@echo "Starting smoke test..."
	@bash scripts/smoke_test.sh

test: ## Run full test scan (1-2 hours) - alias for full methodology
	@echo "Starting full test scan..."
	@docker exec huntforge python3 huntforge.py scan testaspnet.vulnweb.com --profile low

update-tools: ## Update nuclei templates and tool versions (recreate image)
	docker-compose build --no-cache huntforge

help-commands: ## Show all docker-compose commands reference
	@echo "Docker Compose Commands:"
	@echo "  docker-compose ps              # Show service status"
	@echo "  docker-compose logs -f         # Follow logs"
	@echo "  docker-compose up -d           # Start in background"
	@echo "  docker-compose down            # Stop services"
	@echo "  docker-compose restart <svc>   # Restart specific service"
	@echo "  docker-compose build           # Rebuild images"
	@echo "  docker-compose exec huntforge bash  # Enter container"
