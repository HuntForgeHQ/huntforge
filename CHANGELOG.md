# Changelog

All notable changes to HuntForge will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-04-01

### Added

#### 🎉 Initial Release

**Core Framework:**
- 7-phase orchestration system with 30+ integrated tools
- Tag-driven conditional execution engine
- Resource-aware adaptive scheduler (OrchestratorV2)
- Checkpoint/resume capability with JSON state persistence
- Budget tracking (requests and time limits)
- Scope enforcement with wildcard pattern matching
- Docker-based execution with Kali Rolling container
- Profile system (lite, medium, full) for different hardware classes

#### 🔧 Modules

**Phase 1: Passive Recon** (8 tools)
- Subfinder — subdomain enumeration
- Amass — passive/active reconnaissance
- Crtsh — certificate transparency lookup
- TheHarvester — OSINT gathering
- Assetfinder — asset discovery
- Chaos — passive subdomain finder
- Findomain — fast subdomain enumeration
- Waybackurls — historical URL extraction

**Phase 2: Secrets & OSINT** (6 tools)
- Gitleaks — git secret scanning
- TruffleHog — credential detection
- GitHub Dorking — custom query searches
- SecretFinder — JavaScript secret detection
- JSLuice — URL and secret extraction
- Linkfinder — endpoint discovery in JS

**Phase 3: Live Asset Discovery** (6 tools)
- HTTPX — HTTP probing and fingerprinting
- Naabu — fast port scanner
- DNSX — DNS resolver and validator
- PureDNS — wildcard detection
- GoWitness — screenshot capture
- ASNMap — ASN enumeration

**Phase 4: Surface Intelligence** (5 tools)
- WhatWeb — technology detection
- Wappalyzer — tech stack identification
- Nmap Service — service version detection
- Shodan CLI — Shodan integration (API key required)
- Censys CLI — Censys integration (API key required)

**Phase 5: Deep Enumeration** (7 tools)
- Katana — recursive crawling
- GAU — historical URL collection
- ParamSpider — parameter discovery
- GoSpider — concurrent web spider
- GF Extract — pattern matching on URLs
- GraphQL Voyager — schema introspection
- Arjun — HTTP parameter discovery

**Phase 6: Content Discovery** (4 tools)
- FFUF — fuzzing and directory brute-forcing
- Dirsearch — path enumeration
- Feroxbuster — recursive discovery
- WPScan — WordPress path enumeration

**Phase 7: Vulnerability Scanning** (11 tools)
- Nuclei — template-based vuln scanning
- Nuclei CMS — WordPress/Drupal/Joomla templates
- Nuclei Auth — default credential checks
- Subjack — subdomain takeover detection
- Nikto — web server scanner
- Dalfox — reflected XSS scanner
- SQLMap — SQL injection automation
- WPScan Vuln — WordPress vulnerabilities
- CORS Scanner — CORS misconfiguration checks
- SSRF Check — SSRF vulnerability detection

#### 🧠 AI Integration
- Methodology Engine (Ollama + Anthropic support)
- Report Generator (Gemini API)
- Prompt-based custom methodology generation
- AI executive report creation from tags

#### 📊 Monitoring & Logging
- Rich terminal UI with progress indicators
- Structured logging with loguru
- SQLite scan history database
- Flask dashboard for real-time monitoring
- Tag persistence to JSON (enables resume)
- Budget status reporting

#### ⚙️ Configuration
- YAML-based methodology configuration
- Profile system (3 tiers)
- Tool-specific parameter overrides
- Phase dependency management
- Conditional tool execution (`if_tag`)
- Budget limits per phase
- Resource monitor thresholds

#### 🛠️ Developer Experience
- `BaseModule` abstract class for easy tool integration
- Comprehensive error handling with custom exceptions
- Docker isolation for tool execution
- Automated Dockerfile generation with 30+ tools
- Setup wizard and validation scripts
- Smoke test suite

### Documentation

- **README.md** — comprehensive 500+ line documentation
- **CONTRIBUTING.md** — contributor guide with code standards
- Inline code documentation (docstrings)
- Example methodology files
- Profile reference documentation

### Security

- Scope enforcement to prevent out-of-bounds testing
- Rate limiting and budget controls
- Resource monitoring to prevent host exhaustion
- User activity detection for polite scanning
- Checkpoint safety (no duplicate work)

---

## [Planned] - v1.1 (Q2 2026)

### Planned Features

- Target selection interface for Phase 7 (choose which targets to vuln scan)
- Parallel execution for independent phases
- Enhanced dashboard with live tool output streaming
- Export to Burp Suite, other platforms
- Cloud storage integration (S3/GCS)
- Improved Windows support (Docker-free mode)

---

## [Planned] - v1.2 (Q3 2026)

### Planned Features

- Machine learning prioritization of targets
- Collaborative scans with shared TagManager
- Custom tool marketplace/registry
- GitHub Actions CI/CD integration
- Browser extension for scope validation
- Automated exploit chain suggestions

---

## [Planned] - v2.0 (Q4 2026)

### Planned Features

- Distributed scanning across multiple machines
- Real-time team collaboration features
- Automated exploitation with Metasploit integration
- Custom report templates (HackerOne, Bugcrowd)
- Full REST API for programmatic control

---

## Versioning Policy

HuntForge follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html):

- **MAJOR** — incompatible API changes (backwards compatibility breaks)
- **MINOR** — new functionality in a backwards-compatible manner
- **PATCH** — backwards-compatible bug fixes

### Stability Guarantees

- **1.x releases** — stable API for YAML methodology format
- **Core module interface** — `BaseModule` contract will not break
- **Tag system** — tag format and persistence stable
- **Output format** — `output/{domain}/` structure stable

---

## Breaking Changes History

*(None for v1.0.0 — first release)*

Future breaking changes will be documented here with migration guide.

---

## Support Policy

| Version | Released | End of Life | Support |
|---------|----------|-------------|---------|
| 1.0.x   | 2026-04-01 | TBD | Bug fixes only |
| 1.1.x   | TBD | TBD | Full support |
| 2.0.x   | TBD | TBD | Breaking changes |

We recommend always running the latest **patch** version (1.0.x).
**Minor** upgrades (1.0 → 1.1) should be tested before production use.

---

## Migration Guides

### Upgrading from 0.x to 1.0.0

*(No migration needed — first stable release)*

---

## Unreleased

Changes not yet in a release:

- [ ] Feature: parallel phase execution
- [ ] Fix: memory leak in resource monitor thread
- [ ] Enhancement: improved Docker build caching

---

**[⬆ Back to top](#-huntforge-)**
