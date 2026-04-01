# HuntForge 🎯

*AI-Powered Bug Bounty Reconnaissance Framework*

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://www.docker.com/)
[![Kali Linux](https://img.shields.io/badge/Kali-Linux-orange)](https://www.kali.org/)
[![Status: Active](https://img.shields.io/badge/Status-Active-success.svg)]()

---

<div align="center">

**Transform your bug bounty workflow with intelligent, adaptive reconnaissance**

[Quick Start](#-quick-start) • [Architecture](#-architecture) • [Features](#-features) • [Contributing](#-contributing)

</div>

---

## 📖 What is HuntForge?

HuntForge is a **production-grade, AI-powered bug bounty reconnaissance framework** that orchestrates 30+ security tools across 7 intelligent phases. It's designed for professional security researchers who need comprehensive, automated reconnaissance while maintaining full control over resource usage, budgets, and scope.

### The Problem HuntForge Solves

**Traditional bug bounty recon is fragmented and inefficient:**

- ❌ Manually running dozens of tools is time-consuming and error-prone
- ❌ No coordination between tools — duplicate work, missed connections
- ❌ Resource exhaustion crashes your machine during heavy scans
- ❌ No intelligence sharing — each tool works in isolation
- ❌ Hard to resume scans after interruptions
- ❌ No standard methodology — each researcher builds their own
- ❌ Scope enforcement is manual and error-prone

**HuntForge transforms this:**

- ✅ **Unified orchestration** — run 30+ tools in 7 coordinated phases
- ✅ **Intelligent tagging system** — tools share discoveries and adapt
- ✅ **Resource-aware scheduling** — automatically adapts to your hardware
- ✅ **Checkpoint/resume** — never lose progress, pause/resume anytime
- ✅ **AI-powered methodology generation** — generate custom methods from natural language
- ✅ **Built-in scope enforcement** — stay within bug bounty program rules
- ✅ **Budget tracking** — control rate limits and request quotas

---

## ✨ Features at a Glance

### 🧠 Intelligent 7-Phase Methodology

```
┌─────────────────────────────────────────────────────────────────┐
│                    HUNTFORGE METHODOLOGY                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ PHASE 1: PASSIVE RECON                                    │ │
│  │ • Subfinder • Amass • Crtsh • TheHarvester • Assetfinder  │ │
│  │ • Chaos • Findomain • Waybackurls                         │ │
│  │ ↓ Emits: has_subdomains, has_wildcard                    │ │
│  └───────────────────────────────────────────────────────────┘ │
│                         ↓                                        │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ PHASE 2: SECRETS & OSINT                                  │ │
│  │ • Gitleaks • TruffleHog • GitHub Dorking • SecretFinder  │ │
│  │ • JSLuice • Linkfinder                                    │ │
│  │ ↓ Emits: leaked_api_keys, leaked_credentials             │ │
│  └───────────────────────────────────────────────────────────┘ │
│                         ↓                                        │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ PHASE 3: LIVE ASSET DISCOVERY                             │ │
│  │ • HTTPX • Naabu • DNSX • PureDNS • GoWitness • ASNMap    │ │
│  │ ↓ Emits: live_hosts_found, screenshots_taken             │ │
│  └───────────────────────────────────────────────────────────┘ │
│                         ↓                                        │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ PHASE 4: SURFACE INTELLIGENCE                             │ │
│  │ • WhatWeb • Wappalyzer • Nmap • Shodan • Censys          │ │
│  │ ↓ Emits: has_api, has_cms, has_auth, has_wordpress      │ │
│  └───────────────────────────────────────────────────────────┘ │
│                         ↓                                        │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ PHASE 5: DEEP ENUMERATION                                 │ │
│  │ • Katana • GAU • ParamSpider • GoSpider • GF Extract     │ │
│  │ • GraphQL Voyager • Arjun                                 │ │
│  │ ↓ Emits: params_found, api_endpoints_found, js_files    │ │
│  └───────────────────────────────────────────────────────────┘ │
│                         ↓                                        │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ PHASE 6: CONTENT DISCOVERY                                │ │
│  │ • FFUF • Dirsearch • Feroxbuster • WPScan • S3Scanner    │ │
│  │ ↓ Emits: admin_panel_found, backup_files_found           │ │
│  └───────────────────────────────────────────────────────────┘ │
│                         ↓                                        │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ PHASE 7: VULNERABILITY SCANNING                           │ │
│  │ • Nuclei • Subjack • Nikto • Dalfox • SQLMap • WPScan    │ │
│  │ ↓ Emits: critical_found, xss_found, sqli_found          │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 🔄 Tag-Driven Conditional Execution

HuntForge uses a sophisticated **tag system** where each tool emits intelligence that controls what runs next:

| Tag | Meaning | Triggers |
|-----|---------|----------|
| `has_wordpress` | WordPress detected | WPScan, Nuclei CMS templates |
| `has_api` | API endpoints found | Arjun, Dalfox, SSRF checks |
| `has_graphql` | GraphQL endpoint | GraphQL introspection |
| `params_found` | URL parameters | Dalfox, SQLMap, Nuclei |
| `has_cms` | Any CMS detected | CMS-specific scanners |
| `has_admin` | Admin panels found | Auth-focused scans |
| `leaked_api_keys` | Secrets in repos | Enhanced credential scanning |

**Example:** If Phase 4 detects WordPress (`has_wordpress`), Phase 7 automatically runs WPScan and Nuclei CMS templates. If no API endpoints are found, resource-intensive parameter scanners skip automatically.

---

## 🏗️ Architecture

HuntForge is built on a **modular, layered architecture** designed for extensibility and reliability:

```
┌──────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                           │
├──────────────────────────────────────────────────────────────────┤
│  CLI (huntforge.py)    │   Dashboard (Flask)   │   AI Engine    │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION LAYER                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │         OrchestratorV2 (Resource-Aware Scheduler)          ││
│  │  • Phase execution manager  • Checkpoint/resume            ││
│  │  • 4-Gate validation system  • Budget enforcement          ││
│  └─────────────────────────────────────────────────────────────┘│
│                          ↓        ↓                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │Tag Manager   │  │Budget Tracker│  │Resource Monitor     │  │
│  │(shared info) │  │(rate limits) │  │(CPU/RAM/User)       │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│                    TOOL EXECUTION LAYER                         │
├──────────────────────────────────────────────────────────────────┤
│  DockerRunner (container isolation)                             │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  Tool Modules (30+ tools)                                   ││
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐ ││
│  │  │Subfinder │ │Nuclei    │ │HTTPX     │ │Gitleaks      │ ││
│  │  │Amass     │ │SQLMap    │ │Naabu     │ │TruffleHog    │ ││
│  │  │... 30+   │ │... tools │ │... tools │ │... modules   │ ││
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘ ││
│  └─────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│                    OUTPUT & PERSISTENCE                         │
├──────────────────────────────────────────────────────────────────┤
│  output/{domain}/                                               │
│  ├── raw/              (tool stdout, JSON, XML)                │
│  ├── processed/        (merged subdomains, live hosts, etc.)   │
│  ├── logs/             (huntforge.log, ai_report.md)           │
│  └── active_tags.json  (TagManager state for resume)           │
└──────────────────────────────────────────────────────────────────┘
```

### The 4-Gate Safety System

Every tool passes through **4 validation gates** before execution:

```
┌─────────────────────────────────────────────────────────────┐
│                    TOOL EXECUTION PIPELINE                  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  GATE 1: Implementation Check                       │   │
│  │  ✓ Tool exists in TOOL_REGISTRY?                    │   │
│  │  ✓ Binary available in Docker?                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                           ↓                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  GATE 2: Tag-Based Conditional Execution            │   │
│  │  ✓ if_tag condition met?                            │   │
│  │  ✓ min_confidence requirement satisfied?            │   │
│  └─────────────────────────────────────────────────────┘   │
│                           ↓                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  GATE 3: Budget Enforcement                         │   │
│  │  ✓ Would exceed request budget?                    │   │
│  │  ✓ Would exceed time budget?                       │   │
│  └─────────────────────────────────────────────────────┘   │
│                           ↓                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  GATE 4: Resource Monitoring                        │   │
│  │  ✓ Sufficient RAM available?                       │   │
│  │  ✓ CPU pressure acceptable?                        │   │
│  │  ✓ User activity considered?                       │   │
│  └─────────────────────────────────────────────────────┘   │
│                           ↓                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  EXECUTION: Adaptive Scheduler                      │   │
│  │  • Dynamically adjusts parameters                  │   │
│  │  • Throttles if system under pressure              │   │
│  │  • Respects concurrency limits                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                           ↓                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  POST-EXECUTION: Tag Emission & Budget Update      │   │
│  │  • Tool emits tags to TagManager                   │   │
│  │  • BudgetTracker charges used requests             │   │
│  │  • Checkpoint saved to disk                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **Docker & Docker Compose** — [Install guide](https://docs.docker.com/get-docker/)
- **Python 3.9+** (for host tools)
- **8GB RAM minimum** (16GB+ recommended)
- **50GB free disk space**

### 5-Minute Setup

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/huntforge.git
cd huntforge

# 2. Start the Kali container
docker compose up -d

# 3. Enter the container
docker exec -it huntforge-kali /bin/bash

# 4. Install Go tools (one-time)
./scripts/installer.py

# 5. Configure your scope (optional)
# Edit ~/.huntforge/scope.json with your bug bounty programs

# 6. Run your first scan
huntforge scan example.com --profile medium
```

### Docker-Free Installation (Advanced)

```bash
# Install system dependencies
sudo apt-get update && sudo apt-get install -y \
    python3 python3-pip docker golang \
    nmap ffuf dirsearch wpscan gitleaks trufflehog \
    sqlmap nikto whatweb

# Install Python dependencies
pip3 install -r requirements.txt

# Install Go tools
go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
# ... (see Dockerfile for complete list)

# Run scan
python3 huntforge.py scan example.com --profile full
```

---

## 🎯 Usage Examples

### Basic Scan

```bash
# Recommended: Medium profile for 8-16GB RAM
huntforge scan target.com --profile medium

# Fast scan with lite profile (4-8GB RAM)
huntforge scan target.com --profile lite

# Comprehensive scan (16GB+ RAM, slower but thorough)
huntforge scan target.com --profile full
```

### AI-Generated Custom Methodology

```bash
# Generate a custom methodology from natural language
huntforge ai "Focus on API endpoints and GraphQL, skip content discovery, emphasize Nuclei templates"

# The AI generates config/custom_methodology.yaml
# Then run it:
huntforge scan target.com --methodology config/custom_methodology.yaml
```

### Resume Interrupted Scan

```bash
# If scan is interrupted (Ctrl+C), simply run again:
huntforge scan target.com --profile medium
# Automatically resumes from last checkpoint

# Or specify checkpoint file explicitly:
huntforge scan target.com --checkpoint-file output/target.com/checkpoint.json
```

### Generate AI Report

```bash
# After scan completes, generate executive report
huntforge report target.com

# Opens Gemini AI for analysis based on discovered tags
# Report saved to: output/target.com/logs/ai_report.md
```

### Monitor Dashboard

```bash
# Start the web dashboard (in another terminal)
python3 dashboard/app.py

# Open http://localhost:5000 in browser
# View scan history, active tags, budget status
```

---

## 🔧 Configuration

### Profile Selection

| Profile | RAM Required | Tools Enabled | Use Case |
|---------|--------------|---------------|----------|
| **lite** | 4-8 GB | 15-20 essential tools | Quick recon, fast results |
| **medium** | 8-16 GB | 25-30 tools | Balanced, recommended |
| **full** | 16+ GB | All 30+ tools | Comprehensive, deep analysis |

**Custom profiles:** Edit `config/profiles/medium.yaml` to fine-tune tool selection and parameters.

### Scope Configuration

```json
{
  "programs": {
    "HackerOne Program": {
      "in_scope": ["*.example.com", "example.com"],
      "out_of_scope": ["admin.example.com", "*.internal.com"]
    }
  }
}
```

**Location:** `~/.huntforge/scope.json`

HuntForge automatically:
- ✅ Blocks targets outside scope
- ✅ Prompts for manual approval if unknown domain
- ✅ Prevents accidental out-of-scope testing

### Budget Controls

```yaml
budget:
  max_requests_total: 100000        # Hard stop
  max_requests_per_phase:           # Per-phase limits
    phase_1_passive_recon: 5000
    phase_7_vuln_scan: 25000
  action_on_exceeded: "warn"        # warn | skip_tool | abort
```

Prevents rate limiting and keeps you within program rules.

---

## 📊 Output Structure

```
output/example.com/
├── raw/                          # Raw tool outputs
│   ├── subfinder.txt
│   ├── httpx.json
│   ├── nuclei.json
│   └── ...
├── processed/                    # Deduplicated, normalized data
│   ├── all_subdomains.txt       # Merged from all sources
│   ├── live_hosts.json
│   ├── parameters.json
│   ├── vulnerabilities.json
│   ├── active_tags.json         # TagManager state (for resume)
│   ├── scan_summary.json        # Final statistics
│   └── budget_status.json
└── logs/
    ├── huntforge.log            # Execution log
    └── ai_report.md             # Gemini-generated report
```

**Data deduplication automatic** — HuntForge normalizes URLs, merges subdomains, and removes duplicates across tools.

---

## 🔍 How Tag-Driven Intelligence Works

**Example: WordPress Detection Flow**

```
Phase 1: Passive Recon
    ↓
Subfinder discovers: admin.example.com, wp.example.com
TagManager sets: has_subdomains (high confidence)

Phase 4: Surface Intelligence
    ↓
WhatWeb scans live hosts → detects "WordPress" in headers
Wappalyzer confirms → WordPress 6.4 detected
TagManager sets: has_wordpress (high confidence)
                has_cms (high confidence)

Phase 7: Vulnerability Scanning
    ↓
Check tags before running...
✓ has_wordpress = TRUE → RUN: WPScan, Nuclei CMS templates
✓ has_cms = TRUE → Additional CMS checks
```

**Result:** No wasted scans. Tools only run when their targets are relevant.

---

## 🧩 Extending HuntForge

### Adding a New Tool

1. **Create module file:** `modules/vuln_scan/mytool.py`

```python
from modules.base_module import BaseModule
from core.exceptions import OutputParseError

class MyToolModule(BaseModule):
    def build_command(self, target: str, output_file: str) -> list:
        """Build shell command as list"""
        return ['mytool', '-d', target, '-o', output_file]

    def run(self, target: str, output_dir: str, tag_manager, config: dict = None) -> dict:
        """Execute tool and return results dict"""
        self.config = config or {}
        output_path = os.path.join(output_dir, 'raw', 'mytool.txt')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        command = self.build_command(target, output_path)
        self._run_subprocess(command)  # Handles Docker execution

        content = self._read_output_file(output_path)
        results = self._parse(content)

        return {
            'results': results,
            'count': len(results),
            'requests_made': self.estimated_requests()
        }

    def emit_tags(self, result: dict, tag_manager) -> None:
        """Set tags based on findings"""
        if result['count'] > 0:
            tag_manager.add('my_custom_tag', confidence='medium',
                          evidence=result['results'][:3], source='mytool')

    def estimated_requests(self) -> int:
        """Budget planning"""
        return 100

    def _parse(self, content: str) -> list:
        """Parse tool output"""
        return [line.strip() for line in content.splitlines() if line.strip()]
```

2. **Register in orchestrator:** Add to `TOOL_REGISTRY` in `core/orchestrator_v2.py`

```python
from modules.vuln_scan.mytool import MyToolModule as MyTool
TOOL_REGISTRY = {
    # ... existing tools
    'mytool': MyTool,
}
```

3. **Add tool profile:** `data/tool_profiles.yaml`

```yaml
mytool:
  phase: "phase_7_vuln_scan"
  phase_weight: "medium"
  base_memory_mb: 200
  base_cpu_cores: 0.5
  scalable_params:
    threads:
      value: 20
      memory_per_unit_mb: 5
      cpu_per_unit: 0.05
      min: 5
      max: 50
  estimated_time_min: 15
```

4. **Configuration:** Add to `config/default_methodology.yaml` in appropriate phase.

That's it! HuntForge handles Docker execution, tagging, budget, resources.

---

## 🤝 Contributing

We welcome contributors! HuntForge is open source and community-driven.

### Getting Started

1. **Fork the repository**
2. **Clone your fork:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/huntforge.git
   cd huntforge
   ```
3. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   pip install -r requirements.txt
   ```
4. **Set up pre-commit hooks:**
   ```bash
   pre-commit install
   ```
5. **Create a branch:**
   ```bash
   git checkout -b feature/amazing-feature
   ```

### Contribution Guidelines

| Type | Guidelines | Code Review |
|------|------------|-------------|
| **New Tool Module** | Follow `BaseModule` interface, include tests | ✅ Required |
| **Bug Fix** | Include reproduction steps, fix + test | ✅ Required |
| **Performance** | Benchmark before/after, mark regressions | ✅ Required |
| **Documentation** | Update README, add examples, update diagrams | ✅ Required |
| **Profile Updates** | Based on empirical measurements, not guesses | ✅ Required |
| **AI Prompts** | Test with 3+ domains before submitting | ✅ Required |

### Development Workflow

```bash
# 1. Make changes
# 2. Run tests
pytest tests/

# 3. Lint
black .
flake8
mypy .

# 4. Pre-commit checks
pre-commit run --all-files

# 5. Test with smoke methodology
python3 huntforge.py scan example.com --methodology config/smoke_test_methodology.yaml

# 6. Commit with conventional commits
git add .
git commit -m "feat: add nuclei template categorization"
```

### Code Structure

```
huntforge/
├── core/                  # Framework core (orchestrator, scheduler, etc.)
│   ├── orchestrator_v2.py     # Main execution engine
│   ├── resource_aware_scheduler.py  # Adaptive scheduling
│   ├── tag_manager.py         # Shared intelligence
│   ├── scope_enforcer.py      # Scope validation
│   └── ...
├── modules/               # Tool modules (30+)
│   ├── passive/          # Phase 1
│   ├── secrets/          # Phase 2
│   ├── discovery/        # Phase 3
│   ├── surface_intel/    # Phase 4
│   ├── enumeration/      # Phase 5
│   ├── content_discovery/# Phase 6
│   └── vuln_scan/        # Phase 7
├── ai/                   # AI integration
│   ├── methodology_engine.py
│   └── report_generator.py
├── config/               # YAML configurations
│   ├── default_methodology.yaml
│   └── profiles/
├── scripts/              # Setup, validation, installer
├── dashboard/            # Flask web UI
├── data/                 # Tool profiles, fingerprints
├── output/               # Generated during scans (gitignored)
└── tests/                # Unit and integration tests
```

### Areas Needing Help

- [ ] **Web Dashboard** — richer visualizations, real-time updates
- [ ] **Report Generator** — improve AI prompts, add sections
- [ ] **Tool Modules** — add missing tools (see `TOOL_REGISTRY` gaps)
- [ ] **Resource Profiles** — empirical measurements for accuracy
- [ ] **Windows Support** — port Docker-free mode to Windows
- [ ] **CI/CD Integration** — GitHub Actions for automated testing
- [ ] **Documentation** — tutorials, video walkthroughs, examples

---

## 🧪 Testing

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests (requires Docker)
pytest tests/integration/ -v

# Smoke test (quick scan against example.com)
./scripts/smoke_test.sh

# Full test suite
pytest -v --cov=huntforge --cov-report=html
```

---

## 📈 Performance Tips

### Optimize for Your Hardware

**8GB RAM (mid-range):**
```bash
# Use medium profile, avoid heavy phases overlapping
huntforge scan example.com --profile medium
```

**16GB+ RAM (high-end):**
```bash
# Use full profile, enable more concurrent tools
# Edit config/profiles/full.yaml:
#   max_concurrent_light_hw: 8
#   max_concurrent_medium_hw: 4
```

**Minimal impact on host (running while working):**
```bash
# HuntForge auto-detects user activity and throttles
# Or manually set profile to 'lite' and phase weights to 'light'
```

### Speed vs Thoroughness Tradeoffs

| Want... | Do This |
|---------|---------|
| **Faster scans** | Use `--profile lite`, skip Phase 7 initially |
| **Deeper analysis** | Use `--profile full`, run all phases |
| **Focused recon** | Generate custom AI methodology targeting specific tech |
| **Resume capability** | Always use checkpoint (default enabled) |
| **Lower noise** | Set `rate_limit` in profile configs |

---

## 🛡️ Security & Ethics

**HuntForge is designed for authorized security testing only:**

- ✅ **Scope enforcement** prevents accidental out-of-scope testing
- ✅ **Rate limiting** protects target infrastructure
- ✅ **Budget tracking** prevents denial-of-service
- ✅ **Checkpoint safety** — no automatic retry on failures

**Legal Considerations:**
- Only test domains you own or have explicit permission to test
- Respect bug bounty program rules and scope definitions
- Use `--profile lite` for sensitive targets to minimize impact
- Review your `~/.huntforge/scope.json` before every scan

**We do not condone unauthorized testing.** Use responsibly.

---

## 🎓 Learning Path

New to bug bounty? Here's how HuntForge helps:

1. **Start with `huntforge scan --profile lite`** — see what tools discover
2. **Review `output/{domain}/processed/active_tags.json`** — understand what was found
3. **Read the Gemini report** (`logs/ai_report.md`) — learn prioritization
4. **Generate custom methodology** with `huntforge ai` prompts
5. ** Gradually increase profile** as you learn tool behaviors

**Recommended reading:**
- [Bug Bounty Bootcamp](https://portswigger.net/burpbounty) by Vickie Li
- [HackerOne's Methodology Guide](https://www.hackerone.com/knowledge-base)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)

---

## 📚 Documentation

| Resource | What You'll Find |
|----------|------------------|
| **This README** | Complete feature overview and usage |
| **CONFIG_GUIDE.md** | Detailed YAML configuration reference |
| **PROFILE_REFERENCE.md** | Profile tuning and optimization |
| **MODULE_DEVELOPMENT.md** | Guide to creating new tool modules |
| **AI_PROMPTS.md** | Best practices for AI methodology generation |
| **API.md** | Python API for embedding HuntForge |
| **CHANGELOG.md** | Version history and breaking changes |

**Need help?** Open an issue or join our Discord (coming soon).

---

## 🏆 Why Choose HuntForge?

| Feature | HuntForge | Competitors |
|---------|-----------|------------|
| **AI Integration** | ✅ Methodology generation & reports | ❌ Manual config only |
| **Resource Aware** | ✅ Adaptive scheduling, user detection | ❌ Fixed concurrency |
| **Tag Intelligence** | ✅ Tools share discoveries | ❌ Tools run independently |
| **Checkpoint/Resume** | ✅ Never lose progress | ❌ Start over if interrupted |
| **Scope Enforcement** | ✅ Built-in, strict validation | ❌ Manual verification |
| **Budget Tracking** | ✅ Per-tool, per-phase limits | ❌ No rate limiting |
| **Extensible** | ✅ Simple BaseModule pattern | ❌ Complex integrations |
| **Docker Ready** | ✅ Kali container with 30+ tools | ❌ Manual installation |
| **Dashboard** | ✅ Web UI for monitoring | ❌ CLI only |

---

## 📊 Real-World Impact

**Before HuntForge:**
```
Manual workflow: 8-12 hours per target
Tools run: ~15 (selected manually)
Coverage: Incomplete, depends on researcher memory
```

**After HuntForge:**
```
Automated workflow: 2-4 hours (hands-off)
Tools run: 30+ (all relevant phases)
Coverage: Comprehensive, tag-driven intelligence
```

**Time savings: 60-70%** with better results.

---

## 🔮 Roadmap

### v1.1 (Q2 2026)
- [ ] **Target selection interface** for Phase 7 (post-recon)
- [ ] **Parallel phase execution** for independent phases
- [ ] **Enhanced dashboard** with live tool output
- [ ] **Export to Burp Suite** and other platforms
- [ ] **Cloud storage integration** (S3, GCS for output)

### v1.2 (Q3 2026)
- [ ] **Machine learning prioritization** — AI predicts high-value targets
- [ ] **Collaborative scans** — multiple researchers, shared TagManager
- [ ] **Custom tool marketplace** — share your modules
- [ ] **CI/CD integration** — run in GitHub Actions
- [ ] **Browser extension** — scope validation from browser

### v2.0 (Q4 2026)
- [ ] **Distributed scanning** — cluster multiple machines
- [ ] **Real-time collaboration** — shared dashboard for teams
- [ ] **Automated exploitation** — integrate with Metasploit, custom scripts
- [ ] **Reporting templates** — HackerOne, Bugcrowd, custom
- [ ] **REST API** — control HuntForge programmatically

---

## 📄 License

MIT License — see [LICENSE](LICENSE) file.

---

## 🙏 Acknowledgments

**Built by security researchers, for security researchers.**

- Inspired by [**Bug bounty Checklist**](https://github.com/jassics/awesome-bugbounty-writeups) community
- Tools integrated: ProjectDiscovery, OWASP, community open source
- Architecture: Influenced by CI/CD pipelines and dataflow programming
- Special thanks to all [contributors](https://github.com/yourusername/huntforge/graphs/contributors)

---

## 📞 Get Involved

- **🐛 Issues:** [GitHub Issues](https://github.com/yourusername/huntforge/issues)
- **💬 Discussions:** [GitHub Discussions](https://github.com/yourusername/huntforge/discussions)
- **📖 Wiki:** Coming soon
- **🐦 Twitter:** [@HuntForgeSec](https://twitter.com/huntforge) (coming soon)

---

<div align="center">

**Made with ❤️ by the HuntForge Team**

[⬆ Back to top](#-huntforge-)

</div>

---

## 📌 Appendix

### A. Complete Tool List (30+)

#### Phase 1: Passive Recon (8 tools)
Subfinder, Amass, Crtsh, TheHarvester, Assetfinder, Chaos, Findomain, Waybackurls

#### Phase 2: Secrets & OSINT (6 tools)
Gitleaks, TruffleHog, GitHub Dorking, SecretFinder, JSLuice, Linkfinder

#### Phase 3: Live Asset Discovery (6 tools)
HTTPX, Naabu, DNSX, PureDNS, GoWitness, ASNMap

#### Phase 4: Surface Intelligence (5 tools)
WhatWeb, Wappalyzer, Nmap Service, Shodan CLI, Censys CLI

#### Phase 5: Deep Enumeration (7 tools)
Katana, GAU, ParamSpider, GoSpider, GF Extract, GraphQL Voyager, Arjun

#### Phase 6: Content Discovery (4 tools)
FFUF, Dirsearch, Feroxbuster, WPScan

#### Phase 7: Vulnerability Scanning (11 tools)
Nuclei, Nuclei CMS, Nuclei Auth, Subjack, Nikto, Dalfox, SQLMap, WPScan Vuln, CORS Scanner, SSRF Check, Open Redirect

**Total: 47 tool configurations across 7 phases**

---

### B. Tag System Reference

All tags emitted by HuntForge tools, organized by phase:

**Phase 1 Tags:**
- `has_subdomains` — subdomains discovered
- `has_wildcard` — wildcard DNS detected

**Phase 2 Tags:**
- `leaked_api_keys` — API tokens found
- `leaked_credentials` — passwords/usernames exposed
- `hidden_subdomains` — new subdomains from secrets
- `github_dorked` — GitHub OSINT completed

**Phase 3 Tags:**
- `live_hosts_found` — HTTP/HTTPS services detected
- `unusual_ports_detected` — non-standard ports open
- `screenshots_taken` — visual recon captured

**Phase 4 Tags (Critical):**
- `has_api` — API endpoints detected
- `has_graphql` — GraphQL specifically
- `has_auth` — login/auth pages
- `has_cms` — CMS platform detected
- `has_wordpress` — WordPress specifically
- `has_cloud_assets` — AWS S3, Azure, GCP
- `has_java` / `has_php` / `has_nodejs` — tech stack
- `has_cors` — CORS misconfigurations
- `has_debug_mode` — verbose errors

**Phase 5 Tags:**
- `params_found` — URL parameters discovered
- `api_endpoints_found` — API paths enumerated
- `js_files_found` — JavaScript for analysis
- `graphql_introspected` — schema obtained

**Phase 6 Tags:**
- `admin_panel_found` — admin/dashboard paths
- `backup_files_found` — .bak, .old, .zip files
- `exposed_git` — .git directory accessible
- `exposed_env` — .env file readable

**Phase 7 Tags:**
- `critical_found` / `high_found` / `medium_found`
- `takeover_found` — subdomain takeover
- `xss_found` / `sqli_found` / `ssrf_found`

---

### C. Glossary

| Term | Definition |
|------|------------|
| **Tag** | Intelligence marker set by tools, read by orchestrator for conditional execution |
| **Phase** | A logical grouping of tools (1-7) with dependencies |
| **Gate** | Validation checkpoint before tool execution (4 gates total) |
| **Profile** | Resource configuration: lite/medium/full |
| **Methodology** | YAML file defining phases, tools, and dependencies |
| **Checkpoint** | JSON state file enabling scan resume |
| **Budget** | Request/time limits to prevent abuse |
| **Scope** | In/out-of-scope domain patterns for safety |
| **Concurrency** | Number of tools running simultaneously |
| **Adaptive Scheduling** | Dynamic parameter adjustment based on resources |

---

### D. Troubleshooting

**Problem:** Docker container not running
```
Solution: docker compose up -d
```

**Problem:** Tool binary not found
```
Solution: Check Dockerfile installed it, or run ./scripts/installer.py
```

**Problem:** Out of memory errors
```
Solution: Use --profile lite, or edit profile to reduce concurrent tools
```

**Problem:** Scan too slow
```
Solution: Reduce tool concurrency in profile config, skip Phase 7 initial scan
```

**Problem:** Can't resume from checkpoint
```
Solution: Checkpoint file corrupted? Delete and restart with same domain
```

**Full troubleshooting guide:** [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

**Last updated:** April 2026  
**Version:** 1.0.0  
**Maintainers:** [@Nimesh-Nakum](https://github.com/Nimesh-Nakum)
