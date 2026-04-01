# HuntForge

<div align="center">

**AI-Powered Bug Bounty Reconnaissance Framework**

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)](https://github.com/HuntForgeHQ/huntforge)
[![Version](https://img.shields.io/badge/Version-2.0.0-orange)](https://github.com/HuntForgeHQ/huntforge/releases)

*Smart • Resource-Aware • Docker-Isolated • Extensible*

</div>

---

## 📖 Table of Contents

- [What is HuntForge?](#what-is-huntforge)
- [Why HuntForge?](#why-huntforge)
- [Features](#features)
- [Architecture Overview](#architecture-overview)
- [Quick Start](#quick-start)
- [Installation Guide](#installation-guide)
- [Usage](#usage)
- [Configuration](#configuration)
- [The 7-Phase Methodology](#the-7-phase-methodology)
- [Resource Profiles](#resource-profiles)
- [Testing & Validation](#testing--validation)
- [Dashboard](#dashboard)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [Project Structure](#project-structure)
- [Security & Ethics](#security--ethics)
- [Team](#team)
- [Roadmap](#roadmap)
- [License](#license)

---

## What is HuntForge?

**HuntForge** is a reconnaissance framework that automates bug bounty reconnaissance using 25+ security tools. It features resource-aware adaptive scheduling, allowing it to run complete multi-phase reconnaissance on hardware with as little as 4 GB of RAM by dynamically adjusting concurrency and tool parameters based on available system resources.

---

## Why HuntForge?

| Challenge | Traditional Approaches | HuntForge |
|-----------|----------------------|-----------|
| **Hardware constraints** | Requires high-end hardware for full scans | Works on 4 GB RAM with adaptive scheduling |
| **Setup complexity** | Manual install of 20+ tools across platforms | One-command Docker-based setup |
| **Resource management** | Fixed concurrency → OOM crashes | Real-time RAM/CPU monitoring with graceful degradation |
| **Noise generation** | All-or-nothing scanning | Optional Phase 7 - run vuln scanning only when needed |
| **Tool integration** | Fragmented scripts | Unified modular architecture with 25+ tools |

---

## Features

### Complete Automated Reconnaissance
- 7-phase methodology covering passive recon through vulnerability scanning
- 25+ integrated security tools automatically orchestrated
- Conditional tool execution based on discovered tags
- Checkpoint and resume capability for long-running scans

### Intelligent Resource Management
- Real-time system monitoring (RAM, CPU, user activity)
- Dynamic parameter scaling based on available resources
- Graceful degradation when system resources are constrained
- Profile-based configuration (lite/medium/full)

### Docker-Based Isolation
- All tools run in pre-configured Kali Linux container
- Consistent environment across platforms
- No tool installation required on host system
- Easy cleanup and portability

### Tag-Driven Intelligence
- Automatic classification of findings
- Confidence-based tag system
- Tools conditionally execute based on tags (e.g., only scan WordPress with wpscan)
- Tags guide Phase 7 vulnerability scanning decisions

### AI Integration (Optional)
- Generate custom methodologies from natural language prompts via Ollama
- Gemini-powered executive report generation
- Smart recon prioritization based on findings

### Web Dashboard
- Real-time scan monitoring
- Visual tag confidence display
- Scan history and statistics
- Tool fingerprint reference

---

## Architecture Overview

HuntForge uses a modular architecture with clear component separation and data flow.

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                     HuntForge Architecture                  │   │
│  │                                                             │   │
│  │   ┌──────────────┐                                        │   │
│  │   │   CLI Entry  │  huntforge.py                          │   │
│  │   └──────┬───────┘                                        │   │
│  │          │                                                │   │
│  │          ▼                                                │   │
│  │   ┌──────────────────┐                                    │   │
│  │   │  Orchestrator V2 │  • Phase execution                 │   │
│  │   │                  │  • Tool scheduling                 │   │
│  │   │                  │  • Resource coordination           │   │
│  │   └────────┬─────────┘                                    │   │
│  │            │                                               │   │
│  │            ├──────────────────────────────┬───────────────┤   │
│  │            │                              │               │   │
│  │            ▼                              ▼               │   │
│  │   ┌──────────────────┐          ┌──────────────────┐     │   │
│  │   │  Tag Manager     │          │   HFLogger       │     │   │
│  │   │  • Store tags    │          │  • Log events    │     │   │
│  │   │  • has_tag()     │          │  • Track phases  │     │   │
│  │   │  • get_confidence│          │  • Record tools  │     │   │
│  │   └──────────────────┘          └──────────────────┘     │   │
│  │            │                              │               │   │
│  │            ├──────────────────────────────┼───────────────┤   │
│  │            │                              │               │   │
│  │            ▼                              ▼               │   │
│  │   ┌─────────────────────────────────────────────────┐    │   │
│  │   │            Resource-Aware Scheduler             │    │   │
│  │   │  • Monitor: RAM, CPU, User Activity            │    │   │
│  │   │  • Decide: run / wait / scale / skip           │    │   │
│  │   │  • Adaptive parameter adjustment               │    │   │
│  │   └────────────────────────────┬────────────────────┘    │   │
│  │                                │                         │   │
│  │                                ▼                         │   │
│  │                     ┌────────────────────┐              │   │
│  │                     │  Checkpoint Manager│              │   │
│  │                     │  • Save after each │              │   │
│  │                     │    tool completion │              │   │
│  │                     │  • Resume on start │              │   │
│  │                     └────────────────────┘              │   │
│  │                                │                         │   │
│  │                                ▼                         │   │
│  │                     ┌────────────────────┐              │   │
│  │                     │   Docker Runner    │              │   │
│  │                     │  • Execute in ctn  │              │   │
│  │                     │  • Stream I/O      │              │   │
│  │                     └──────────┬─────────┘              │   │
│  │                                │                         │   │
│  │                                ▼                         │   │
│  │                     ┌─────────────────────────────────┐ │   │
│  │                     │        Docker Container          │ │   │
│  │                     │       (Kali Linux)              │ │   │
│  │                     │                                 │ │   │
│  │                     │  ┌───────────────────────────┐ │ │   │
│  │                     │  │      Tool Modules         │ │ │   │
│  │                     │  │  ┌─────────────────────┐  │ │ │   │
│  │                     │  │  │ Phase 1: Passive    │  │ │ │   │
│  │                     │  │  │  • subfinder        │  │ │ │   │
│  │                     │  │  │  • amass            │  │ │ │   │
│  │                     │  │  │  • crtsh            │  │ │ │   │
│  │                     │  │  └─────────────────────┘  │ │ │   │
│  │                     │  │  ┌─────────────────────┐  │ │ │   │
│  │                     │  │  │ Phase 2: Secrets    │  │ │ │   │
│  │                     │  │  │  • gitleaks         │  │ │ │   │
│  │                     │  │  │  • trufflehog       │  │ │ │   │
│  │                     │  │  └─────────────────────┘  │ │ │   │
│  │                     │  │  ┌─────────────────────┐  │ │ │   │
│  │                     │  │  │ Phase 3: Discovery  │  │ │ │   │
│  │                     │  │  │  • httpx            │  │ │ │   │
│  │                     │  │  │  • dnsx            │  │ │ │   │
│  │                     │  │  └─────────────────────┘  │ │ │   │
│  │                     │  │         ... (all 7 phases)│ │ │   │
│  │                     │  └───────────────────────────┘ │ │   │
│  │                     └─────────────────────────────────┘ │   │
│  │                                │                         │   │
│  │                                ▼                         │   │
│  │   ┌─────────────────────────────────────────────────────┐│   │
│  │   │                   Output Files                      ││   │
│  │   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐││   │
│  │   │  │  raw/        │  │  processed/ │  │  logs/      │││   │
│  │   │  │  • Tool      │  │  • Findings │  │  • Events   │││   │
│  │   │  │    outputs   │  │  • Tags     │  │  • JSONL    │││   │
│  │   │  └─────────────┘  └─────────────┘  └─────────────┘││   │
│  │   └─────────────────────────────────────────────────────┘│   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Flow Sequence

```
┌──────────────────────────────────────────────────────────────────────┐
│                          Scan Execution Flow                         │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. Scan Initiated     2. Scope Check       3. Load Methodology     │
│     ┌─────────           ┌─────────          ┌─────────             │
│     │ CLI parses│        │ Validate│         │ Read YAML│           │
│     │ args      │───────>│ domain  │───────>│ phases   │           │
│     └─────────           └─────────          └─────────             │
│                              │                                        │
│                              ▼                                        │
│                      4. For Each Phase:                               │
│                         ┌─────────────┐                              │
│                         │ Phase Loop   │                              │
│                         └──────┬──────┘                              │
│                                │                                       │
│                ┌───────────────┼───────────────┐                      │
│                ▼               ▼               ▼                      │
│         ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│         │ Check       │ │Scheduler    │ │Execute Tool │              │
│         │ Resources   │ │Decision:    │ │in Docker:   │              │
│         │ • RAM <80%? │ │ • Run now?  │ │ • docker    │              │
│         │ • CPU <85%? │ │ • Wait?     │ │   exec      │              │
│         │ • Idle user?│ │ • Scale?    │ │ • Stream    │              │
│         └─────────────┘ └─────────────┘ └─────────────┘              │
│                │               │               │                      │
│                └───────────────┼───────────────┘                      │
│                                ▼                                       │
│                        5. Process Results:                            │
│                           ┌─────────────┐                              │
│                           │ Parse tool  │                              │
│                           │ output      │                              │
│                           │ • Extract   │                              │
│                           │   findings  │                              │
│                           │ • Set tags  │                              │
│                           │ • Checkpoint│                              │
│                           └─────────────┘                              │
│                                │                                       │
│                                ▼                                       │
│                        6. Phase Complete?                               │
│                           ┌─────────────┐                              │
│                           │ More phases?│                              │
│                           └──────┬──────┘                              │
│                                  │                                      │
│                    Yes ──────────┘                                      │
│                                  │                                      │
│                                  ▼                                      │
│                    Return to Phase Loop (step 4)                       │
│                                                                      │
│   All phases done → Generate reports → Scan Complete                 │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### Component Interaction Matrix

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Orchestrator V2                               │
├─────────────┬─────────────┬──────────────┬─────────────┬───────────┤
│   Tag       │  Resource    │  HFLogger    │  Checkpoint │  Docker   │
│   Manager   │  Monitor     │              │  Manager    │  Runner   │
├─────────────┼─────────────┼──────────────┼─────────────┼───────────┤
│ • add(tag)  │ • get_load() │ • log_phase_ │ • save()    │ • exec()  │
│ • has(tag)  │ • wait_until_│   start()    │ • load()    │ • stream  │
│ • conf()    │   safe()     │ • log_tool_  │             │           │
│             │              │   start()    │             │           │
│             │              │ • log_tool_  │             │           │
│             │              │   complete() │             │           │
└─────────────┴──────────────┴──────────────┴─────────────┴───────────┘
      │               │               │              │              │
      │               │               │              │              │
      ▼               ▼               ▼              ▼              ▼
   Tags         RAM/CPU          Event          State        Container
   stored       monitoring       logging        persistence   execution
```

### Output Directory Structure

```
output/
└── {domain}/
    ├── raw/
    │   ├── subfinder.txt
    │   ├── httpx.json
    │   ├── nuclei.json
    │   └── ... (one file per tool)
    │
    ├── processed/
    │   ├── all_subdomains.txt      # Merged from all passive tools
    │   ├── live_hosts.json         # From httpx probing
    │   ├── parameters.json         # From enum tools
    │   ├── active_tags.json        # TagManager export
    │   ├── scan_summary.json       # Final statistics
    │   └── efficiency_report.json  # What got skipped & why
    │
    ├── logs/
    │   ├── scan_events.jsonl       # One JSON per event
    │   └── ai_report.md            # Gemini-generated report
    │
    └── checkpoint.json              # Resume state (after each tool)
```

---

## Quick Start

Get HuntForge running in under 5 minutes:

```bash
# 1. Clone
git clone https://github.com/HuntForgeHQ/huntforge.git
cd huntforge

# 2. Start the Kali container (builds on first run)
docker-compose up -d

# 3. Install tools inside the container (first time only)
docker exec huntforge-kali python3 scripts/installer.py --profile lite

# 4. Run your first scan
python3 huntforge.py scan testaspnet.vulnweb.com --profile lite

# 5. View results
cat output/testaspnet.vulnweb.com/processed/scan_summary.json

# 6. Launch dashboard (optional, separate terminal)
python3 dashboard/app.py
# Open http://localhost:5000
```

That's it! HuntForge handles the rest automatically.

---

## Installation Guide

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **OS** | Linux, macOS, Windows WSL2 | Linux/macOS native |
| **RAM** | 4 GB | 8+ GB |
| **CPU** | Dual-core | Quad-core+ |
| **Disk** | 5 GB free | 20 GB SSD |
| **Docker** | 20.10+ | Latest stable |
| **Python** | 3.9+ | 3.11+ |

**Windows users**: Use WSL2 for best compatibility.

### Prerequisites

#### 1. Install Docker

**Linux (Ubuntu/Debian)**:
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker
```

**macOS**:
```bash
brew install --cask docker
# Start Docker Desktop from Applications
```

**Windows**: Install Docker Desktop with WSL2 integration

#### 2. Install Python Dependencies

```bash
python3 --version  # Should be 3.9+
pip3 install --user -r requirements.txt
```

### HuntForge Setup

#### Step 1: Clone Repository

```bash
git clone https://github.com/HuntForgeHQ/huntforge.git
cd huntforge
```

#### Step 2: Configure User Settings (Optional)

```bash
# Run the interactive setup wizard
python3 scripts/setup_wizard.py

# Creates ~/.huntforge/config.json with profile, API keys, scope settings
```

#### Step 3: Start Docker Container

```bash
docker-compose up -d
docker ps | grep huntforge-kali  # Verify it's running
```

#### Step 4: Install Security Tools

```bash
# Choose profile based on your hardware:
docker exec huntforge-kali python3 scripts/installer.py --profile lite    # 4-8 GB
docker exec huntforge-kali python3 scripts/installer.py --profile medium  # 8-16 GB
docker exec huntforge-kali python3 scripts/installer.py --profile full    # 16+ GB
```

Installation takes 5-15 minutes. The installer:
- Installs Kali packages via apt
- Downloads and installs Go-based tools
- Verifies all binaries are accessible

#### Step 5: Configure Scope

Edit `~/.huntforge/scope.json` with your authorized targets:

```json
{
  "allowed_domains": [
    "testaspnet.vulnweb.com",
    "dvwa.co.uk"
  ],
  "auto_approve_test": true
}
```

⚠️ **Only scan targets you own or have permission to test.**

---

## Usage

### Basic Scan

```bash
# Run a full reconnaissance scan
python3 huntforge.py scan example.com --profile medium

# Output structure:
# output/example.com/
# ├── raw/                    # Raw tool outputs
# ├── processed/              # Normalized results
# │   ├── all_subdomains.txt
# │   ├── live_hosts.json
# │   ├── active_tags.json
# │   └── scan_summary.json
# └── logs/
#     ├── scan_events.jsonl   # Structured event log
#     └── ai_report.md        # Gemini executive summary
```

### Command Reference

| Command | Description | Example |
|---------|-------------|---------|
| `scan` | Run reconnaissance | `huntforge scan target.com --profile full` |
| `scan --phases 1-3` | Run specific phases | `huntforge scan target.com --phases 1,2,3` |
| `ai` | Generate custom methodology | `huntforge ai "aggressive recon on subdomains"` |
| `report` | Generate AI report | `huntforge report target.com` |
| `resume` | Continue interrupted scan | `huntforge resume target.com` |

### Common Use Cases

#### Quick Recon (Phases 1-3)

```bash
python3 huntforge.py scan target.com --profile lite --phases 1,2,3
```
Completes in 1-2 hours. Use for fast attack surface mapping.

#### Custom Methodology via AI

```bash
python3 huntforge.py ai "fast passive recon only, focus on subdomains and secrets"
python3 huntforge.py scan target.com --methodology config/generated_methodology.yaml
```

#### Vulnerability Scanning (After Recon)

```bash
# First run recon (phases 1-6)
python3 huntforge.py scan target.com --profile medium

# Review findings, then optionally run Phase 7
python3 huntforge.py scan target.com --profile full --phase 7
```

---

## Configuration

### Methodology YAML

Controls what tools run and when. Conditional execution based on tags:

```yaml
phases:
  phase_1_passive_recon:
    label: "Passive Recon"
    parallel: true
    weight: light

    tools:
      subfinder:
        enabled: true
        timeout: 300
        extra_args: "-sources all"

      amass:
        enabled: true
        if_tag: "has_subdomains"   # Only if subfinder found subdomains
        min_confidence: "medium"

  phase_7_vuln_scan:
    label: "Vulnerability Scanning"
    conditional_tools:
      - tool: nuclei
        if_tag: "has_live_hosts"
      - tool: sqlmap
        if_tag: "params_found"
```

### Resource Profiles

Profiles in `config/profiles/{lite,medium,full}.yaml` control concurrency and tool selection.

| Profile | RAM | Time (Full) | Tools | Best For |
|---------|-----|-------------|-------|----------|
| `lite` | 4 GB | 12-20 hrs | 8 core | Low-end laptops |
| `medium` | 8 GB | 4-8 hrs | 15 | Workstations |
| `full` | 16+ GB | 1.5-3 hrs | All 25+ | High-end rigs |

### User Config (~/.huntforge/config.json)

```json
{
  "default_profile": "medium",
  "gemini_api_key": "your-key",
  "shodan_api_key": "your-key",
  "strict_scope": true
}
```

---

## The 7-Phase Methodology

HuntForge executes reconnaissance across 7 logical phases.

### Phase 1: Passive Reconnaissance

**Goal**: Discover subdomains without contacting the target

**Tools**: subfinder, amass, crtsh, theharvester, assetfinder, chaos, findomain, waybackurls

**Output**: `all_subdomains.txt`

**Tags**: `subdomain_list`, `has_subdomains`, `has_wildcard`

**Runtime**: 5-30 minutes

---

### Phase 2: Secrets & OSINT Collection

**Goal**: Find exposed credentials and sensitive data in public repositories

**Tools**: gitleaks, trufflehog, github_dorking, secretfinder, jsluice, linkfinder

**Input**: Subdomains from Phase 1

**Output**: `leaked_secrets.json`

**Tags**: `leaked_api_keys`, `leaked_credentials`

**Runtime**: 10-60 minutes

---

### Phase 3: Live Asset Discovery

**Goal**: Determine which assets are live and gather network information

**Tools**: httpx, dnsx, naabu, puredns, gowitness, asnmap

**Input**: Subdomains

**Output**: `live_hosts.json`, `open_ports.json`

**Tags**: `has_live_hosts`, `unusual_ports_detected`

**Runtime**: 15-90 minutes

---

### Phase 4: Surface Intelligence

**Goal**: Fingerprint technologies and services

**Tools**: whatweb, wappalyzer, nmap_service, shodan_cli, censys_cli

**Input**: Live hosts

**Output**: `tech_stack.json`

**Tags**: `has_wordpress`, `has_php`, `has_api`, `has_auth`, `has_cloud_assets`

**Runtime**: 20-120 minutes

---

### Phase 5: Web Enumeration

**Goal**: Crawl and enumerate endpoints, parameters, APIs

**Tools**: katana, gau, paramspider, gospider, gf_extract, graphql_voyager, arjun

**Input**: Live hosts

**Output**: `all_urls.txt`, `parameters.json`, `api_endpoints.json`

**Tags**: `params_found`, `js_files_found`, `has_api`

**Runtime**: 30 min - 3 hours

---

### Phase 6: Content Discovery

**Goal**: Discover hidden files and directories

**Tools**: ffuf, dirsearch, feroxbuster, wpscan

**Input**: Live hosts

**Output**: `discovered_paths.txt`

**Tags**: `admin_panel_found`, `backup_files`

**Runtime**: 1-6 hours

---

### Phase 7: Vulnerability Scanning

**Goal**: Run active vulnerability scanners on prioritized targets

**Tools**: nuclei, subjack, dalfox, nikto, sqlmap, wpscan_vuln, cors_scanner, ssrf_check

**Input**: Filtered based on tags

**Output**: `vulnerabilities.json`

**Tags**: `sqli_vulnerable`, `xss_vulnerable`, `subdomain_takeover`

**Runtime**: 1-8 hours (optional - user prompted after Phase 6)

---

## Resource Profiles

HuntForge adapts to your hardware automatically.

```
┌─────────────┬──────────────┬──────────────┬──────────────┐
│   Profile   │   Lite       │   Medium     │   Full       │
├─────────────┼──────────────┼──────────────┼──────────────┤
│ RAM         │  4 GB        │  8 GB        │  16+ GB      │
│ Max Workers │  2-4         │  4-8         │  8-16        │
│ Time (Full) │  12-20 hrs   │  4-8 hrs     │  1.5-3 hrs   │
│ Tools       │  8 core      │  15          │  All 25+     │
├─────────────┼──────────────┼───────┬──────┼──────────────┤
│ Best For    │  Laptops     │  Work-│  Servers/    │
│             │  Overnight   │  stations│  High-end   │
└─────────────┴──────────────┴───────┴──────┴──────────────┘
```

### Adaptive Behavior

The scheduler:
1. Monitors RAM/CPU every 2 seconds
2. Estimates tool requirements from profile data
3. Scales parameters if resources constrained (e.g., reduce threads)
4. Waits or skips if system under critical pressure
5. Never crashes due to OOM - always gracefully degrades

---

## Testing & Validation

### Verify Installation

```bash
# Check Docker container
docker ps | grep huntforge-kali

# Verify tools
docker exec huntforge-kali which subfinder
docker exec huntforge-kali which nuclei

# Run diagnostic
docker exec huntforge-kali python3 scripts/check_tools.py
```

### Test with Safe Targets

```bash
# Legal test targets:
python3 huntforge.py scan testaspnet.vulnweb.com --profile lite
python3 huntforge.py scan dvwa.co.uk --profile lite
```

Expected terminal output:
```
┌─────────────────────────────────────────────────────────────┐
│           HuntForge v2.0.0 — Recon Framework               │
├─────────────────────────────────────────────────────────────┤
│ Scan Configuration                                          │
│   Target:      testaspnet.vulnweb.com                     │
│   Profile:     lite                                       │
│                                                             │
│ Scope check passed ✓                                        │
│                                                             │
│ Launching HuntForge                                        │
├─────────────────────────────────────────────────────────────┤
│ Phase: Passive Recon                                        │
│   subfinder → 12 results in 15s                            │
│   crtsh → 8 results in 3s                                  │
└─────────────────────────────────────────────────────────────┘
```

### Validate Output

```bash
# Summary file
cat output/testaspnet.vulnweb.com/processed/scan_summary.json | python3 -m json.tool

# Expected structure
# {
#   "domain": "...",
#   "subdomain_count": 20,
#   "live_host_count": 15,
#   "tech_stack": [...],
#   "critical_tags": [...]
# }

# Event log (one JSON per line)
head -5 output/testaspnet.vulnweb.com/logs/scan_events.jsonl | python3 -m json.tool
```

---

## Dashboard

Launch the web dashboard:

```bash
python3 dashboard/app.py
# Open http://localhost:5000
```

### Dashboard Interface

```
┌─────────────────────────────────────────────────────────────┐
│  HuntForge Dashboard                                        │
├─────────────────────────────────────────────────────────────┤
│  Recent Scans                    Scan Details               │
│  ┌──────────────────────────┐   ┌──────────────────────┐   │
│  │ ID │ Domain      │ Tags  │   │ example.com          │   │
│  │ 1  │ test.com    │ 8     │   ├──────────────────────┤   │
│  │ 2  │ demo.com    │ 12    │   │ Status: COMPLETED   │   │
│  │    │              │       │   │ Tags:                │   │
│  │    │              │       │   │ • [HIGH] has_api    │   │
│  └──────────────────────────┘   └──────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

Features:
- View recent scans with status and tag counts
- Drill into individual scan details
- See phase execution timeline
- View tag confidence levels
- Browse tool fingerprint database

---

## Troubleshooting

### Container Issues

```bash
# Start container
docker-compose up -d

# Check logs if startup fails
docker-compose logs kali

# Restart container
docker-compose restart
```

### Missing Tools

```bash
# Re-run installer
docker exec huntforge-kali python3 scripts/installer.py --profile full

# Verify specific tool
docker exec huntforge-kali which subfinder
```

### Memory Errors

```bash
# Use lite profile
python3 huntforge.py scan target.com --profile lite

# Close other applications to free RAM
# Skip Phase 7 if system is constrained
```

### Slow Performance

This is expected on low-end hardware. Options:
- Use higher profile (if RAM allows)
- Run overnight
- Skip Phase 7 (vulnerability scanning)
- Use SSD storage

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for complete guidelines.

### Quick Start for Contributors

1. Fork and clone
2. Create feature branch: `git checkout -b feature/your-feature`
3. Make changes and test
4. Follow Conventional Commits for messages
5. Submit Pull Request

### Good First Issues

- Add missing tool modules (nuclei already done, others WIP)
- Improve error messages
- Add unit tests
- Enhance dashboard with charts
- Windows/WSL2 compatibility testing

### Code Standards

- PEP 8 compliance (use `black`)
- Type hints on all functions
- Google-style docstrings
- Tests for new functionality
- No breaking changes to existing interfaces

---

## Project Structure

```
huntforge/
├── huntforge.py              # Main CLI
├── orchestrator_v2.py        # Core engine (adaptive)
├── requirements.txt          # Python dependencies
├── docker-compose.yml        # Container orchestration
├── Dockerfile.kali           # Kali image with tools
│
├── core/                     # Core components
│   ├── base_module.py        # Tool module base class
│   ├── resource_monitor.py   # System resource tracking
│   ├── tag_manager.py        # Tag storage & queries
│   ├── hf_logger.py          # Structured logging
│   ├── scope_enforcer.py     # Scope validation
│   ├── scan_history.py       # SQLite history
│   └── exceptions.py         # Custom exceptions
│
├── modules/                  # Tool integrations (25+)
│   ├── passive/              # Phase 1 (subfinder, amass...)
│   ├── secrets/              # Phase 2 (gitleaks, trufflehog...)
│   ├── discovery/            # Phase 3 (httpx, dnsx...)
│   ├── surface_intel/        # Phase 4 (whatweb...)
│   ├── enumeration/          # Phase 5 (katana, gau...)
│   ├── content_discovery/    # Phase 6 (ffuf, dirsearch...)
│   └── vuln_scan/            # Phase 7 (nuclei, dalfox...)
│
├── ai/                       # AI integration
│   ├── methodology_engine.py # Ollama → YAML
│   └── report_generator.py   # Gemini → Markdown
│
├── dashboard/                # Web UI
│   ├── app.py
│   ├── templates/
│   └── static/
│
├── config/
│   ├── default_methodology.yaml
│   ├── profiles/{lite,medium,full}.yaml
│   └── machine_profiles.yaml
│
├── data/
│   ├── tool_profiles.yaml    # Resource estimates
│   └── bug_bounty_scopes.json
│
├── scripts/
│   ├── installer.py          # Tool installation
│   ├── check_tools.py        # Verification
│   └── setup_wizard.py       # First-run config
│
└── output/                   # Generated per scan
    └── {domain}/
        ├── raw/
        ├── processed/
        ├── logs/
        └── checkpoint.json
```

---

## Security & Ethics

⚠️ **Only scan targets you own or have explicit permission to test.**

### Legal Compliance

Scanning without authorization is illegal in most jurisdictions and can result in criminal charges, civil lawsuits, and employment termination.

### Safe Practice Targets

Use these for learning:
- `testaspnet.vulnweb.com` - ASP.NET test site
- `dvwa.co.uk` - Damn Vulnerable Web App
- `demo.testfire.net` - Test bank
- `portswigger-labs.net` - Web Security Academy
- Your own local VMs

### Scope Enforcement

HuntForge includes automatic scope checking:
1. Validates against `~/.huntforge/scope.json`
2. Checks known bug bounty programs in `data/bug_bounty_scopes.json`
3. Blocks out-of-scope targets by default
4. Requires manual confirmation for unknown targets

### Responsible Disclosure

If you discover vulnerabilities:
1. Document steps to reproduce
2. Report promptly to vendor/bug bounty platform
3. Don't exploit beyond proof-of-concept
4. Don't access or exfiltrate data
5. Give organization time to fix before public disclosure

---

## Team

HuntForge was developed as a structured team project:

| Role | Member | Responsibility |
|------|--------|----------------|
| Red Team Lead | Member 1 | Core orchestrator, scheduler, tag system |
| Red Team Partner | Member 2 | Tool modules (25+), AI integration |
| Blue Team 1 | Member 3 | Logging, detection, SIEM formatting |
| Blue Team 2 | Member 4 | Dashboard, scope enforcement, onboarding |

See [implementation.md](implementation.md) for detailed breakdown.

---

## Roadmap

### v2.1 (Current)
- [x] Complete Phase 7 modules
- [x] Adaptive scheduling with parameter scaling
- [x] Checkpoint/resume
- [ ] SQLMap wrapper improvements
- [ ] Windows WSL2 polish

### v2.2 (Next)
- [ ] Real-time dashboard with WebSocket updates
- [ ] Multi-target scanning
- [ ] Export reports (PDF/JSON)
- [ ] CLI auto-completion
- [ ] Advanced dashboard filtering

### v3.0 (Future)
- [ ] Distributed scanning
- [ ] Cloud integration (AWS Lambda)
- [ ] ML-based target prioritization
- [ ] REST API
- [ ] Plugin system

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

<div align="center">

**Made by the HuntForge Team**

[Documentation](README.md) • [Contributing](CONTRIBUTING.md) • [Issues](https://github.com/HuntForgeHQ/huntforge/issues)

</div>
