<div align="center">
  <h1>⚡ HuntForge</h1>
  <p><b>AI-Powered, Adaptive Bug Bounty Recon Framework</b></p>
  <p>
    <a href="https://github.com/yourusername/huntforge/issues"><img alt="Issues" src="https://img.shields.io/github/issues/yourusername/huntforge"></a>
    <a href="https://github.com/yourusername/huntforge/network/members"><img alt="Forks" src="https://img.shields.io/github/forks/yourusername/huntforge"></a>
    <a href="https://github.com/yourusername/huntforge/stargazers"><img alt="Stars" src="https://img.shields.io/github/stars/yourusername/huntforge"></a>
    <a href="LICENSE"><img alt="License" src="https://img.shields.io/github/license/yourusername/huntforge"></a>
  </p>
</div>

<br />

## 🚀 The Real-World Problem It Solves

Traditional bug bounty automation frameworks suffer from three major flaws: they are **rigid**, they **pollute the host machine**, and they generate **overwhelming noise**. When security tools run blindly against a target, you hit API rate limits, get IP-banned, and waste hours sorting through false positives.

**HuntForge** solves this by introducing **Adaptive Reconnaissance**. Powered by a multi-agent AI engine and a state machine based on "Confidence Tags", HuntForge runs only the tools that make sense for the target's specific stack. 
If an AI detects a WordPress tag, it triggers `wpscan`. If `gitleaks` finds a hidden token, it automatically pivots downstream phases. All 25+ offensive tools run seamlessly isolated inside a Kali Docker container, keeping your host pure and clean.

## ✨ Key Features

- 🧠 **AI-Assisted Engine:** Uses local (Ollama) and cloud (Gemini) LLMs to dynamically generate scan methodologies and synthesize human-readable reports based on raw JSON tool output.
- 🐳 **Host-Isolated Execution:** Zero dependency hell. A lightweight Python orchestrator runs on your host, firing subprocesses entirely inside a dedicated Kali Linux container holding 25+ security tools.
- 🏷️ **Confidence Tagging System:** Scans are intelligent. Phase 3 relies on tags emitted by Phase 2 (e.g., `has_api`, `wp_xmlrpc_found`, `has_s3`) to conditionally gate expensive tools.
- 📉 **SIEM-Compatible Logging:** Built for the Blue Team as much as the Red Team. Every scan action is emitted as Splunk-ready JSONL for deep observability and detection-engineering exercises.
- 💰 **Budget & Scope Enforcement:** Hard IP/Domain scoping constraints prevent legal headaches, while budget-tracking prevents your expensive APIs (Shodan, AWS, etc.) from draining your wallet.
- 📊 **Web Dashboard:** Track live scans, historical executions, and discovered vulnerabilities via a local Flask dashboard.

## 🛠️ Technology Stack

* **Core Engine:** Python 3.10+
* **Containerization:** Docker & Docker Compose
* **AI/LLMs:** Google Gemini API (Reporting), Ollama / Llama3 (Methodology Generation)
* **Web UI / DB:** Flask, SQLite
* **Security Tools:** 25+ Go, Python, and Ruby-based industry standards (`subfinder`, `nuclei`, `httpx`, `ffuf`, `dalfox`, `gitleaks`, `trufflehog`, etc.)

## 📦 Project Structure & The 7-Phase Modular Pipeline

HuntForge organizes its 25+ offensive modules into 7 distinct tactical phases:

1. **`passive/`** - OSINT and APIs with zero target interaction. *(amass, subfinder, theharvester)*
2. **`secrets/`** - Discovering leaked tokens and API keys. *(gitleaks, trufflehog, github_dorking)*
3. **`discovery/`** - DNS resolution and live host validation. *(httpx, dnsx, naabu)*
4. **`surface_intel/`** - Technology fingerprinting and classification. *(whatweb, wappalyzer, censys_cli)*
5. **`enumeration/`** - Deep crawling and parameter discovery. *(katana, gau, paramspider, graphql_voyager)*
6. **`content_discovery/`** - Directory brute-forcing. *(ffuf, dirsearch, wpscan)*
7. **`vuln_scan/`** - Automated payload execution. *(nuclei, dalfox, subjack)*

## ⚙️ Getting Started

### Prerequisites

- Python 3.10+
- Docker Engine & Docker Compose
- API Keys for necessary services (Gemini, Shodan, Github, etc.)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/huntforge.git
   cd huntforge
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Build the Kali Tool Container:**
   ```bash
   docker-compose build
   docker-compose up -d
   ```
   *Note: This pulls an official Kali Linux base image and installs all 25+ security tools. This step may take several minutes.*

4. **Configure Environment Variables:**
   Rename `.env.example` to `.env` (or set environment variables natively) and populate your keys:
   ```bash
   GEMINI_API_KEY="your-gemini-api-key"
   GITHUB_TOKEN="ghp_..."
   SHODAN_API_KEY="..."
   WPSCAN_API_TOKEN="..."
   ```

### 🚀 Usage Guide

**Basic Full Scan:**
Run the default 7-phase methodology against a single domain.
```bash
python huntforge.py scan --target example.com
```

**AI Methodology Mode:**
Let Ollama generate a custom playbook based on your specific goal (e.g., focus only on GraphQL or APIs).
```bash
python huntforge.py ai --goal "Find hidden parameters in GraphQL endpoints" --target example.com
```

**Generate Reports:**
Ask Gemini to read the raw `scan_events.jsonl` output and synthesize a highly professional PDF/HTML report.
```bash
python huntforge.py report --target example.com --format html
```

**Resume a Interrupted Scan:**
```bash
python huntforge.py resume --target example.com
```

## 🤝 Contributing to HuntForge

Open source thrives on community contributions! HuntForge is designed to be highly extensible. 

### How to add a new security tool to HuntForge:
1. Ensure the binary is installed inside `Dockerfile.kali`.
2. Create a new python file in the appropriate `modules/` phase folder (e.g., `modules/passive/newtool.py`).
3. Inherit from `BaseModule` (via `from modules.base_module import BaseModule`).
4. Ensure your class ends with the `Module` suffix (e.g., `NewtoolModule`).
5. Overwrite the `build_command()` method to dictate how the tool runs. 

Please take a look at our [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines on pushing code, reporting bugs, and our branch strategy.

## 🛡️ Disclaimer

**HuntForge is designed strictly for authorized, legal security assessments.**
Usage of this tool for attacking targets without prior mutual consent is illegal. It is the end user's responsibility to obey all applicable local, state, and federal laws. Developers assume no liability and are not responsible for any misuse or damage caused by this program.

---
*Developed with ❤️ and caffeine by the open-source security community.*
