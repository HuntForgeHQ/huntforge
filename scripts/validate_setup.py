#!/usr/bin/env python3
"""
HuntForge Setup Validation - Native Installation

Checks:
- Python dependencies
- Installed tools (by profile)
- Configuration files
- System resources
"""

import sys
import json
import shutil
from pathlib import Path
import subprocess

# Add current directory to Python path to enable core module imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def check(description, condition, error_msg=""):
    """Print check result"""
    status = "[OK]" if condition else "[FAIL]"
    color = "\033[92m" if condition else "\033[91m"
    reset = "\033[0m"
    print(f"  {color}{status}{reset} {description}")
    if not condition and error_msg:
        print(f"         {error_msg}")
    return condition

def main():
    print("="*60)
    print("HuntForge Setup Validation")
    print("="*60)
    print()

    all_ok = True

    # 1. Python version
    print("[1] Python environment")
    py_ok = sys.version_info >= (3, 9)
    all_ok &= check(f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} (need 3.9+)",
                    py_ok, "Upgrade to Python 3.9+")
    print()

    # 2. Core modules
    print("[2] Python dependencies")
    try:
        import yaml
        import loguru
        import flask
        import requests
        import rich
        check("All core modules available", True)
    except ImportError as e:
        check("Core modules", False, f"Run: pip3 install -r requirements.txt ({e})")
        all_ok = False
    print()

    # 3. HuntForge modules
    print("[3] HuntForge core modules")
    try:
        from core.tag_manager import TagManager
        from core.orchestrator import Orchestrator
        from core.resource_aware_scheduler import AdaptiveScheduler
        check("Core modules importable", True)
    except ImportError as e:
        check("Core modules", False, f"Import error: {e}")
        all_ok = False
    print()

    # 4. Docker container status
    print("[4] Docker container (huntforge-kali)")
    docker_ok = True
    try:
        result = subprocess.run(
            ['docker', 'ps', '-q', '-f', 'name=huntforge-kali'],
            capture_output=True,
            text=True
        )
        container_running = result.returncode == 0 and bool(result.stdout.strip())
        all_ok &= check("Docker container is running", container_running,
                       "Start with: docker-compose up -d")
        docker_ok = container_running
    except FileNotFoundError:
        check("Docker", False, "Install Docker Desktop or Docker Engine")
        docker_ok = False
        all_ok = False
    print()

    # 5. Tools inside container (only if Docker is running)
    if docker_ok:
        print("[5] Security tools (inside container)")
        tools = ['subfinder', 'httpx', 'dnsx', 'nuclei', 'whatweb']
        for tool in tools:
            try:
                result = subprocess.run(
                    ['docker', 'exec', 'huntforge-kali', 'which', tool],
                    capture_output=True,
                    text=True
                )
                installed = result.returncode == 0
                all_ok &= check(f"{tool}", installed,
                               f"Install via: docker exec huntforge-kali python3 scripts/installer.py --profile lite")
            except Exception:
                all_ok = False
        print()

    # 6. Configuration
    print("[6] Configuration files")
    config_ok = True
    if not Path("~/.huntforge/scope.json").expanduser().exists():
        check("~/.huntforge/scope.json", False, "Will be created on first scan")
        config_ok = False
    else:
        check("~/.huntforge/scope.json", True)

    if not Path("config/default_methodology.yaml").exists():
        check("config/default_methodology.yaml", False, "Missing methodology file")
        config_ok = False
    else:
        check("config/default_methodology.yaml", True)

    if not Path("config/profiles/lite.yaml").exists():
        check("config/profiles/lite.yaml", False, "Missing resource profile")
        config_ok = False
    else:
        check("config/profiles/lite.yaml", True)

    all_ok &= config_ok
    print()

    # 7. System resources
    print("[7] System resources")
    try:
        import psutil
        mem = psutil.virtual_memory()
        cpu_count = psutil.cpu_count()
        print(f"  RAM: {mem.total/1024**3:.1f} GB total, {mem.available/1024**3:.1f} GB available")
        print(f"  CPU: {cpu_count} cores")
        if mem.total < 4 * 1024**3:
            print("  \033[93m[WARN] Less than 4GB RAM. Use --profile lite\033[0m")
        else:
            print("  \033[92m[OK] Sufficient RAM for bug bounty work\033[0m")
    except ImportError:
        check("psutil", False, "Install: pip3 install psutil")
        all_ok = False
    print()

    # 8. Write permissions
    print("[8] Directories")
    dirs_ok = True
    for d in ['output', 'logs', 'config']:
        path = Path(d)
        if not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
                print(f"  \033[92m✓ Created {d}/\033[0m")
            except:
                check(f"Can create {d}/", False)
                dirs_ok = False
        else:
            check(f"{d}/ exists and writable", True)
    all_ok &= dirs_ok
    print()

    # Summary
    print("="*60)
    if all_ok:
        print("\033[92m[SUCCESS] Setup is valid! Ready to scan.\033[0m")
        print("\nNext steps:")
        print("  1. Edit ~/.huntforge/scope.json with your targets")
        print("  2. Run: python3 huntforge.py scan testaspnet.vulnweb.com --profile lite")
    else:
        print("\033[91m[FAILED] Some checks failed. Fix issues above.\033[0m")
        print("\nQuick fix:")
        print("  python3 -m pip install -r requirements.txt")
        print("  python3 scripts/installer.py --profile lite")
    print("="*60)

    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
