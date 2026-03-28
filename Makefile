.PHONY: help install test clean status logs

help: ## Show this help
	@echo "HuntForge - Native Installation (No Docker)"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Setup:"
	@echo "  install      Install dependencies and tools (first-time only)"
	@echo "  validate     Check if installation is correct"
	@echo ""
	@echo "Running:"
	@echo "  test         Run quick test scan (5-15 min, lite profile)"
	@echo "  test-full    Run full scan on test target (2-4 hours)"
	@echo "  scan         Scan a custom target: make scan DOMAIN=example.com"
	@echo ""
	@echo "Utilities:"
	@echo "  status       Show tool installation status"
	@echo "  logs         Show recent logs"
	@echo "  clean        Clean output directories"
	@echo "  clean-all    Clean output and logs"
	@echo ""
	@echo "Examples:"
	@echo "  make install              # Install tools (first time)"
	@echo "  make test                # Quick validation scan"
	@echo "  make scan DOMAIN=testaspnet.vulnweb.com PROFILE=lite"
	@echo ""

install: ## Install tools and dependencies (first-time)
	@echo "Running HuntForge installer..."
	@python3 scripts/installer.py --profile lite
	@echo ""
	@echo "Installation complete! Next:"
	@echo "  1. Edit ~/.huntforge/scope.json with your targets"
	@echo "  2. Run: make test"

validate: ## Validate installation
	@echo "Validating HuntForge installation..."
	@python3 scripts/validate_setup.py || true

test: ## Quick test scan (5-15 min)
	@echo "Starting quick test scan..."
	@python3 huntforge.py scan testaspnet.vulnweb.com --profile lite

test-full: ## Full test scan (2-4 hours)
	@echo "Starting full test scan..."
	@python3 huntforge.py scan testaspnet.vulnweb.com --profile medium

scan: ## Scan a custom target
	@if [ -z "$(DOMAIN)" ]; then \
		echo "Usage: make scan DOMAIN=example.com [PROFILE=lite]"; \
		exit 1; \
	fi
	@python3 huntforge.py scan $(DOMAIN) --profile $(or $(PROFILE),lite)

status: ## Show tool installation status
	@echo "Checking installed tools..."
	@python3 -c "from scripts.installer import HuntForgeInstaller; i = HuntForgeInstaller(); print('Profile:', i.profile); i.check_existing_tools(i.PROFILE_TOOLS[i.profile])" 2>/dev/null || echo "Run 'make install' first"

logs: ## Show recent logs
	@echo "=== Recent HuntForge logs ==="
	@tail -50 logs/huntforge.log 2>/dev/null || echo "No logs found yet"

clean: ## Clean output directories (preserves logs)
	@echo "Cleaning output/..."
	@rm -rf output/*
	@echo "Done."

clean-all: ## Clean everything including logs
	@echo "Cleaning output/ and logs/..."
	@rm -rf output/*
	@rm -rf logs/*
	@echo "Done."

recon-only: ## Run only phases 1-6 (reconnaissance, no vuln scanning)
	@if [ -z "$(DOMAIN)" ]; then \
		echo "Usage: make recon-only DOMAIN=example.com"; \
		exit 1; \
	fi
	@python3 huntforge.py scan $(DOMAIN) --profile $(or $(PROFILE),lite) --phases 1,2,3,4,5,6

resume: ## Resume interrupted scan
	@if [ -z "$(DOMAIN)" ]; then \
		echo "Usage: make resume DOMAIN=example.com"; \
		exit 1; \
	fi
	@python3 huntforge.py scan $(DOMAIN) --resume

dashboard: ## Start web dashboard (in background)
	@echo "Starting dashboard on http://localhost:5000"
	@python3 dashboard/app.py &

stop-dashboard: ## Stop dashboard
	@pkill -f "dashboard/app.py" 2>/dev/null || echo "Dashboard not running"

report: ## Generate AI report for completed scan
	@if [ -z "$(DOMAIN)" ]; then \
		echo "Usage: make report DOMAIN=example.com"; \
		exit 1; \
	fi
	@python3 huntforge.py report $(DOMAIN)

install-wordlists: ## Download additional wordlists (large download)
	@python3 scripts/installer.py --profile lite --download-wordlists

update-profiles: ## Re-scan system resources and suggest profile
	@python3 -c "from core.resource_aware_scheduler import ResourceMonitor; r = ResourceMonitor(); import time; time.sleep(2); c = r.get_capacity(); print(f'Total RAM: {c.total_ram_gb:.1f} GB'); print(f'Recommended profile: {\"lite\" if c.total_ram_gb < 8 else \"medium\" if c.total_ram_gb < 16 else \"full\"}')"
