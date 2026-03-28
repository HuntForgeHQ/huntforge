<div align="center">
  <h1>⚡ HuntForge</h1>
  <p><b>AI-Powered Bug Bounty Recon Framework</b></p>
  <p>
    <a href="https://github.com/HuntForgeHQ/huntforge/issues"><img alt="Issues" src="https://img.shields.io/github/issues/HuntForgeHQ/huntforge"></a>
    <a href="https://github.com/HuntForgeHQ/huntforge/stargazers"><img alt="Stars" src="https://img.shields.io/github/stars/HuntForgeHQ/huntforge"></a>
    <a href="LICENSE"><img alt="License" src="https://img.shields.io/github/license/HuntForgeHQ/huntforge"></a>
  </p>
</div>

<br/>

## **Quick Start (2 Commands)**

```bash
# 1. Clone and setup
git clone https://github.com/HuntForgeHQ/huntforge.git && cd huntforge
bash setup.sh          # Linux/macOS
# or setup.bat         # Windows

# 2. Run first scan
docker exec huntforge python3 huntforge.py scan testaspnet.vulnweb.com --profile low

# 3. Open dashboard
open http://localhost:5000
```

**That's it.** No manual tool installation, no dependency hell. Everything runs in Docker.

---

## **What You Get**

- ✅ **25+ security tools** pre-installed (subfinder, nuclei, httpx, sqlmap, ffuf, etc.)
- ✅ **7-phase intelligent methodology** - runs right tools at right time
- ✅ **Web dashboard** - monitor scans live in browser
- ✅ **AI-powered reports** - Claude/Gemini generates findings summaries
- ✅ **Tag-driven** - conditional execution based on what's found
- ✅ **Budget & scope** controls to prevent costs and legal issues
- ✅ **Works on any OS** with Docker (Windows, macOS, Linux)

---

## **See It In Action**

```bash
# After setup, run:
make test          # Quick test scan (10-30 min)
# or
make test-full     # Full 7-phase scan (1-2 hours)

# Open dashboard: http://localhost:5000
```

---

## **Need Details?**

- **[Quick Start Guide](QUICKSTART.md)** - Complete walkthrough with troubleshooting
- **[Full Documentation](implementation.md)** - Architecture, configuration, customization
- **[Contributing](CONTRIBUTING.md)** - Help improve HuntForge

---

## **Requirements**

- Docker Desktop (or Docker Engine) - https://www.docker.com/products/docker-desktop
- 4GB RAM minimum, 8GB recommended
- 20GB disk space

---

## **Safety**

⚠️ **Only scan targets you own or have permission to test.**

Practice on authorized targets:
- `testaspnet.vulnweb.com` (ASP.NET test site)
- `testphp.vulnhub.com` (PHP test site)
- `dvwa.co.uk` (Damn Vulnerable Web App)

---

## **Common Commands**

```bash
make start          # Start services
make stop           # Stop services
make logs           # View scan logs
make shell          # Enter container shell
make status         # Show running services
make help           # Show all commands
```

See `QUICKSTART.md` for full command reference.

---

**Questions?** Open an issue: https://github.com/HuntForgeHQ/huntforge/issues

Happy hunting! 🎯
