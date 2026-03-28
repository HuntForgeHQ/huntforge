# HuntForge - Quick Start Guide

**Get up and running in 2 commands.**

---

## **Prerequisites**

- **Docker Desktop** (Windows/Mac) or **Docker Engine** (Linux)
  - Download: https://www.docker.com/products/docker-desktop
- **4GB RAM** minimum (8GB recommended)
- **20GB disk space** (for tools and Docker images)

> **No Python, Go, or any other dependencies needed.** Everything runs in Docker.

---

## **Setup (2 Minutes)**

### **Linux / macOS**

```bash
# 1. Clone repository
git clone https://github.com/HuntForgeHQ/huntforge.git
cd huntforge

# 2. Run setup script
bash setup.sh

# That's it! Setup automates everything.
```

### **Windows (PowerShell / CMD)**

```cmd
# 1. Clone repository
git clone https://github.com/HuntForgeHQ/huntforge.git
cd huntforge

# 2. Run setup script (right-click → Run as administrator)
setup.bat
```

---

## **First Scan (30 Seconds)**

```bash
# Run against the built-in test target (safe, legal)
docker exec huntforge python3 huntforge.py scan testaspnet.vulnweb.com --profile low
```

**Result:** Complete recon + vulnerability scan in ~10-30 minutes.

---

## **View Results**

### **Dashboard (Recommended)**
Open in browser: **http://localhost:5000**

View live scan progress, browse findings, export reports.

### **CLI**
```bash
# Enter the container
docker exec -it huntforge bash

# Inside container:
python3 huntforge.py report testaspnet.vulnweb.com

# Or view raw results:
cat output/testaspnet.vulnweb.com/processed/vulnerabilities.json | jq '.'
```

---

## **What's Running?**

```
┌─────────────────┐    ┌─────────────────┐
│   HuntForge     │    │   Dashboard     │
│   (Full Tool    │────▶   (Flask UI)   │
│    Stack)       │    │   :5000         │
└─────────────────┘    └─────────────────┘
      Docker Container
```

- **HuntForge container** (huntforge service): Runs scans, executes tools
- **Dashboard container**: Web UI to monitor scans
- Both started automatically by `setup.sh` / `setup.bat`

---

## **Common Commands**

```bash
# See running services
docker-compose ps

# View logs
docker-compose logs -f huntforge    # Main scan logs
docker-compose logs -f dashboard   # Dashboard logs

# Stop everything
docker-compose down

# Restart services
docker-compose restart

# Run scan with custom methodology
docker exec huntforge python3 huntforge.py scan example.com --methodology config/custom.yaml

# Start interactive shell in container
docker exec -it huntforge bash

# Rebuild after code changes
docker-compose build --no-cache huntforge
```

---

## **Configuration (Optional)**

### **Add API Keys for AI Features**

Edit `.env` file:
```bash
ANTHROPIC_API_KEY=your_key_here
SHODAN_API_KEY=your_key_here    # Optional, for more data
GITHUB_TOKEN=your_token_here    # Optional, higher rate limits
```

Restart services: `docker-compose restart huntforge`

### **Set Your Authorized Targets**

Edit `~/.huntforge/scope.json` (on your **host machine**):

```json
{
  "programs": {
    "My Bug Bounty Targets": {
      "in_scope": [
        "example.com",
        "*.example.com"
      ],
      "out_of_scope": [
        "admin.example.com"
      ]
    }
  }
}
```

**Important:** Only scan targets you own or have permission to test.

---

## **Troubleshooting**

### **"docker: command not found"**
→ Install Docker Desktop first: https://www.docker.com/products/docker-desktop

### **"Insufficient memory"**
→ Increase Docker memory in Settings → Resources → Memory (set to 8GB+)

### **"Permission denied" on Linux/macOS**
```bash
sudo usermod -aG docker $USER
# Log out and back in
```

### **Port 5000 already in use**
Change in `docker-compose.yml`:
```yaml
dashboard:
  ports:
    - "5001:5000"  # Use 5001 instead
```

Then access dashboard at http://localhost:5001

### **Scan seems stuck / frozen**
```bash
# Check container logs
docker-compose logs huntforge | tail -50

# Check if specific tool is hanging
docker exec huntforge ps aux

# Restart the scan (Ctrl+C to stop, then re-run)
```

---

## **What's Included?**

**25+ Security Tools:**
- Subdomain enumeration: subfinder, amass, assetfinder, findomain, theharvester, crtsh
- Live detection: httpx, dnsx, naabu, puredns
- Content discovery: katana, gau, gospider, paramspider, ffuf, dirsearch, feroxbuster
- Vulnerability scanning: nuclei, wpscan, nikto, dalfox, sqlmap
- Secrets scanning: gitleaks, trufflehog, github_dorking, jsluice, linkfinder, secretfinder
- Technology detection: whatweb, wappalyzer, nmap, shodan, censys

**Full HuntForge Framework:**
- 7-phase intelligent methodology
- Tag-driven conditional execution
- Budget tracking & scope enforcement
- Structured logging (JSONL)
- AI-generated reports (Claude/Gemini)
- Web dashboard

---

## **Uninstall**

```bash
# Stop and remove containers
docker-compose down

# Remove images (saves ~5GB)
docker rmi huntforge_kali huntforge-dashboard

# Remove HuntForge project files
cd ..
rm -rf huntforge
```

---

## **Need Help?**

- **Documentation**: See `README.md` and `implementation.md`
- **Issues**: https://github.com/HuntForgeHQ/huntforge/issues
- **Contributing**: See `CONTRIBUTING.md`

---

## **Safety First**

⚠️ **Only scan targets you own or have explicit permission to test.**

Legal targets for practice:
- `testaspnet.vulnweb.com` (ASP.NET test site)
- `testphp.vulnhub.com` (PHP test site)
- `dvwa.co.uk` (Damn Vulnerable Web App)
- `demo.testfire.net` (Test bank app)

Never point this at random websites — it's illegal in most jurisdictions.

---

**Ready to hunt?** Start with:

```bash
docker exec huntforge python3 huntforge.py scan testaspnet.vulnweb.com --profile low
```
