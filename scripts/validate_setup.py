#!/usr/bin/env python3
"""
HuntForge Setup Validation - Run after setup to verify everything works
"""

import subprocess
import sys
import json
from pathlib import Path

def run_cmd(cmd):
    """Run shell command and return output"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", "timeout"
    except Exception as e:
        return False, "", str(e)

def check_docker():
    """Check if Docker is running"""
    print("[1/8] Checking Docker...")
    ok, out, err = run_cmd("docker info")
    if ok:
        print("    ✓ Docker is running")
        return True
    else:
        print("    ✗ Docker is not running or not accessible")
        print(f"    Error: {err}")
        return False

def check_services():
    """Check if Docker services are healthy"""
    print("\n[2/8] Checking HuntForge services...")
    ok, out, err = run_cmd("docker-compose ps")
    if "huntforge" in out and "Up" in out:
        print("    ✓ huntforge service is up")
    else:
        print("    ✗ huntforge service is not running")
        print("    Run: docker-compose up -d")
        return False

    ok, out, err = run_cmd("docker-compose ps")
    if "dashboard" in out and "Up" in out:
        print("    ✓ dashboard service is up")
    else:
        print("    ✗ dashboard service is not running")
        print("    Run: docker-compose up -d")
        return False
    return True

def check_tools():
    """Check if essential tools are available in container"""
    print("\n[3/8] Checking security tools...")
    tools = [
        "subfinder", "httpx", "nuclei", "katana", "ffuf",
        "sqlmap", "dalfox", "wpscan", "whatweb", "nmap"
    ]
    missing = []

    for tool in tools:
        ok, out, err = run_cmd(f"docker exec huntforge which {tool}")
        if ok and out:
            print(f"    ✓ {tool}")
        else:
            print(f"    ✗ {tool} NOT FOUND")
            missing.append(tool)

    if missing:
        print(f"\n    Missing tools: {', '.join(missing)}")
        print("    Some tools may be in different locations or need reinstallation")
        return False
    return True

def check_python_modules():
    """Check if Python modules are installed"""
    print("\n[4/8] Checking Python modules...")
    modules = [
        "yaml", "loguru", "flask", "requests", "rich"
    ]
    missing = []

    for module in modules:
        ok, out, err = run_cmd(
            f"docker exec huntforge python3 -c \"import {module}\" 2>&1"
        )
        if ok:
            print(f"    ✓ {module}")
        else:
            print(f"    ✗ {module} NOT FOUND")
            missing.append(module)

    if missing:
        print(f"\n    Missing modules: {', '.join(missing)}")
        return False
    return True

def check_huntforge_cli():
    """Test HuntForge CLI"""
    print("\n[5/8] Testing HuntForge CLI...")
    ok, out, err = run_cmd(
        "docker exec huntforge python3 huntforge.py --help"
    )
    if ok and "HuntForge" in out:
        print("    ✓ CLI responds correctly")
        return True
    else:
        print("    ✗ CLI check failed")
        print(f"    Output: {out or err}")
        return False

def check_dashboard():
    """Test dashboard accessibility"""
    print("\n[6/8] Testing Dashboard...")
    ok, out, err = run_cmd("curl -s http://localhost:5000 | head -20")
    if ok and "Flask" in out:
        print("    ✓ Dashboard is accessible at http://localhost:5000")
        return True
    else:
        print("    ✗ Dashboard not responding")
        print("    Check: docker-compose logs dashboard")
        return False

def check_directories():
    """Check if required directories exist"""
    print("\n[7/8] Checking directories...")
    dirs = ["output", "logs", "config", ".huntforge"]
    all_ok = True

    for d in dirs:
        if Path(d).exists():
            print(f"    ✓ {d}/ exists")
        else:
            print(f"    ! {d}/ missing (will be created on first scan)")

    return True

def check_scope():
    """Check if scope.json is properly configured"""
    print("\n[8/8] Checking scope configuration...")
    scope_file = Path.home() / ".huntforge" / "scope.json"

    if not scope_file.exists():
        print("    ! ~/.huntforge/scope.json not found")
        print("    It will be created on first scan with default values")
        return True

    try:
        with open(scope_file) as f:
            data = json.load(f)
        if "programs" in data:
            print("    ✓ scope.json is valid")
            return True
        else:
            print("    ✗ scope.json format is invalid")
            return False
    except Exception as e:
        print(f"    ✗ scope.json parse error: {e}")
        return False

def main():
    print("=" * 50)
    print("  HuntForge Setup Validation")
    print("=" * 50)
    print()

    results = []
    results.append(("Docker", check_docker()))
    results.append(("Services", check_services()))
    results.append(("Tools", check_tools()))
    results.append(("Python Modules", check_python_modules()))
    results.append(("CLI", check_huntforge_cli()))
    results.append(("Dashboard", check_dashboard()))
    results.append(("Directories", check_directories()))
    results.append(("Scope", check_scope()))

    print("\n" + "=" * 50)
    print("  Summary")
    print("=" * 50)

    passed = sum(1 for _, ok in results if ok)
    total = len(results)

    for name, ok in results:
        status = "✓ PASS" if ok else "✗ FAIL"
        print(f"  {status:8} {name}")

    print()
    print(f"  Score: {passed}/{total} ({100*passed//total}%)")
    print()

    if passed == total:
        print("  ✓ Setup is complete and working!")
        print()
        print("  Next: Run your first scan")
        print("    docker exec huntforge python3 huntforge.py scan testaspnet.vulnweb.com --profile low")
        sys.exit(0)
    else:
        print("  ✗ Some checks failed. Review the errors above.")
        print()
        print("  Common fixes:")
        print("    - Docker Desktop: Make sure it's running")
        print("    - Rebuild: docker-compose build --no-cache huntforge")
        print("    - View logs: docker-compose logs -f")
        sys.exit(1)

if __name__ == "__main__":
    main()
