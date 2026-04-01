# Contributing to HuntForge

Thank you for your interest in contributing! This guide will help you understand our process and standards.

---

## 📋 Table of Contents

- [Code of Conduct](#-code-of-conduct)
- [Getting Started](#-getting-started)
- [Development Workflow](#-development-workflow)
- [Adding New Tool Modules](#-adding-new-tool-modules)
- [Code Standards](#-code-standards)
- [Testing](#-testing)
- [Pull Request Process](#-pull-request-process)
- [Commit Guidelines](#-commit-guidelines)
- [Community](#-community)

---

## 📜 Code of Conduct

This project adheres to the [Contributor Covenant](https://www.contributor-covenant.org/). By participating, you are expected to:

- ✅ Be respectful and inclusive
- ✅ Welcome newcomers and help them get started
- ✅ Focus on constructive feedback
- ✅ Accept responsibility and apologize for mistakes

**Harassment or discrimination of any kind is unacceptable.**

Report violations to: [security@huntforge.dev](mailto:security@huntforge.dev)

---

## 🚀 Getting Started

### 1. Fork & Clone

```bash
# Fork the repo on GitHub, then:
git clone https://github.com/YOUR_USERNAME/huntforge.git
cd huntforge
git remote add upstream https://github.com/huntforge/huntforge.git
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate          # Linux/Mac
venv\Scripts\activate             # Windows

# Install dependencies
pip install -r requirements.txt

# Install pre-commit hooks
pip install pre-commit
pre-commit install
```

### 3. Build Docker Image (Optional but Recommended)

```bash
docker compose build
docker compose up -d
```

### 4. Verify Setup

```bash
# Run smoke test (quick scan)
python3 scripts/smoke_test.sh

# Should complete without errors
```

---

## 🔄 Development Workflow

### Branch Strategy

- **`main`** — stable, production-ready code
- **`develop`** — integration branch for features
- **`feature/xxx`** — new features
- **`fix/xxx`** — bug fixes
- **`docs/xxx`** — documentation updates
- **`tool/xxx`** — new tool modules

```bash
# Start from latest develop
git checkout develop
git pull upstream develop

# Create feature branch
git checkout -b feature/amazing-feature
```

### Daily Sync with Upstream

```bash
git fetch upstream
git rebase upstream/develop
# Resolve conflicts if any
```

---

## 📦 Adding New Tool Modules

This is the most common contribution. Follow these steps:

### Step 1: Choose the Right Category

Place your module in the appropriate directory:

| Phase | Directory | Examples |
|-------|-----------|----------|
| Passive Recon | `modules/passive/` | subfinder.py, amass.py |
| Secrets | `modules/secrets/` | gitleaks.py, trufflehog.py |
| Discovery | `modules/discovery/` | httpx.py, naabu.py |
| Surface Intel | `modules/surface_intel/` | whatweb.py, wappalyzer.py |
| Enumeration | `modules/enumeration/` | katana.py, gau.py |
| Content Discovery | `modules/content_discovery/` | ffuf.py, dirsearch.py |
| Vuln Scan | `modules/vuln_scan/` | nuclei.py, sqlmap.py |

### Step 2: Implement the Module

Create `modules/vuln_scan/mytool.py`:

```python
"""
MyTool Module - Vulnerability scanner for XSS

Author: Your Name
Module: vuln_scan
Tool: mytool
"""

import os
import json
from modules.base_module import BaseModule
from core.exceptions import OutputParseError


class MyToolModule(BaseModule):
    """MyTool vulnerability scanner integration."""

    def build_command(self, target: str, output_file: str) -> list:
        """
        Build the command to run inside Docker container.

        Args:
            target: Domain being scanned
            output_file: Container path for output

        Returns:
            List of command arguments
        """
        return [
            'mytool',
            '-d', target,
            '-o', output_file,
            '-json',
            '-threads', str(self._cfg('threads', default=10))
        ]

    def run(self, target: str, output_dir: str, tag_manager, config: dict = None) -> dict:
        """
        Execute the tool and parse results.

        Args:
            target: Domain to scan
            output_dir: Host output directory (output/domain/)
            tag_manager: shared TagManager instance
            config: Tool configuration from YAML

        Returns:
            {
                'results': [...],           # List of findings
                'count': 15,               # Number of findings
                'requests_made': 250,      # HTTP requests made
                'metadata': {...}          # Optional extra data
            }
        """
        self.config = config or {}

        # Setup output path
        host_output = os.path.join(output_dir, 'raw', 'mytool.json')
        container_output = host_output.replace('\\', '/')
        os.makedirs(os.path.dirname(host_output), exist_ok=True)

        # Execute
        command = self.build_command(target, container_output)
        self._run_subprocess(command)

        # Parse results
        try:
            with open(host_output, 'r') as f:
                data = json.load(f)

            results = self._parse_results(data)
        except FileNotFoundError:
            raise OutputParseError(
                f"Tool produced no output: {host_output}",
                tool='mytool'
            )

        return {
            'results': results,
            'count': len(results),
            'requests_made': self._parse_request_count(data),
        }

    def emit_tags(self, result: dict, tag_manager) -> None:
        """
        Set tags based on tool output.

        Args:
            result: Return value from run()
            tag_manager: Shared TagManager to update
        """
        if result['count'] == 0:
            return

        # Set XSS found tag
        tag_manager.add(
            tag='xss_found',
            confidence='high' if result['count'] > 5 else 'medium',
            evidence=[r['url'] for r in result['results'][:3]],
            source='mytool'
        )

    def estimated_requests(self) -> int:
        """
        Estimated HTTP requests for budget planning.

        Returns:
            Integer count of expected requests
        """
        # Estimate based on subdomain count if available
        # Or return conservative default
        return 200

    # ──────────────────────────────────────────────────────────────
    # Private helper methods (custom to your module)
    # ──────────────────────────────────────────────────────────────

    def _parse_results(self, data: dict) -> list:
        """Parse tool-specific JSON format into standardized list."""
        findings = []

        for item in data.get('findings', []):
            findings.append({
                'url': item.get('url'),
                'param': item.get('param'),
                'payload': item.get('payload'),
                'severity': item.get('severity', 'medium'),
            })

        return findings

    def _parse_request_count(self, data: dict) -> int:
        """Extract request count from tool metadata."""
        return data.get('stats', {}).get('requests', 100)
```

### Step 3: Add Tool Profile

Edit `data/tool_profiles.yaml`:

```yaml
mytool:
  phase: "phase_7_vuln_scan"
  phase_weight: "medium"          # light | medium | heavy
  base_memory_mb: 300             # Typical RAM usage
  base_cpu_cores: 0.8             # CPU cores needed
  scalable_params:
    threads:
      value: 10                   # Default threads
      memory_per_unit_mb: 20      # RAM per additional thread
      cpu_per_unit: 0.1           # CPU per additional thread
      min: 1
      max: 50
    timeout:
      value: 300
      memory_per_unit_mb: 0
      min: 60
      max: 1800
  estimated_time_min: 20          # Typical duration
```

**How to determine values:**
- Run tool with `time` command, monitor `htop`
- `base_memory_mb`: Resident Set Size (RSS) in MB
- `base_cpu_cores`: CPU% / 100 during steady state
- `estimated_time_min`: Wall clock time for typical target

### Step 4: Register in Orchestrator

Edit `core/orchestrator_v2.py`:

```python
# Import at top (with other phase 7 imports)
from modules.vuln_scan.mytool import MyToolModule as MyTool

# Add to TOOL_REGISTRY
TOOL_REGISTRY = {
    # ... existing tools
    'mytool': MyTool,
}
```

### Step 5: Add to Methodology

Edit `config/default_methodology.yaml`:

```yaml
phase_7_vuln_scan:
  # ... existing config

  conditional_tools:
    # ... existing tools

    - tool: mytool
      always: false
      if_tag: "params_found"      # Only run if parameters discovered
      binary: "mytool"
      weight: medium
      timeout: 600
      output_file: "raw/mytool.json"
      default_flags: "-d {domain} -o {output_file} -json"
      extra_args: ""
      config:
        threads: 10
        severity: "high,critical"
```

### Step 6: Write Tests

Create `tests/modules/vuln_scan/test_mytool.py`:

```python
import pytest
from modules.vuln_scan.mytool import MyToolModule
from core.tag_manager import TagManager


def test_mytool_parse_results():
    """Test parsing of tool-specific output format."""
    module = MyToolModule()

    sample_data = {
        "findings": [
            {"url": "https://example.com/search?q=<script>", "severity": "high"}
        ]
    }

    results = module._parse_results(sample_data)

    assert len(results) == 1
    assert results[0]['url'] == "https://example.com/search?q=<script>"
    assert results[0]['severity'] == "high"


def test_mytool_tag_emission():
    """Test that tags are set correctly."""
    tag_manager = TagManager()
    module = MyToolModule()

    result = {
        'results': [
            {'url': 'https://example.com/test', 'severity': 'high'}
        ],
        'count': 1
    }

    module.emit_tags(result, tag_manager)

    assert tag_manager.has('xss_found')
    assert tag_manager.get('xss_found')['confidence'] == 'high'


def test_mytool_command_building():
    """Test command construction with config."""
    module = MyToolModule()
    module.config = {'threads': 20}

    cmd = module.build_command('example.com', '/tmp/out.json')

    assert 'mytool' in cmd
    assert '-d' in cmd and 'example.com' in cmd
    assert '-threads' in cmd and '20' in cmd
```

Run the test:

```bash
pytest tests/modules/vuln_scan/test_mytool.py -v
```

### Step 7: Submit Pull Request

```bash
git add .
git commit -m "feat: add mytool vulnerability scanner"
git push origin feature/mytool
```

Open PR against `huntforge:develop` branch.

---

## 📏 Code Standards

We use **PEP 8** with modifications. Auto-format with `black`:

```bash
black .
```

### Linting

```bash
flake8 huntforge/           # Style guide enforcement
mypy huntforge/            # Type checking (optional but encouraged)
```

### Type Hints

**Add type hints for all public methods:**

```python
from typing import List, Dict, Optional

def build_command(self, target: str, output_file: str) -> List[str]:
    ...

def run(self, target: str, output_dir: str,
        tag_manager, config: Optional[dict] = None) -> dict:
    ...
```

### Docstrings

Use **Google style** docstrings:

```python
def method_name(self, param1: str, param2: int) -> bool:
    """Short description of method.

    Longer description if needed, explaining the purpose
    and any edge cases.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Boolean indicating success/failure

    Raises:
        ValueError: If param1 is empty
    """
```

---

## 🧪 Testing

### Run All Tests

```bash
# Unit tests only (fast)
pytest tests/unit/ -v

# Integration tests (requires Docker)
pytest tests/integration/ -v --docker

# With coverage
pytest -v --cov=huntforge --cov-report=html
```

### Test Categories

| Type | Location | Description |
|------|----------|-------------|
| **Unit** | `tests/unit/` | Test individual modules in isolation |
| **Integration** | `tests/integration/` | Full scan against test domain |
| **Smoke** | `scripts/smoke_test.sh` | Quick sanity check |
| **Performance** | `tests/performance/` | Benchmark against baselines |

### Writing Tests

**Good test:**
```python
def test_subfinder_parse_empty_output():
    """Empty output should return empty list, not crash."""
    module = SubfinderModule()
    results = module._parse("")
    assert results == []
```

**Bad test:**
```python
def test_subfinder():
    """Test subfinder"""  # Vague description
    # Test does multiple things
    # No assertions clarity
```

---

## 🔀 Pull Request Process

### Before Submitting

1. ✅ **Rebase on latest develop**
   ```bash
   git fetch upstream
   git rebase upstream/develop
   ```

2. ✅ **Run all tests locally**
   ```bash
   pytest -v
   ```

3. ✅ **Run linter**
   ```bash
   black . && flake8
   ```

4. ✅ **Update documentation**
   - Add/update comments
   - Update README if user-facing changes
   - Add examples if new feature

5. ✅ **Check git history**
   ```bash
   git log --oneline develop..HEAD
   # Should be clean, logical commits
   ```

### PR Template

Fill this out when opening PR:

```markdown
## Description
[What does this PR do?]

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
[pytest output, manual test results]

## Screenshots/Demo
[If UI changes, attach screenshot]

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] No lint errors (black, flake8)
- [ ] Works on lite, medium, full profiles
- [ ] No hardcoded paths or secrets
```

### Review Process

1. **Automated checks** run (CI/CD):
   - Build Docker image
   - Run test suite
   - Lint code
   - Security scan

2. **Maintainer review** (within 3 days):
   - Code quality
   - Architecture consistency
   - Performance impact
   - Security considerations

3. **Changes requested?** Address them:
   ```bash
   git commit -m "fix: address review feedback"
   git push -f origin feature/xxx
   ```

4. **Approval + Squash + Merge**
   - PR will be squashed into single commit
   - Commit message will follow [Conventional Commits](#commit-guidelines)

---

## 📝 Commit Guidelines

We follow **[Conventional Commits](https://www.conventionalcommits.org/)**.

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

| Type | When to Use |
|------|-------------|
| `feat` | New feature (user-facing) |
| `fix` | Bug fix (user-facing) |
| `docs` | Documentation only |
| `style` | Formatting, missing semicolons (no code change) |
| `refactor` | Code restructuring (no feature/fix) |
| `perf` | Performance improvement |
| `test` | Adding or fixing tests |
| `chore` | Build process, tooling, CI |
| `ci` | Changes to CI configuration |
| `revert` | Revert previous commit |

### Examples

```bash
# Good
git commit -m "feat(modules): add nuclei template categorization"

git commit -m "fix(orchestrator): handle null tag_manager in checkpoint load"

git commit -m "docs(README): add architecture diagram for Phase 4"

git commit -m "refactor(scheduler): extract resource estimation logic"

# Bad
git commit -m "updated stuff"
git commit -m "fixed bug"
```

### Scopes

Use these standardized scopes:

- `modules` — tool modules (subfinder, nuclei, etc.)
- `orchestrator` — main execution engine
- `scheduler` — resource-aware scheduling
- `tag_manager` — intelligence system
- `docker_runner` — container execution
- `config` — YAML configurations
- `profiles` — resource profiles
- `dashboard` — web UI
- `ai` — AI integration
- `docs` — documentation
- `tests` — test suite

---

## 🎯 Areas for Contribution

### High Priority

1. **Missing Tool Modules** — see `TOOL_REGISTRY` gaps in orchestrator_v2.py
2. **Tool Profiles** — empirical measurements in `data/tool_profiles.yaml`
3. **Dashboard Enhancements** — real-time updates, charts, exports
4. **AI Report Prompts** — improve Gemini/Claude prompts
5. **Windows Support** — enable Docker-free mode on Windows

### Medium Priority

6. **Performance Optimization** — reduce memory footprint
7. **Error Handling** — better recovery from tool failures
8. **Test Coverage** — aim for 80%+ coverage
9. **CI/CD Pipeline** — automated Docker builds, releases
10. **Documentation** — tutorials, video walkthroughs

### Low Priority / Good First Issues

11. **Wordlist Updates** — modern directory/parameter wordlists
12. **Configuration Validation** — schema validation for YAML
13. **Log Formatting** — improved log output, colors
14. **Template Improvements** — CHANGELOG, PR templates

---

## 🏗️ Project Structure

```
huntforge/
├── core/                    # Framework core
│   ├── orchestrator_v2.py      ⭐ Main
│   ├── resource_aware_scheduler.py
│   ├── tag_manager.py
│   ├── scope_enforcer.py
│   ├── budget_tracker.py
│   ├── hf_logger.py
│   ├── docker_runner.py
│   ├── exceptions.py
│   └── base_module.py          ⭐ Inherit from this
│
├── modules/                 # Tool integrations (30+)
│   ├── passive/
│   ├── secrets/
│   ├── discovery/
│   ├── surface_intel/
│   ├── enumeration/
│   ├── content_discovery/
│   └── vuln_scan/
│
├── ai/                      # AI integration
│   ├── methodology_engine.py   # Ollama + fallback
│   └── report_generator.py     # Gemini API
│
├── config/                  # YAML configurations
│   ├── default_methodology.yaml ⭐ Master config
│   ├── smoke_test_methodology.yaml
│   └── profiles/
│       ├── lite.yaml
│       ├── medium.yaml         ⭐ Default
│       └── full.yaml
│
├── data/                    # Static data
│   ├── tool_profiles.yaml      ⭐ Resource profiles
│   ├── tool_fingerprints.json
│   └── bug_bounty_scopes.json
│
├── scripts/                 # Utilities
│   ├── installer.py
│   ├── validate_setup.py
│   └── smoke_test.sh
│
├── dashboard/               # Flask web UI
│   ├── app.py
│   └── templates/
│
├── tests/                   # Test suite
│   ├── unit/
│   └── integration/
│
├── output/                  # Generated (gitignored)
├── logs/                    # Generated (gitignored)
├── .env.example            # Environment template
├── requirements.txt
├── Dockerfile.kali
├── docker-compose.yml
├── huntforge.py            # CLI entry point ⭐
├── README.md               ⭐ Start here
└── CONTRIBUTING.md         ⭐ You are here
```

**⭐ Key files to understand first**

---

## 🐛 Bug Reports

Found a bug? Help us fix it!

### Before Filing

1. **Search existing issues** — maybe it's already known
2. **Check troubleshooting guide** — might have quick fix
3. **Test with latest code** — bug might already be fixed

### Issue Template

```markdown
## Description
[Clear description of bug]

## Steps to Reproduce
1. [First step]
2. [Second step]
3. [Expected vs actual]

## Environment
- OS: [e.g., Ubuntu 22.04]
- HuntForge version: [git commit or tag]
- Profile: [lite/medium/full]
- Docker: [yes/no]
- Python version:

## Logs
[Attach relevant log snippets, ERROR lines]

## Expected Behavior
[What should happen]

## Additional Context
[Screenshots, context, anything else]
```

**Bugs with clear reproduction steps get fixed fastest.**

---

## 💡 Feature Requests

Want a new feature? Tell us!

### Before Suggesting

1. **Check roadmap** — maybe it's planned
2. **Search existing requests** — avoid duplicates
3. **Think about scope** — is it general-purpose?

### Feature Request Template

```markdown
## Problem
[What pain point does this solve?]

## Proposed Solution
[Describe the feature, how it would work]

## Alternatives Considered
[What else did you think about?]

## Use Case
[Who benefits? How would they use it?]

## Similar Tools
[Do other tools do this? How can we improve?]
```

---

## 🎉 Recognition

Contributors are recognized in:

- [CONTRIBUTORS.md](CONTRIBUTORS.md) — alphabetical list
- Release notes — your name in each release you contribute to
- GitHub's contributor graph — green squares forever!

**Special contributors** receive:
- Early access to new features
- Direct line to maintainers
- Swag (stickers, t-shirts) at conferences

---

## ❓ Questions?

- **General:** [GitHub Discussions](https://github.com/yourusername/huntforge/discussions)
- **Private:** [security@huntforge.dev](mailto:security@huntforge.dev)
- **Security vulnerabilities:** Report via [responsible disclosure](SECURITY.md)

---

## 📚 Additional Resources

| Resource | Purpose |
|----------|---------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Deep dive into system design |
| [CONFIG_GUIDE.md](CONFIG_GUIDE.md) | Complete YAML reference |
| [MODULE_DEVELOPMENT.md](MODULE_DEVELOPMENT.md) | Extended module guide |
| [PERFORMANCE_TUNING.md](PERFORMANCE_TUNING.md) | Optimization tips |
| [SECURITY.md](SECURITY.md) | Vulnerability disclosure |

---

**Thank you for contributing! The bug bounty community thrives on collaboration.**

---

*Last updated: April 2026*  
*Maintained by: HuntForge Core Team*
