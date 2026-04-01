# Contributing to HuntForge

Thank you for your interest in contributing to HuntForge! This guide will help you get started.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment Setup](#development-environment-setup)
- [Workflow](#workflow)
- [Adding a New Tool Module](#adding-a-new-tool-module)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Community](#community)

---

## Code of Conduct

HuntForge is an inclusive, respectful community. By participating, you agree to:

- Be respectful and welcoming
- Accept constructive feedback
- Focus on what's best for the community
- Show empathy towards others

Harassment or discrimination of any kind will not be tolerated.

---

## Getting Started

### Finding Something to Work On

1. **Browse open issues**: Check the [GitHub Issues](https://github.com/HuntForgeHQ/huntforge/issues) page
   - Labeled `good-first-issue` - perfect for newcomers
   - Labeled `help-wanted` - needs community assistance
   - Labeled `bug` - something that needs fixing

2. **Check the roadmap**: See [README.md](README.md#roadmap) for planned features

3. **Join discussions**: Open a [GitHub Discussion](https://github.com/HuntForgeHQ/huntforge/discussions) to ask questions or propose ideas

4. **Review implementation.md**: Understand the team structure and architecture

### Before You Start

- **Comment on the issue** to claim it (prevents duplicate work)
- **Ask questions** if anything is unclear
- **Ensure the issue is actionable** - if not, we'll help refine it

---

## Development Environment Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOURUSERNAME/huntforge.git
cd huntforge

# Add upstream remote
git remote add upstream https://github.com/HuntForgeHQ/huntforge.git
```

### 2. Create Virtual Environment

```bash
# Create Python virtual environment
python3 -m venv venv

# Activate it
# Linux/macOS:
source venv/bin/activate
# Windows (PowerShell):
venv\Scripts\Activate.ps1

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install black pylint pytest pytest-cov  # Development tools
```

### 3. Start Docker Container

```bash
# Build and start Kali container
docker-compose up -d

# Wait for it to be ready
docker ps | grep huntforge-kali

# Install tools (if not already)
docker exec huntforge-kali python3 scripts/installer.py --profile lite
```

### 4. Verify Setup

```bash
# Check Python syntax
python3 -m py_compile huntforge.py

# Test core imports
python3 -c "
from core.tag_manager import TagManager
from core.orchestrator_v2 import OrchestratorV2
print('Development environment OK')
"

# Run test scan (dry-run mode if available)
python3 huntforge.py --help
```

---

## Workflow

### Branch Strategy

- **`main`**: Stable production code (protected)
- **`feature/your-feature-name`**: Your development branch
- **`fix/issue-description`**: Bug fix branches

**Never push directly to `main`**. All changes via Pull Request.

### Daily Workflow

```bash
# 1. Sync with upstream
git checkout main
git pull upstream main
git checkout -b feature/your-feature

# 2. Make changes
# ... edit code ...

# 3. Check syntax
python3 -m py_compile **/*.py

# 4. Run tests (if any)
pytest tests/ -v

# 5. Commit with conventional commit message
git add .
git commit -m "feat(tag-manager): add tag expiration support"

# 6. Push to your fork
git push origin feature/your-feature

# 7. Open PR on GitHub
#    - Base: HuntForgeHQ/main
#    - Compare: YOURUSERNAME/feature/your-feature
```

### Keeping Your Branch Updated

```bash
# If upstream/main has changed, rebase your branch
git checkout feature/your-feature
git fetch upstream
git rebase upstream/main
# Resolve any conflicts, then:
git push -f origin feature/your-feature  # Force push after rebase
```

---

## Adding a New Tool Module

HuntForge's modular architecture makes adding new tools straightforward.

### Step-by-Step Guide

#### 1. Choose the Right Phase

Place your tool in the appropriate category:

| Phase | Directory | Purpose |
|-------|-----------|---------|
| 1 | `modules/passive/` | Passive reconnaissance (no target contact) |
| 2 | `modules/secrets/` | Secret/credential scanning |
| 3 | `modules/discovery/` | Asset discovery and probing |
| 4 | `modules/surface_intel/` | Technology fingerprinting |
| 5 | `modules/enumeration/` | Endpoint and parameter enumeration |
| 6 | `modules/content_discovery/` | Directory/file discovery |
| 7 | `modules/vuln_scan/` | Active vulnerability scanning |

#### 2. Create Module File

Create `modules/{category}/{toolname}.py`:

```python
"""
{ToolName} Module

Responsibility: Brief description of what this tool does
Inherits from: BaseModule
Raises: Specific custom exceptions
"""
import os
from modules.base_module import BaseModule
from core.exceptions import OutputParseError

class {Toolname}Module(BaseModule):
    """
    Wrapper for {Toolname} security scanner.

    Attributes:
        name (str): Tool identifier - must match YAML config key
        phase (int): Default phase number - can be overridden in YAML
    """

    def build_command(self, target: str, container_output_file: str) -> list:
        """
        Build shell command to run inside Docker container.

        Args:
            target: Domain to scan (e.g., 'example.com')
            container_output_file: Path inside container for output

        Returns:
            list: Command as array of strings for subprocess

        Example:
            return ['{toolname}', '-d', target, '-o', container_output_file]
        """
        return [
            '{toolname}',
            '-d', target,
            '-o', container_output_file,
            '-silent'
        ]

    def run(self, target: str, output_dir: str,
            tag_manager, config: dict = None) -> dict:
        """
        Execute tool and return standardized result dictionary.

        Args:
            target: Domain to scan
            output_dir: Base output path (e.g., 'output/example.com')
            tag_manager: TagManager instance for tag operations
            config: Optional YAML configuration overrides

        Returns:
            dict: Must contain:
                - 'results': list of findings
                - 'count': int count of findings
                - 'requests_made': estimated HTTP requests
        """
        self.config = config or {}

        # Setup paths
        host_output_file = os.path.join(output_dir, 'raw', '{toolname}.txt')
        container_output_file = host_output_file.replace('\\', '/')
        os.makedirs(os.path.dirname(host_output_file), exist_ok=True)

        # Build and run command
        command = self.build_command(target, container_output_file)
        self._run_subprocess(command)  # Raises BinaryNotFoundError, ToolTimeoutError, etc.

        # Parse output
        try:
            content = self._read_output_file(host_output_file)
            results = self._parse(content)
        except Exception as e:
            raise OutputParseError(f"Failed to parse {self.__class__.__name__} output: {e}")

        return {
            'results': results,
            'count': len(results),
            'requests_made': self.estimated_requests()
        }

    def emit_tags(self, result: dict, tag_manager) -> None:
        """
        Set tags on tag_manager based on tool results.

        Only override if tool produces actionable intelligence for other phases.

        Args:
            result: The return dict from run()
            tag_manager: TagManager instance to add tags to
        """
        if result['count'] == 0:
            return

        # Example: Set a tag based on findings
        tag_manager.add(
            'has_{toolname}_findings',
            confidence='medium',
            evidence=result['results'][:3],
            source='{toolname}'
        )

    def estimated_requests(self) -> int:
        """
        Return estimated HTTP requests this tool will make.
        Used by BudgetTracker for pre-execution gatekeeping.

        Returns:
            int: Estimated request count
        """
        return 100  # Adjust based on tool behavior

    def _parse(self, content: str) -> list:
        """Parse raw tool output into list of findings."""
        return [
            line.strip()
            for line in content.splitlines()
            if line.strip()
        ]
```

#### 3. Register in Orchestrator

Add to `orchestrator_v2.py`:

```python
# At top with other imports:
from modules.{category}.{toolname} import {Toolname}Module as {ToolnameCap}

# Add to TOOL_REGISTRY dict:
TOOL_REGISTRY = {
    # ... existing tools ...
    '{toolname}': {ToolnameCap},  # Add with proper alphabetical sorting
}
```

#### 4. Add Resource Profile

Add entry to `data/tool_profiles.yaml`:

```yaml
{toolname}:
  phase: "phase_{n}_{name}"  # Match phase from orchestrator_v2.py
  phase_weight: "light"      # or "medium", "heavy"
  base_memory_mb: 150        # Estimate base RAM usage
  base_cpu_cores: 0.5        # CPU cores required
  scalable_params:
    threads:
      value: 10              # Default value
      memory_per_unit_mb: 5   # RAM per thread unit
      cpu_per_unit: 0.1       # CPU per thread
      min: 1
      max: 50
  estimated_time_min: 15      # Expected runtime on typical target
  category: "{category}"
```

Adjust values based on tool characteristics. Start conservative (high memory estimate) to avoid OOM.

#### 5. Add to Methodology

Edit `config/default_methodology.yaml`:

```yaml
  phase_{n}_{name}:
    label: "Phase Name"
    description: "Brief description"
    parallel: true
    weight: medium

    tools:
      {toolname}:
        enabled: true
        timeout: 300
        extra_args: ""  # Additional flags
        config:
          threads: 20
```

#### 6. Add Tests

Create `tests/test_{toolname}.py`:

```python
import pytest
from modules.{category}.{toolname} import {Toolname}Module

def test_{toolname}_command_build():
    module = {Toolname}Module()
    cmd = module.build_command("example.com", "/tmp/output.txt")
    assert cmd[0] == "{toolname}"
    assert "-d" in cmd
    assert "example.com" in cmd

def test_{toolname}_parse():
    module = {Toolname}Module()
    content = "finding1\nfinding2\n"
    results = module._parse(content)
    assert len(results) == 2
```

Run tests:

```bash
pytest tests/test_{toolname}.py -v
```

#### 7. Documentation

- Add docstring to class (see examples)
- Update `README.md` Phase section if needed
- Add tool to `docs/tool-reference.md` (if exists)
- Include example output format in comments

---

## Code Standards

### Python Style

- **Format**: Use `black` (default line length 88)
  ```bash
  black . --check  # Verify
  black .          # Apply
  ```

- **Linting**: Use `pylint` or `flake8`
  ```bash
  pylint modules/your_module.py
  ```

- **Type hints**: Use for all function signatures
  ```python
  def run(self, target: str, output_dir: str) -> dict:
  ```

- **Docstrings**: Google style
  ```python
  def function(param: str) -> bool:
      """Short description.

      Longer description if needed.

      Args:
          param: Parameter description

      Returns:
          bool: Return value description
      """
  ```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

**Examples**:

```
feat(modules): add nuclei template-based vuln scanner

- Implements NucleiModule with template loading
- Adds emit_tags() for CVE and technology detection
- Includes resource profile (heavy, 500MB)
- Closes #45

fix(orchestrator): handle None tag_manager in budget tracker

The budget tracker expects a TagManager but previous code
could pass None during initialization. Added None check.

Refs: #78
```

```
docs(readme): update installation guide for WSL2

Added detailed Windows/WSL2 instructions since many users
were confused about Docker path issues. Included troubleshooting
for common permission errors.
```

### What to Avoid

- ❌ Don't commit secrets, API keys, passwords (use `.env` and add to `.gitignore`)
- ❌ Don't commit large output files or wordlists (add to `.gitignore`)
- ❌ Don't modify core interfaces without discussion (TagManager, BaseModule signatures)
- ❌ Don't push to `main` branch
- ❌ Don't leave debug `print()` statements

---

## Testing

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific file
pytest tests/test_tag_manager.py -v

# With coverage
pytest tests/ --cov=core --cov=modules --cov-report=html

# Open htmlcov/index.html to see coverage report
```

### Test Coverage Goals

- Core components: >80%
- Tool modules: >60%
- Integration: >40%

**New code should include tests**. At minimum:
- Unit tests for your class
- Mocked subprocess tests (don't actually run tools)
- Integration test if it affects multi-module workflow

### Example Test Pattern

```python
import pytest
from unittest.mock import Mock, patch
from modules.passive.subfinder import SubfinderModule

def test_subfinder_emits_tags():
    """Test that subfinder sets tags correctly."""
    # Arrange
    module = SubfinderModule()
    mock_tag_manager = Mock()
    result = {
        'results': ['sub1.example.com', 'sub2.example.com'],
        'count': 2
    }

    # Act
    module.emit_tags(result, mock_tag_manager)

    # Assert
    assert mock_tag_manager.add.called
    call_args = mock_tag_manager.add.call_args
    assert call_args[0][0] == 'has_subdomains'
    assert call_args[1]['confidence'] == 'high'
```

---

## Submitting Changes

### Pull Request Checklist

Before submitting PR:

- [ ] Code follows style guide (`black`, type hints, docstrings)
- [ ] Tests added/updated and passing (`pytest`)
- [ ] No lint errors (`pylint`)
- [ ] Commit messages follow conventional format
- [ ] Branch is up-to-date with `upstream/main`
- [ ] `PR Title` is concise and descriptive
- [ ] `PR Description` includes:
  - What changed and why
  - Screenshots (if UI changes)
  - Test instructions (if needed)
  - Link to related issue
- [ ] Code is well-commented (explain why, not what)
- [ ] No secrets or hardcoded credentials

### PR Template

Fill this out in PR description:

```markdown
## Description
[Describe changes]

## Related Issue
Closes #123

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## How to Test
```bash
# Steps to verify changes
python3 huntforge.py scan testaspnet.vulnweb.com --profile lite
```

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Code follows standards
```

### Review Process

1. **Automated checks** run (lint, tests, security scan)
2. **Maintainer review** - at least 1 maintainer must approve
3. **Address feedback** - make requested changes
4. **Squash merge** - PRs merged with "Squash and merge"

**Typical review time**: 2-7 days depending on complexity.

---

## Community

### Getting Help

- **Documentation**: Read [README.md](README.md) first
- **Issues**: Search existing [issues](https://github.com/HuntForgeHQ/huntforge/issues)
- **Discussions**: Ask in [GitHub Discussions](https://github.com/HuntForgeHQ/huntforge/discussions)
- **Chat**: Join our Discord (link in README badge)

### Reporting Bugs

Open an issue with:

```markdown
## Bug Description
[Clear description]

## Steps to Reproduce
1. [First step]
2. [Second step]

## Expected Behavior
[What should happen]

## Actual Behavior
[What actually happens]

## Environment
- OS: [e.g., Ubuntu 22.04]
- Python: [e.g., 3.11.5]
- Docker: [e.g., 24.0.7]
- HuntForge commit: [e.g., abc123f]

## Additional Context
[Screenshots, logs, etc.]
```

### Suggesting Features

We love new ideas! Before opening feature request:

1. Check if it's already been suggested (search issues)
2. Consider if it fits HuntForge's scope (recon framework, not vuln scanner)
3. Think about backward compatibility
4. Consider resource impact (adaptive scheduling must accommodate)

Feature request template:

```markdown
## Problem
[What pain point does this solve?]

## Proposed Solution
[How should HuntForge behave?]

## Alternatives Considered
[Other approaches]

## Resource Impact
[Will this increase memory/CPU/time requirements? How should profile handle it?]
```

---

## Recognition

Contributors will be:

- Listed in [README.md](README.md#team) (with permission)
- Mentioned in release notes
- Granted repository collaborator permissions after substantial contributions

We value all contributions - code, docs, bugs, ideas, community support.

---

## Questions?

Open a [Discussion](https://github.com/HuntForgeHQ/huntforge/discussions) or email team@huntforge.dev

**Happy hunting!** 🔍
