# ⚡ HuntForge

> **AI-Powered Bug Bounty Recon Framework — Team Edition**
>
> Version 3.0 • 4-Member Team • 2025
>
> *Sequential • Resource-Aware • Laptop-Safe • AI-Ready • Team-Built*

---

## Table of Contents

1. [Team Structure & Ownership Map](#1-team-structure--ownership-map)
2. [Member 1 — Red Team Lead / Core Engine](#2-member-1--red-team-lead--core-engine)
3. [Member 2 — Red Team Partner / Tool Modules & AI](#3-member-2--red-team-partner--tool-modules--ai)
4. [Member 3 — Blue Team 1 / Logging & Detection](#4-member-3--blue-team-1--logging--detection)
5. [Member 4 — Blue Team 2 / Dashboard, Scope & Onboarding](#5-member-4--blue-team-2--dashboard-scope--onboarding)
6. [The Logging System — How It All Connects](#6-the-logging-system--how-it-all-connects)
7. [Team Git Workflow & Integration Guide](#7-team-git-workflow--integration-guide)
8. [Complete Project Structure](#8-complete-project-structure)
9. [Team Build Timeline](#9-team-build-timeline)
10. [What Each Member Learns](#10-what-each-member-learns)

---

## 1. Team Structure & Ownership Map

HuntForge is large enough that four people working in parallel can each own a meaningful slice without stepping on each other. The split below is designed so that blue team members learn offensive tooling deeply through the act of building its defense layer — not by passively watching.

### 1.1 The Core Principle

> **Rule: Every team member owns something they can demo alone in an interview.**
>
> - Red Team members own the **attack pipeline** — they understand every tool and why it runs.
> - Blue Team members own the **defense layer** — they understand what every tool looks like from the victim's perspective and build the systems that detect it.
> - The two sides meet at the **Logging System**. Red team generates events. Blue team defines what those events mean to a defender.
>
> This is exactly how real SOC/Red Team collaboration works at companies.

### 1.2 Team Roles at a Glance

| Component | Member 1 (Red Lead) | Member 2 (Red) | Member 3 (Blue) | Member 4 (Blue) |
|---|---|---|---|---|
| Core orchestrator | ✅ Owner | 📖 Reviewer | 📖 Reader | 📖 Reader |
| Resource monitor | ✅ Owner | | | |
| Tag manager | ✅ Owner | | | |
| Efficiency filter | ✅ Owner | | | |
| Budget tracker | ✅ Owner | | | |
| Passive recon modules | | ✅ Owner | | |
| Secrets & OSINT modules | | ✅ Owner | | |
| Discovery modules | | ✅ Owner | | |
| Surface intel modules | | ✅ Owner | | |
| Vuln scan modules | | ✅ Owner | | |
| AI methodology engine | | ✅ Owner | | |
| AI report generator | | ✅ Owner | | |
| HuntForge Logger | | | ✅ Owner | |
| Tool fingerprint DB | | | ✅ Owner | |
| SIEM log formatter | | | ✅ Owner | |
| Detection signatures | | | ✅ Owner | |
| Scope enforcer | | | | ✅ Owner |
| Report dashboard (Flask) | | | | ✅ Owner |
| Scan history DB | | | | ✅ Owner |
| Onboarding CLI wizard | | | | ✅ Owner |

---

## 2. Member 1 — Red Team Lead / Core Engine

> **Role:** Red Team Lead
> **Owns:** The entire `core/` directory. You are the architect.
> **Files:** `orchestrator.py`, `resource_monitor.py`, `tag_manager.py`, `efficiency_filter.py`, `budget_tracker.py`, `base_module.py`
> **Git Branch:** `feature/core-engine`
> **Resume Line:** *"Designed and built the orchestration engine for an AI-powered multi-tool recon framework in Python."*

### 2.1 Complete File List

| File | Responsibility |
|---|---|
| `core/orchestrator.py` | Main engine. Reads YAML, runs 4-gate check per tool, manages phase lifecycle. |
| `core/resource_monitor.py` | CPU/RAM safety system. `wait_until_safe()` before every tool launch. |
| `core/tag_manager.py` | Confidence-based tag system. v2 backward compat. `expires_after` storage. |
| `core/efficiency_filter.py` | Pre-execution sufficiency checks. Prevents redundant heavy enumeration. |
| `core/budget_tracker.py` | Scan budget enforcement. Graceful degradation when limits exceeded. |
| `modules/base_module.py` | Abstract base class. All 25+ tool modules inherit from this. |
| `huntforge.py` | Main CLI entry point. argparse, Rich output, AI prompt handling. |
| `config/default_methodology.yaml` | The v3 methodology with `budget`, `min_confidence`, `budget_applies` fields. |
| `config/machine_profiles.yaml` | Low/mid/high resource threshold definitions. |

### 2.2 The Orchestrator — Your Most Important File

The orchestrator is the heart of the project. Every other member's code is called by or feeds into this file.

```python
# core/orchestrator.py --- complete v3

import yaml, importlib, os
from concurrent.futures import ThreadPoolExecutor
from core.resource_monitor import ResourceMonitor
from core.tag_manager import TagManager
from core.efficiency_filter import EfficiencyFilter
from core.budget_tracker import BudgetTracker
from core.hf_logger import HFLogger  # Member 3 provides this
from loguru import logger

class Orchestrator:

    def __init__(self, domain, methodology_path, profile="mid",
                 output_dir="output", scope_checker=None):
        self.domain = domain
        self.output_dir = f"{output_dir}/{domain}"
        self.monitor = ResourceMonitor(profile)
        self.tags = TagManager(self.output_dir)
        self.eff_filter = EfficiencyFilter(self.output_dir)
        self.hf_log = HFLogger(self.output_dir)  # Member 3
        self.scope = scope_checker                # Member 4
        with open(methodology_path) as f:
            self.methodology = yaml.safe_load(f)
        budget_cfg = self.methodology.get("budget")
        self.budget = BudgetTracker(budget_cfg) if budget_cfg else None

    def run(self):
        self.hf_log.scan_start(self.domain)
        for phase_name, cfg in self.methodology["phases"].items():
            self.hf_log.phase_start(phase_name, cfg.get("label", ""))
            self._run_phase(phase_name, cfg)
            self.hf_log.phase_end(phase_name)
            if self.budget: self.budget.log_status()
        self.hf_log.scan_end(self.tags.all())

    def _run_phase(self, phase_name, cfg):
        flat  = cfg.get("tools", [])
        cond  = cfg.get("conditional_tools", [{"tool": t, "always": True} for t in flat])
        weight  = cfg.get("weight", "medium")
        max_w   = {"light": 4, "medium": 2, "heavy": 1}[weight]
        budgeted = cfg.get("budget_applies", False)
        use_pool = cfg.get("parallel", False) and max_w > 1
        pool = ThreadPoolExecutor(max_workers=max_w) if use_pool else None
        try:
            for tc in cond:
                tool = tc["tool"]
                skip_reason = self._get_skip_reason(tc, budgeted)
                if skip_reason:
                    self.hf_log.tool_skipped(tool, skip_reason)
                    continue
                self.monitor.wait_until_safe()
                self.hf_log.tool_start(tool)
                if pool: pool.submit(self._run_tool, tool)
                else:    self._run_tool(tool)
        finally:
            if pool: pool.shutdown(wait=True)
        self.eff_filter.evaluate_after_phase(phase_name)
        self._collect_phase_tags(cfg.get("tags_generated", []), phase_name)

    def _get_skip_reason(self, tc, budgeted):
        if not tc.get("always", False):
            req = tc.get("if_tag")
            if req:
                min_c = tc.get("min_confidence", "medium")
                if not self.tags.has(req, min_confidence=min_c):
                    actual = self.tags.get_confidence(req)
                    return f"tag={req} conf={actual} < required={min_c}"
        if self.eff_filter.should_skip(tc["tool"]):
            return "efficiency_filter: data already sufficient"
        if budgeted and self.budget and not self.budget.within_limits():
            return "budget_exceeded"
        return None  # no skip reason = run the tool

    def _collect_phase_tags(self, declared_tags, phase_name):
        self.tags.add_many_simple(declared_tags, source=f"{phase_name}_completion")

    def _run_tool(self, tool_name):
        pkgs = ["passive", "secrets", "discovery", "surface_intel",
                "enumeration", "content_discovery", "vuln_scan"]
        for pkg in pkgs:
            try:
                mod  = importlib.import_module(f"modules.{pkg}.{tool_name}")
                cls  = getattr(mod, tool_name.capitalize() + "Module")
                inst = cls(self.domain, self.output_dir, {})
                if self.budget:
                    self.budget.add_requests(inst.estimated_requests())
                inst.run()
                self.hf_log.tool_complete(tool_name, len(inst.results))
                for tag, meta in inst.emitted_tag_metadata.items():
                    self.tags.add(tag, **meta)
                return
            except ModuleNotFoundError:
                continue
        logger.warning(f"No module found for: {tool_name}")
```

### 2.3 Learning Path

| Week | Task |
|---|---|
| 1–2 | Build `base_module.py` and `resource_monitor.py`. Test with a simple echo command. |
| 3 | Build `tag_manager.py`. Write unit tests for `has()` with different confidence levels. |
| 4 | Build `efficiency_filter.py` and `budget_tracker.py` as standalone classes. |
| 5 | Build the orchestrator. Wire all systems together. Test with mock tool modules. |
| 6 | Integrate Member 3's HFLogger. Integrate Member 4's scope checker. |
| 7+ | Integration testing with Member 2's real tool modules. |

### 2.4 Git Workflow

```bash
# Your branch setup
git checkout -b feature/core-engine

# Commit often with meaningful messages
git commit -m "feat(orchestrator): add 4-gate pre-execution check"
git commit -m "feat(tag-manager): add confidence threshold to has()"
git commit -m "fix(budget): handle missing budget block gracefully"

# Create PR to main when a component is complete and tested
# Never push directly to main
```

---

## 3. Member 2 — Red Team Partner / Tool Modules & AI

> **Role:** Red Team Partner
> **Owns:** All tool modules (`modules/` directory) + AI integration (`ai/` directory)
> **Files:** 25+ tool wrapper modules, `methodology_engine.py`, `report_generator.py`
> **Git Branch:** `feature/tool-modules`
> **Resume Line:** *"Implemented 25+ security tool integrations for a Python recon framework, including AI-driven methodology generation via Ollama."*

### 3.1 Complete File List

| File / Directory | Responsibility |
|---|---|
| `modules/passive/subfinder.py` | Fast passive subdomain discovery — subprocess wrapper |
| `modules/passive/amass.py` | OWASP Amass — heavy tool, careful rate limiting |
| `modules/passive/crtsh.py` | Certificate transparency API — overrides `run()` with requests |
| `modules/passive/theharvester.py` | Email, subdomain, IP harvesting |
| `modules/passive/assetfinder.py` | Quick related domain finder |
| `modules/secrets/gitleaks.py` | Git secrets scanner — emits `leaked_api_keys` tag |
| `modules/secrets/trufflehog.py` | High-entropy string detector in git history |
| `modules/secrets/secretfinder.py` | JS file API key and token extractor |
| `modules/discovery/httpx.py` | HTTP probing — most important discovery tool |
| `modules/discovery/naabu.py` | Port scanner — feeds `unusual_ports_detected` tag |
| `modules/discovery/dnsx.py` | Bulk DNS resolver |
| `modules/surface_intel/whatweb.py` | Technology fingerprinter — feeds classifier |
| `modules/surface_intel/classifier.py` | **Your most important module** — sets confidence tags |
| `modules/enumeration/katana.py` | Web crawler — always runs |
| `modules/enumeration/gau.py` | Get All URLs from archives |
| `modules/enumeration/paramspider.py` | URL parameter discovery — efficiency filter may skip |
| `modules/enumeration/graphql_voyager.py` | GraphQL introspection — only if `has_api` |
| `modules/content_discovery/ffuf.py` | Directory fuzzer — needs `estimated_requests()` override |
| `modules/content_discovery/wpscan.py` | WordPress scanner — only if `has_cms` |
| `modules/vuln_scan/nuclei.py` | Template-based vuln scanner — most important vuln tool |
| `modules/vuln_scan/subjack.py` | Subdomain takeover — always runs |
| `modules/vuln_scan/dalfox.py` | XSS scanner — only if `params_found` |
| `ai/methodology_engine.py` | Ollama: user prompt → YAML methodology |
| `ai/report_generator.py` | Claude API: scan results + tags → HTML report |
| `scripts/install_tools.sh` | Auto-install all Go/pip tools in one command |

### 3.2 The Base Module Pattern — Learn This First

Every one of your 20+ modules follows the exact same pattern. Master it once and the rest takes 15 minutes each.

```python
# Pattern: subprocess tool (most of your modules)
from modules.base_module import BaseModule

class SubfinderModule(BaseModule):
    name   = "subfinder"
    weight = "light"
    phase  = 1

    def build_command(self):
        return ["subfinder", "-d", self.domain, "-silent", "-all", "-t", "10", "-timeout", "30"]

    def emit_tags(self):
        if len(self.results) > 5:
            self.emitted_tag_metadata["subdomain_list"] = {
                "confidence": "high",
                "source": self.name,
                "detected_at": "phase_1_passive_recon",
                "evidence": [f"{len(self.results)} subdomains found"],
            }

# Pattern: API tool (crtsh, shodan, etc.)
class CrtshModule(BaseModule):
    name   = "crtsh"
    weight = "light"

    def run(self):  # override run() entirely
        import requests
        url  = f"https://crt.sh/?q=%.{self.domain}&output=json"
        resp = requests.get(url, timeout=30)
        subs = set()
        for e in resp.json():
            subs.update(e["name_value"].replace("*.", "").split("\n"))
        self.results = [s for s in subs if self.domain in s]
        self.save_results()
        return self.results

    def build_command(self): pass

# Pattern: Heavy tool with budget reporting
class FfufModule(BaseModule):
    name   = "ffuf"
    weight = "heavy"

    def estimated_requests(self):
        return 4614 * max(1, self._live_host_count())

    def _live_host_count(self):
        import os
        p = os.path.join(self.output_dir, "raw", "httpx.txt")
        if not os.path.exists(p): return 1
        with open(p) as f: return max(1, sum(1 for l in f if l.strip()))

    def build_command(self):
        return ["ffuf", "-u", f"https://{self.domain}/FUZZ",
                "-w", "/usr/share/seclists/Discovery/Web-Content/common.txt",
                "-t", "50", "-rate", "100",
                "-o", f"{self.output_dir}/raw/ffuf.json", "-of", "json"]
```

### 3.3 AI Integration Files

```python
# ai/methodology_engine.py
import ollama, yaml

SYSTEM = """
You are a bug bounty recon expert for HuntForge v3.
Convert user instructions into a valid HuntForge YAML methodology.
Use conditional_tools with if_tag and min_confidence for smart execution.
Keep all weight, parallel, and budget_applies fields intact.
Return YAML only --- no explanation, no markdown fences.
Available tags: has_api, has_auth, has_cms, has_cloud_assets,
params_found, subdomain_list, leaked_api_keys.
Confidence levels: low, medium, high.
"""

def generate_methodology(user_instruction):
    resp = ollama.chat(model="llama3", messages=[
        {"role": "system", "content": SYSTEM},
        {"role": "user",   "content": user_instruction}
    ])
    try:
        return yaml.safe_load(resp["message"]["content"])
    except:
        return None
```

```python
# ai/report_generator.py
import anthropic, json

def generate_report(scan_results, domain, active_tags):
    client = anthropic.Anthropic()
    priority_hints = []
    for tag, meta in active_tags.items():
        if isinstance(meta, dict) and meta.get("confidence") == "high":
            priority_hints.append(f"HIGH CONFIDENCE: {tag} ({meta.get('source')})")

    prompt = f"""
Generate a professional HTML bug bounty recon report for: {domain}
Priority Intelligence: {", ".join(priority_hints)}
Tag Summary: {json.dumps({k: v.get("confidence") if isinstance(v, dict) else v
                           for k, v in active_tags.items()}, indent=2)}
Scan Data: {json.dumps(scan_results, indent=2)}
Structure: Executive Summary, Attack Surface Map, Priority Findings
(sorted by tag confidence), Full Subdomain Table, Next Steps.
Return only valid HTML with embedded CSS.
"""
    msg = client.messages.create(model="claude-opus-4-5", max_tokens=4096,
                                  messages=[{"role": "user", "content": prompt}])
    return msg.content[0].text
```

### 3.4 Learning Path

| Week | Task |
|---|---|
| 1–2 | Write `subfinder`, `crtsh`, `theharvester` modules. Run them manually against a bug bounty target. |
| 3 | Write `httpx` and `naabu` modules. These are your most important discovery tools. |
| 4 | Write `classifier.py` and `whatweb.py`. Test that confidence tags are set correctly. |
| 5 | Write `nuclei`, `subjack`, `gitleaks`. Add `emit_tags()` to each. |
| 6 | Write remaining modules (`ffuf`, `katana`, `gau`, `paramspider`, `dalfox`). |
| 7 | Install Ollama and build `methodology_engine.py`. Test with 5 different prompts. |
| 8 | Build `report_generator.py`. Get API key from console.anthropic.com. |
| 9 | Write `install_tools.sh`. Make sure one script installs everything cleanly. |

---

## 4. Member 3 — Blue Team 1 / Logging & Detection

> **Role:** Blue Team 1 — Logging & Detection
> **Owns:** The entire logging system + tool fingerprint database + SIEM formatter
> **Files:** `core/hf_logger.py`, `core/siem_formatter.py`, `data/tool_fingerprints.json`
> **Git Branch:** `feature/logging-detection`
> **Resume Line:** *"Built a structured security event logging system for a recon framework, including SIEM-compatible log formatting and a tool detection fingerprint database of 25+ offensive tools."*

This is where blue team meets red team. You are building the logging system that makes HuntForge educational — every scan generates structured logs that show exactly what an attacker's traffic looks like from the defender's perspective.

### 4.1 Why This Is Pure Blue Team Value

When HuntForge runs `subfinder` against a target, your logger records:
- What DNS queries were made
- What User-Agent strings were sent
- What IP ranges were contacted
- What rate of requests was generated

Your `tool_fingerprints.json` then answers:
- *"What does subfinder traffic look like in a DNS server log?"*
- *"What Snort rule would detect this?"*
- *"What Splunk query would catch this pattern?"*

### 4.2 HFLogger — Your Core File

```python
# core/hf_logger.py --- HuntForge Logger
import json, os, time
from datetime import datetime
from loguru import logger

class HFLogger:
    """
    HuntForge's structured event logger.
    Writes two outputs simultaneously:
    1. Human-readable colored terminal output (via loguru)
    2. Structured JSON event log (machine-readable, SIEM-compatible)
    """

    def __init__(self, output_dir):
        self.output_dir    = output_dir
        self.log_path      = os.path.join(output_dir, "logs", "scan_events.jsonl")
        self.scan_start_time = None
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

    # ── Scan Lifecycle ──────────────────────────────────
    def scan_start(self, domain):
        self.scan_start_time = time.time()
        self._write_event("SCAN_START", {"domain": domain, "timestamp": self._ts()})
        logger.info(f"[HuntForge] Scan started: {domain}")

    def scan_end(self, final_tags):
        duration = round(time.time() - self.scan_start_time, 2)
        self._write_event("SCAN_END", {
            "duration_seconds": duration,
            "duration_human":   self._human_duration(duration),
            "tags_at_completion": final_tags,
        })
        logger.success(f"[HuntForge] Scan complete in {self._human_duration(duration)}")

    # ── Phase Lifecycle ─────────────────────────────────
    def phase_start(self, phase_name, label):
        self._phase_start_time = time.time()
        self._write_event("PHASE_START", {"phase": phase_name, "label": label})
        logger.info(f"[Phase] ── {label} ──────────────")

    def phase_end(self, phase_name):
        duration = round(time.time() - self._phase_start_time, 2)
        self._write_event("PHASE_END", {"phase": phase_name, "duration": duration})
        logger.info(f"[Phase] {phase_name} done in {duration}s")

    # ── Tool Lifecycle ───────────────────────────────────
    def tool_start(self, tool_name):
        self._tool_times = getattr(self, "_tool_times", {})
        self._tool_times[tool_name] = time.time()
        fp = self._get_fingerprint(tool_name)
        self._write_event("TOOL_START", {
            "tool":           tool_name,
            "weight":         fp.get("weight", "unknown"),
            "detection_risk": fp.get("detection_risk", "unknown"),
        })
        logger.info(f"  [Tool] Starting: {tool_name}")

    def tool_complete(self, tool_name, result_count):
        start    = self._tool_times.get(tool_name, time.time())
        duration = round(time.time() - start, 2)
        self._write_event("TOOL_COMPLETE", {
            "tool": tool_name, "results": result_count, "duration_sec": duration
        })
        logger.success(f"  [Tool] {tool_name}: {result_count} results in {duration}s")

    def tool_skipped(self, tool_name, reason):
        self._write_event("TOOL_SKIPPED", {"tool": tool_name, "reason": reason})
        logger.debug(f"  [Skip] {tool_name} --- {reason}")

    def tool_error(self, tool_name, error):
        self._write_event("TOOL_ERROR", {"tool": tool_name, "error": str(error)})
        logger.error(f"  [Error] {tool_name}: {error}")

    # ── Tag Events ──────────────────────────────────────
    def tag_set(self, tag_name, confidence, source, evidence):
        self._write_event("TAG_SET", {
            "tag": tag_name, "confidence": confidence,
            "source": source, "evidence": evidence,
        })
        logger.info(f"  [Tag] {tag_name} = {confidence} (src:{source})")

    # ── Budget Events ───────────────────────────────────
    def budget_warning(self, pct_used, limit_type):
        self._write_event("BUDGET_WARNING", {"pct_used": pct_used, "limit_type": limit_type})
        logger.warning(f"  [Budget] {limit_type} at {pct_used}%")

    # ── Private Helpers ─────────────────────────────────
    def _write_event(self, event_type, data):
        event = {"event": event_type, "timestamp": self._ts(), **data}
        with open(self.log_path, "a") as f:
            f.write(json.dumps(event) + "\n")

    def _ts(self):
        return datetime.utcnow().isoformat() + "Z"

    def _human_duration(self, seconds):
        if seconds < 60:   return f"{seconds:.0f}s"
        if seconds < 3600: return f"{seconds/60:.1f}m"
        return f"{seconds/3600:.1f}h"

    def _get_fingerprint(self, tool_name):
        try:
            with open("data/tool_fingerprints.json") as f:
                fps = json.load(f)
            return fps.get(tool_name, {})
        except:
            return {}
```

### 4.3 Tool Fingerprint Database — Your Most Unique Contribution

This JSON file is pure blue team knowledge. For every tool HuntForge runs, you document what it looks like from the defender's side.

```json
// data/tool_fingerprints.json
{
  "subfinder": {
    "weight": "light",
    "detection_risk": "low",
    "description": "Passive subdomain enumeration --- queries third-party APIs",
    "network_behavior": {
      "direct_target_contact": false,
      "queries_made_to": ["virustotal.com", "shodan.io", "censys.io", "crt.sh", "alienvault.com"],
      "dns_queries": "none to target directly"
    },
    "defender_visibility": {
      "target_server_logs": "none --- target is never directly contacted",
      "dns_server_logs": "none",
      "waf_detection": "not detectable by target WAF",
      "splunk_query": "N/A --- passive tool",
      "snort_rule": "N/A --- passive tool"
    },
    "evasion_notes": "Fully passive. No direct connection to target ever."
  },
  "nmap": {
    "weight": "heavy",
    "detection_risk": "high",
    "description": "Port scanner --- sends TCP/UDP probes to target hosts",
    "network_behavior": {
      "direct_target_contact": true,
      "protocol": "TCP, UDP, ICMP",
      "rate": "up to 1000 packets/sec by default (use --max-rate 100)",
      "user_agent": "none --- operates at network layer"
    },
    "defender_visibility": {
      "target_server_logs": "SYN packets from scanner IP in firewall logs",
      "ids_detection": "HIGH --- nmap has well-known signatures in all IDS",
      "splunk_query": "index=firewall src_ip=<scanner> | stats count by dest_port",
      "snort_rule": "alert tcp any any -> $HOME_NET any (msg:\"Possible nmap scan\"; flags:S; threshold:type both,track by_src,count 20,seconds 1; sid:1000001;)",
      "waf_detection": "Detected by most WAFs via port scan heuristics"
    },
    "evasion_notes": "Use -T2 timing, --max-rate 50, -D decoy IPs for stealth"
  },
  "nuclei": {
    "weight": "heavy",
    "detection_risk": "high",
    "description": "Template-based vulnerability scanner --- sends HTTP requests",
    "network_behavior": {
      "direct_target_contact": true,
      "protocol": "HTTP/HTTPS",
      "user_agent": "Mozilla/5.0 (Windows; nuclei-v3)",
      "rate": "150 req/sec default (use -rate 20 for stealth)",
      "request_patterns": "Sends specific payloads matching vulnerability templates"
    },
    "defender_visibility": {
      "target_server_logs": "VERY HIGH --- nuclei generates distinctive request patterns",
      "waf_detection": "Most WAFs block nuclei by User-Agent and payload patterns",
      "splunk_query": "index=web_logs useragent=*nuclei* | stats count by src_ip",
      "snort_rule": "alert http any any -> $HTTP_SERVERS any (msg:\"Nuclei scanner\"; content:\"nuclei\"; http_header; sid:1000002;)",
      "cloudflare_rule": "Blocked by default WAF managed rules (CVE scanning category)"
    },
    "evasion_notes": "Change User-Agent with -H, use -rate 20, add random delays"
  },
  "ffuf": {
    "weight": "heavy",
    "detection_risk": "high",
    "description": "Web fuzzer --- sends rapid requests with wordlist variations",
    "network_behavior": {
      "direct_target_contact": true,
      "protocol": "HTTP/HTTPS",
      "user_agent": "Fuzz Faster U Fool",
      "rate": "up to 500 req/sec (limit with -rate)",
      "request_patterns": "Sequential 404/200 responses from wordlist"
    },
    "defender_visibility": {
      "target_server_logs": "EXTREME --- hundreds of 404s in rapid succession",
      "waf_detection": "Immediately blocked by all major WAFs",
      "splunk_query": "index=web_logs status=404 | bucket _time span=10s | stats count by src_ip | where count > 50",
      "snort_rule": "Detect via 404 rate threshold: >50 per 10 seconds from single IP"
    },
    "evasion_notes": "Use -rate 10, random delays, rotate User-Agents and IPs"
  },
  "gitleaks": {
    "weight": "light",
    "detection_risk": "none",
    "description": "Offline analysis of git repositories --- no network contact",
    "network_behavior": {
      "direct_target_contact": false,
      "queries_made_to": "GitHub API (read-only public data)",
      "dns_queries": "github.com only"
    },
    "defender_visibility": {
      "target_server_logs": "none",
      "detection_note": "Only detectable if GitHub API rate limit triggers alert",
      "mitigation": "Secret scanning (GitHub Advanced Security) prevents exposure"
    },
    "evasion_notes": "Fully offline analysis. Target has no visibility."
  }
}
```

### 4.4 SIEM Log Formatter

```python
# core/siem_formatter.py
import json

class SIEMFormatter:
    """
    Converts HuntForge scan_events.jsonl into SIEM-compatible formats.
    Useful for blue team practice: feed HuntForge output into
    a Splunk trial or ELK stack to practice detection.
    """

    def to_cef(self, event):
        """Common Event Format --- used by ArcSight, QRadar."""
        severity = {"TOOL_ERROR": 7, "TOOL_COMPLETE": 1, "TAG_SET": 3,
                    "SCAN_START": 1, "PHASE_START": 1}.get(event["event"], 1)
        return (
            f"CEF:0|HuntForge|ReconFramework|3.0|"
            f"{event['event']}|{event['event']}|{severity}|"
            f"rt={event['timestamp']} "
            + " ".join(f"{k}={v}" for k, v in event.items()
                       if k not in ["event", "timestamp"])
        )

    def to_leef(self, event):
        """Log Event Extended Format --- used by QRadar."""
        fields = "\t".join(f"{k}={v}" for k, v in event.items()
                           if k not in ["event", "timestamp"])
        return f"LEEF:2.0|HuntForge|ReconFramework|3.0|{event['event']}|{fields}"

    def to_splunk_hec(self, event):
        """Splunk HTTP Event Collector format."""
        return json.dumps({
            "time":       event["timestamp"],
            "source":     "huntforge",
            "sourcetype": "huntforge:scan",
            "event":      event,
        })

    def convert_file(self, jsonl_path, output_format="splunk"):
        """Convert entire scan log to chosen SIEM format."""
        converter = {"splunk": self.to_splunk_hec, "cef": self.to_cef, "leef": self.to_leef}[output_format]
        with open(jsonl_path) as f:
            lines = [json.loads(l) for l in f if l.strip()]
        return [converter(ev) for ev in lines]
```

### 4.5 Learning Path

| Week | Task |
|---|---|
| 1–2 | Study the orchestrator code (Member 1). Understand every event you need to log. |
| 3 | Build HFLogger. Wire it up with stub calls, test independently. |
| 4 | Research 5 tools (subfinder, nmap, nuclei, ffuf, gitleaks). Fill `tool_fingerprints.json`. |
| 5 | Research remaining 20 tools. Complete the fingerprint database. |
| 6 | Build SIEM formatter. Install a free Splunk trial. Feed your logs into it. |
| 7 | Write detection rules in Splunk for nuclei and ffuf traffic. Document them. |
| 8 | Integration test — run a full scan, verify all events appear in logs correctly. |

---

## 5. Member 4 — Blue Team 2 / Dashboard, Scope & Onboarding

> **Role:** Blue Team 2 — Dashboard, Scope & Onboarding
> **Owns:** Flask web dashboard, scope enforcer, scan history DB, onboarding wizard
> **Files:** `dashboard/app.py`, `core/scope_enforcer.py`, `core/scan_history.py`, `scripts/setup_wizard.py`, `templates/*.html`
> **Git Branch:** `feature/dashboard-scope`
> **Resume Line:** *"Built a Flask-based recon dashboard with scope enforcement and scan history for a team security tool, including an onboarding wizard for new security team members."*

Your work is the face of HuntForge. You make the tool accessible, safe, and professional. The scope enforcer is what keeps the team out of legal trouble. The dashboard is what makes the project visually impressive for the portfolio.

### 5.1 Complete File List

| File | Responsibility |
|---|---|
| `core/scope_enforcer.py` | Validates every domain against bug bounty program scope before any scan runs |
| `core/scan_history.py` | SQLite database wrapper — stores all scan results and tags historically |
| `dashboard/app.py` | Flask web application — main dashboard backend |
| `dashboard/templates/index.html` | Dashboard homepage — scan overview, recent scans, active tags |
| `dashboard/templates/scan.html` | Individual scan detail page — phase timeline, findings, tag confidence |
| `dashboard/templates/tools.html` | Tool fingerprint browser — shows Member 3's detection data visually |
| `dashboard/static/style.css` | Dashboard CSS styling |
| `scripts/setup_wizard.py` | First-run interactive wizard — API keys, machine profile, scope config |
| `scripts/check_tools.py` | Checks all required tools are installed, shows version table |
| `data/bug_bounty_scopes.json` | Maintained list of known bug bounty program scopes |

### 5.2 Scope Enforcer — Your Most Critical File

This runs before every scan and validates the target is in scope for a known bug bounty program or explicitly approved by the user. This protects everyone on the team legally.

```python
# core/scope_enforcer.py
import json, re, os
from loguru import logger

class ScopeEnforcer:
    """
    Validates scan targets against bug bounty program scopes.
    Must be checked BEFORE any scan begins.
    Blocks scans against out-of-scope targets.
    """

    def __init__(self, scope_file="data/bug_bounty_scopes.json"):
        self.scope_file       = scope_file
        self.manual_approvals = set()
        self._load_scopes()

    def _load_scopes(self):
        try:
            with open(self.scope_file) as f:
                self.programs = json.load(f)
        except FileNotFoundError:
            self.programs = {}
            logger.warning("No scope file found. All scans require manual approval.")

    def check(self, domain):
        """
        Returns: (is_allowed: bool, reason: str, program: str|None)
        Orchestrator must call this and abort if is_allowed is False.
        """
        if domain in self.manual_approvals:
            return True, "manually_approved", None

        for program_name, program_data in self.programs.items():
            in_scope     = program_data.get("in_scope", [])
            out_of_scope = program_data.get("out_of_scope", [])

            for pattern in out_of_scope:
                if self._matches(domain, pattern):
                    return False, f"out_of_scope:{program_name}", program_name

            for pattern in in_scope:
                if self._matches(domain, pattern):
                    return True, f"in_scope:{program_name}", program_name

        return False, "not_in_any_known_program", None

    def approve_manual(self, domain, confirmation_text):
        """User must type the exact domain to confirm they own it."""
        if confirmation_text.strip() == domain:
            self.manual_approvals.add(domain)
            logger.info(f"Manual approval granted for {domain}")
            return True
        return False

    def _matches(self, domain, pattern):
        """Support wildcard patterns like *.example.com"""
        if pattern.startswith("*."):
            suffix = pattern[2:]
            return domain.endswith("." + suffix) or domain == suffix
        return domain == pattern or domain.endswith("." + pattern)
```

Scope file format (`data/bug_bounty_scopes.json`):

```json
{
  "HackerOne: example_program": {
    "platform": "hackerone",
    "in_scope":     ["*.example.com", "api.example.com"],
    "out_of_scope": ["blog.example.com", "status.example.com"]
  },
  "Bugcrowd: another_program": {
    "platform": "bugcrowd",
    "in_scope":     ["*.target.com"],
    "out_of_scope": ["careers.target.com"]
  }
}
```

### 5.3 Flask Dashboard

```python
# dashboard/app.py --- Flask web dashboard
from flask import Flask, render_template, jsonify, request
from core.scan_history import ScanHistory
import json, os

app     = Flask(__name__)
history = ScanHistory()

@app.route("/")
def index():
    scans = history.get_recent(limit=10)
    return render_template("index.html", scans=scans)

@app.route("/scan/<domain>")
def scan_detail(domain):
    data   = history.get_scan(domain)
    tags   = data.get("tags", {})
    phases = data.get("phases", [])
    return render_template("scan.html", domain=domain, tags=tags, phases=phases)

@app.route("/api/tags/<domain>")
def api_tags(domain):
    """JSON endpoint for tags --- used by dashboard JS charts."""
    return jsonify(history.get_scan(domain).get("tags", {}))

@app.route("/api/scan_log/<domain>")
def api_scan_log(domain):
    """Stream scan event log for live view during active scans."""
    log_path = f"output/{domain}/logs/scan_events.jsonl"
    if not os.path.exists(log_path):
        return jsonify([])
    with open(log_path) as f:
        events = [json.loads(l) for l in f if l.strip()]
    return jsonify(events)

@app.route("/tools")
def tools():
    with open("data/tool_fingerprints.json") as f:
        fingerprints = json.load(f)
    return render_template("tools.html", fingerprints=fingerprints)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
```

### 5.4 Scan History Database

```python
# core/scan_history.py
import sqlite3, json, os
from datetime import datetime

class ScanHistory:

    def __init__(self, db_path="data/scan_history.db"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db = sqlite3.connect(db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self):
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS scans (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                domain        TEXT NOT NULL,
                started       TEXT,
                completed     TEXT,
                profile       TEXT,
                tags          TEXT,
                phases        TEXT,
                finding_count INTEGER DEFAULT 0
            )""")
        self.db.commit()

    def save_scan(self, domain, profile, tags, phases, finding_count=0):
        self.db.execute(
            "INSERT INTO scans (domain,started,completed,profile,tags,phases,finding_count)"
            " VALUES (?,?,?,?,?,?,?)",
            (domain, datetime.utcnow().isoformat(), datetime.utcnow().isoformat(),
             profile, json.dumps(tags), json.dumps(phases), finding_count)
        )
        self.db.commit()

    def get_recent(self, limit=10):
        cur = self.db.execute(
            "SELECT domain,started,profile,finding_count FROM scans"
            " ORDER BY id DESC LIMIT ?", (limit,))
        return [{"domain": r[0], "started": r[1], "profile": r[2], "findings": r[3]}
                for r in cur.fetchall()]

    def get_scan(self, domain):
        cur = self.db.execute(
            "SELECT * FROM scans WHERE domain=? ORDER BY id DESC LIMIT 1", (domain,))
        row = cur.fetchone()
        if not row: return {}
        return {"domain": row[1], "started": row[2], "profile": row[4],
                "tags":   json.loads(row[5] or "{}"),
                "phases": json.loads(row[6] or "[]")}
```

### 5.5 Setup Wizard

```python
# scripts/setup_wizard.py --- First-time onboarding for new team members
import os, json
from rich.console import Console
from rich.panel   import Panel
from rich.prompt  import Prompt, Confirm

console = Console()

def run_wizard():
    console.print(Panel("[bold cyan]HuntForge Setup Wizard[/]", expand=False))
    console.print("[yellow]This wizard configures HuntForge for your machine.[/]\n")
    config = {}

    # Machine profile
    console.print("[bold]Step 1: Machine Profile[/]")
    console.print("  1) Low end (4GB RAM, 2 cores)")
    console.print("  2) Mid range (8GB RAM, 4 cores)")
    console.print("  3) High end (16GB+ RAM, 8+ cores)")
    choice = Prompt.ask("Your machine", choices=["1", "2", "3"], default="2")
    config["profile"] = ["low", "mid", "high"][int(choice) - 1]

    # API keys
    console.print("\n[bold]Step 2: API Keys (press Enter to skip)[/]")
    config["anthropic_api_key"] = Prompt.ask("Anthropic API key", default="", password=True)
    config["shodan_api_key"]    = Prompt.ask("Shodan API key",    default="", password=True)

    # Scope preference
    console.print("\n[bold]Step 3: Default Scope Behavior[/]")
    strict = Confirm.ask("Require scope check before every scan?", default=True)
    config["strict_scope"] = strict

    # Save to user config
    config_dir  = os.path.expanduser("~/.huntforge")
    config_path = os.path.join(config_dir, "config.json")
    os.makedirs(config_dir, exist_ok=True)
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    console.print(f"\n[green]Config saved to {config_path}[/]")
    console.print("[cyan]Run: python scripts/check_tools.py to verify all tools are installed.[/]")

if __name__ == "__main__":
    run_wizard()
```

### 5.6 Learning Path

| Week | Task |
|---|---|
| 1–2 | Study `scope_enforcer.py`. Research 10 real bug bounty programs on HackerOne. Populate scopes JSON. |
| 3 | Build `scan_history.py`. Test with dummy data. Run queries against it. |
| 4 | Build `setup_wizard.py` and `check_tools.py`. These help the whole team onboard. |
| 5 | Build Flask dashboard skeleton — `index.html`, `scan.html` with placeholder data. |
| 6 | Connect dashboard to real scan output. Wire up API routes. |
| 7 | Style the dashboard. Use AI to generate the CSS and HTML templates. |
| 8 | Add the tool fingerprint browser page (uses Member 3's data). |
| 9 | Integration testing — run a real scan, verify it appears in dashboard. |

---

## 6. The Logging System — How It All Connects

The logging system is the thread that ties all four team members together.

### 6.1 Log Flow Diagram

```
Member 1 (Orchestrator) calls:
  hf_log.scan_start(domain)
  hf_log.phase_start(phase_name, label)
  hf_log.tool_start(tool_name)      ← Member 3 HFLogger captures this
  hf_log.tool_complete(tool_name, count)
  hf_log.tool_skipped(tool_name, reason)
  hf_log.tag_set(tag, confidence, source)
  hf_log.phase_end(phase_name)
  hf_log.scan_end(final_tags)
            ↓
Member 3 (HFLogger) writes to:
  output/[domain]/logs/scan_events.jsonl  ← one JSON object per line
            ↓
Member 3 (SIEMFormatter) converts to:
  Splunk HEC format / CEF / LEEF
  → Import into Splunk trial for detection rule practice
            ↓
Member 4 (Dashboard) reads:
  GET /api/scan_log/<domain> → reads scan_events.jsonl
  Renders timeline of events in browser
  Shows tag confidence as colored badges
  Shows skip reasons for each tool
```

### 6.2 Sample scan_events.jsonl Output

```jsonl
{"event":"SCAN_START","timestamp":"2025-09-15T14:00:00Z","domain":"example.com"}
{"event":"PHASE_START","timestamp":"2025-09-15T14:00:01Z","phase":"phase_1_passive_recon","label":"Passive Recon"}
{"event":"TOOL_START","timestamp":"2025-09-15T14:00:02Z","tool":"subfinder","weight":"light","detection_risk":"low"}
{"event":"TOOL_COMPLETE","timestamp":"2025-09-15T14:01:45Z","tool":"subfinder","results":47,"duration_sec":103}
{"event":"TOOL_START","timestamp":"2025-09-15T14:01:46Z","tool":"amass","weight":"heavy","detection_risk":"low"}
{"event":"TOOL_COMPLETE","timestamp":"2025-09-15T14:06:12Z","tool":"amass","results":61,"duration_sec":266}
{"event":"PHASE_END","timestamp":"2025-09-15T14:06:13Z","phase":"phase_1_passive_recon","duration":372}
{"event":"TOOL_START","timestamp":"2025-09-15T14:06:15Z","tool":"gitleaks","weight":"light","detection_risk":"none"}
{"event":"TOOL_COMPLETE","timestamp":"2025-09-15T14:07:02Z","tool":"gitleaks","results":2,"duration_sec":47}
{"event":"TAG_SET","timestamp":"2025-09-15T14:07:03Z","tag":"leaked_api_keys","confidence":"high","source":"gitleaks","evidence":["AWS_SECRET_KEY in config.py"]}
{"event":"TAG_SET","timestamp":"2025-09-15T14:09:12Z","tag":"has_cms","confidence":"high","source":"whatweb","evidence":["WordPress 6.4","wp-content/themes/"]}
{"event":"TAG_SET","timestamp":"2025-09-15T14:09:13Z","tag":"has_api","confidence":"medium","source":"httpx_tech","evidence":["/api/v1","/api/v2"]}
{"event":"TOOL_SKIPPED","timestamp":"2025-09-15T14:12:01Z","tool":"graphql_voyager","reason":"tag=has_api conf=medium < required=high"}
{"event":"TOOL_SKIPPED","timestamp":"2025-09-15T14:18:44Z","tool":"paramspider","reason":"efficiency_filter: data already sufficient"}
{"event":"SCAN_END","timestamp":"2025-09-15T15:02:30Z","duration_seconds":3750,"duration_human":"1.0h","tags_at_completion":{...}}
```

### 6.3 What Blue Team Learns From These Logs

| Log Event | What a Defender Sees | Blue Team Skill Built |
|---|---|---|
| `TOOL_START: nmap detection_risk=high` | SYN flood from single IP in firewall logs | Writing Snort/Suricata rules for port scan detection |
| `TOOL_START: nuclei detection_risk=high` | Distinctive HTTP payloads in WAF logs | Building WAF rules, understanding CVE scanner traffic |
| `TOOL_START: ffuf detection_risk=high` | Hundreds of 404s per second in web logs | Threshold alerting in Splunk, rate-based detection |
| `TAG_SET: leaked_api_keys confidence=high` | GitHub secret scanning alert | Understanding why secrets management matters |
| `TOOL_SKIPPED: efficiency_filter` | N/A — internal only | Understanding recon workflow optimization |
| `TAG_SET: has_cms confidence=high` | Technology fingerprinting headers in response | Hardening CMS fingerprint exposure |

---

## 7. Team Git Workflow & Integration Guide

### 7.1 Branch Strategy

```
main                         ← stable, working code only. PRs reviewed by all 4.
├── feature/core-engine      ← Member 1
├── feature/tool-modules     ← Member 2
├── feature/logging-detection ← Member 3
└── feature/dashboard-scope  ← Member 4

Integration branches (created when 2+ features need to be tested together):
└── integration/phase1-complete ← created after Phases 1–3 all work together
```

### 7.2 Interface Contracts — What Each Member Provides

These are the agreements between team members. If you change an interface, you tell the person who depends on it **before** merging.

| Contract | Details |
|---|---|
| Member 1 → Member 2 | `base_module.py` interface is stable. `emitted_tag_metadata` dict and `estimated_requests()` method are fixed APIs. Member 2 depends on these. |
| Member 1 → Member 3 | Orchestrator calls `hf_log.tool_start(tool_name)` and `hf_log.tool_complete(tool_name, count)`. These signatures will not change after Week 5. |
| Member 1 → Member 4 | Orchestrator accepts `scope_checker=None` parameter. Calls `scope_checker.check(domain)` before scan. Member 4 provides the `ScopeEnforcer` instance. |
| Member 3 → Member 4 | HFLogger writes to `output/[domain]/logs/scan_events.jsonl`. Format is stable JSONL. Member 4 reads this in the dashboard. |
| Member 3 → Everyone | `data/tool_fingerprints.json` is read by HFLogger and dashboard. Schema is stable after Week 5. |

### 7.3 Weekly Sync Checklist

- **Every Sunday:** each member pushes their week's work to their branch
- **Every Monday:** 30-minute call — each person demos what they built
- **Rule:** if you cannot demo it running, it is not done
- **Week 7:** First full integration test — all branches merged to integration branch
- **Week 13:** GitHub release v1.0 — tag it, write changelog, share publicly

### 7.4 Testing Strategy

| Test Type | Who Writes It / What It Tests |
|---|---|
| Unit tests (pytest) | Each member writes tests for their own code. `tag_manager.has()` threshold logic, `ScopeEnforcer` pattern matching, budget time parsing. |
| Integration tests | Member 1 writes tests that run mock tool modules through the full orchestrator pipeline. |
| End-to-end tests | All 4 members: run a full scan against a test domain (use your own server or a dedicated bug bounty program). Verify all logs, tags, and dashboard output. |
| Blue team exercise | Member 3 and 4: after a full scan, analyze the `scan_events.jsonl` in Splunk. Write at least one detection rule for nuclei and one for ffuf. |

---

## 8. Complete Project Structure

```
huntforge/                          ← root
│
├── huntforge.py                    ← Member 1: main CLI entry point
├── requirements.txt
├── README.md                       ← All members contribute sections
├── CONTRIBUTING.md                 ← Member 4 writes this
├── docker-compose.yml              ← Member 1 (Phase 5)
│
├── core/                           ← Member 1 OWNS this entire directory
│   ├── orchestrator.py
│   ├── resource_monitor.py
│   ├── tag_manager.py
│   ├── efficiency_filter.py
│   ├── budget_tracker.py
│   ├── hf_logger.py                ← Member 3 provides, Member 1 imports
│   ├── siem_formatter.py           ← Member 3
│   ├── scope_enforcer.py           ← Member 4 provides, Member 1 imports
│   ├── scan_history.py             ← Member 4
│   └── deduplicator.py             ← Member 1
│
├── modules/                        ← Member 2 OWNS this entire directory
│   ├── base_module.py              ← Member 1 defines, Member 2 inherits
│   ├── passive/
│   │   ├── subfinder.py
│   │   ├── amass.py
│   │   ├── crtsh.py
│   │   └── theharvester.py
│   ├── secrets/
│   │   ├── gitleaks.py
│   │   ├── trufflehog.py
│   │   └── secretfinder.py
│   ├── discovery/
│   │   ├── httpx.py
│   │   ├── naabu.py
│   │   └── dnsx.py
│   ├── surface_intel/
│   │   ├── whatweb.py
│   │   ├── wappalyzer.py
│   │   └── classifier.py
│   ├── enumeration/
│   │   ├── katana.py
│   │   ├── gau.py
│   │   ├── paramspider.py
│   │   └── graphql_voyager.py
│   ├── content_discovery/
│   │   ├── ffuf.py
│   │   ├── dirsearch.py
│   │   └── wpscan.py
│   └── vuln_scan/
│       ├── nuclei.py
│       ├── subjack.py
│       └── dalfox.py
│
├── ai/                             ← Member 2 OWNS
│   ├── methodology_engine.py
│   └── report_generator.py
│
├── dashboard/                      ← Member 4 OWNS
│   ├── app.py
│   ├── templates/
│   │   ├── index.html
│   │   ├── scan.html
│   │   └── tools.html
│   └── static/
│       └── style.css
│
├── config/
│   ├── default_methodology.yaml    ← Member 1
│   ├── tool_configs.yaml           ← Member 2
│   └── machine_profiles.yaml      ← Member 1
│
├── data/                           ← Shared data directory
│   ├── tool_fingerprints.json      ← Member 3 OWNS
│   ├── bug_bounty_scopes.json      ← Member 4 OWNS
│   └── scan_history.db             ← Auto-created by Member 4's ScanHistory
│
├── output/                         ← Auto-created per scan
│   └── [domain]/
│       ├── raw/                    ← Tool output text files
│       ├── processed/
│       │   ├── active_tags.json    ← Tag manager output
│       │   ├── surface_intel.json
│       │   ├── budget_status.json
│       │   └── efficiency_report.json
│       ├── logs/
│       │   └── scan_events.jsonl   ← Member 3's HFLogger output
│       └── report.html             ← AI-generated final report
│
├── tests/                          ← All members write tests for their code
│   ├── test_orchestrator.py        ← Member 1
│   ├── test_tag_manager.py         ← Member 1
│   ├── test_modules.py             ← Member 2
│   ├── test_hf_logger.py           ← Member 3
│   └── test_scope_enforcer.py      ← Member 4
│
└── scripts/
    ├── install_tools.sh            ← Member 2
    ├── setup_wizard.py             ← Member 4
    └── check_tools.py              ← Member 4
```

---

## 9. Team Build Timeline

| Week | All 4 Members | Milestone |
|---|---|---|
| 1 | Setup: Git repo, branches, Python env, install tools | Everyone has a working Python env and has cloned the repo |
| 2 | M1: `base_module` + `resource_monitor`. M2: `subfinder`, `crtsh`. M3: HFLogger skeleton. M4: `scope_enforcer` | First real code in all 4 branches |
| 3 | M1: `tag_manager`. M2: `httpx`, `naabu`. M3: `tool_fingerprints` (5 tools). M4: `setup_wizard` | |
| 4 | M1: `efficiency_filter` + `budget_tracker`. M2: `whatweb` + `classifier`. M3: fingerprints (15 tools). M4: `scan_history` | |
| 5 | M1: orchestrator core. M2: `nuclei`, `gitleaks`, `subjack`. M3: SIEM formatter. M4: Flask skeleton | Integration test: Member 1+2 phases run together |
| 6 | M1: wire all systems. M2: remaining modules. M3: Splunk import test. M4: dashboard routes | |
| **7** | **Integration branch: all features merged. Full scan test.** | 🎯 **MILESTONE: Full scan works end-to-end on real target** |
| 8 | M1+2: AI integration. M3: detection rules. M4: dashboard styling | AI methodology + report working |
| 9 | M2: `install_tools.sh`. M4: `check_tools.py`. All: bug fixes from Week 7 test | |
| **10** | **Full team: run scan on 3 different bug bounty targets. Fix every issue found.** | 🎯 **MILESTONE: Framework reliable in real hunting** |
| 11 | M4: Docker setup. All: README sections. M3: Blue team exercise in Splunk | |
| 12 | All: code review across all branches. Write tests. Fix edge cases. | |
| **13** | **GitHub release v1.0. Write changelogs. Add screenshots to README.** | 🎯 **MILESTONE: Public GitHub launch** |
| 14–17 | M4: dashboard polish. M3: add 5 more tool fingerprints. M1: `--resume` flag. | v1.1 polish release |

---

## 10. What Each Member Learns

| Member | Technical Skills Gained | Career Value |
|---|---|---|
| **Member 1** Red Lead | Python system design, subprocess management, concurrent execution, YAML parsing, tag/flag systems, budget tracking | Can explain framework architecture in interviews. Demonstrates senior-level thinking about modularity and safety. |
| **Member 2** Red Team | 25+ offensive security tools (hands-on), subprocess wrappers, AI API integration, LLM prompt engineering, Go tool ecosystem | Knows more tools than most junior red teamers. AI integration is a rare skill in security roles. |
| **Member 3** Blue Team | Structured logging design, SIEM formats (CEF/LEEF/Splunk), offensive tool behavior from defender perspective, detection rule writing | Can discuss how to detect recon tools in any SOC interview. Unique dual-perspective knowledge. |
| **Member 4** Blue Team | Flask web development, SQLite, scope enforcement design, UX/onboarding design, legal compliance thinking | Built a security web application. Understands compliance/scope constraints that real security teams deal with daily. |

### 10.1 Resume Lines for Everyone

| Member | Resume Project Entry |
|---|---|
| Member 1 | Architected HuntForge — a Python recon framework with modular orchestration, AI-driven methodology, and resource-aware execution (`github.com/team/huntforge`) |
| Member 2 | Built 25+ security tool integrations for HuntForge using Python subprocess architecture, and implemented Ollama/Claude AI integration for dynamic scan methodology |
| Member 3 | Built the logging and detection layer for HuntForge — including a SIEM-compatible event log system and a detection fingerprint database covering 25+ offensive tools |
| Member 4 | Developed the HuntForge web dashboard, scope enforcement engine, and onboarding system, ensuring legal compliance and accessibility for security team workflows |

---

*HuntForge Team Edition v3.0 — Four people. One framework. Real skills.*
