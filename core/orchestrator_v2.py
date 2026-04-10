#!/usr/bin/env python3
"""
HuntForge Orchestrator V2 - Resource-Aware Adaptive Scheduling

Professional-grade orchestrator. Runs exactly what the methodology YAML defines.
No profile filtering — the methodology IS the single source of truth.

Key features:
- Adaptive concurrency based on system resources
- Phase-specific scheduling strategies (light vs heavy)
- Parameter scaling (reduce threads if memory constrained)
- Checkpoint/resume capability
- Optional Phase 7 (user selects targets after recon)
- Resource monitoring throughout
"""

import os
import gc
import yaml
import json
import time
import sys
import signal
import inspect
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from loguru import logger

# Import core components
from core.tag_manager import TagManager
from core.budget_tracker import BudgetTracker
from core.scan_history import ScanHistory
from core.hf_logger import HFLogger
from core.exceptions import (
    HuntForgeError, OutOfScopeError, BudgetExceededError,
    BinaryNotFoundError, ToolTimeoutError, ToolExecutionError
)

# Import new scheduler
from core.resource_aware_scheduler import (
    AdaptiveScheduler,
    ToolProfiles,
    ResourceMonitor,
    SystemCapacity
)

# ═══════════════════════════════════════════════════════════════════
# TOOL IMPORTS — Professional methodology only (16 essential tools)
# ═══════════════════════════════════════════════════════════════════

# Phase 1 — Passive Recon (3 tools)
from modules.passive.subfinder import SubfinderModule as Subfinder
from modules.passive.crtsh import CrtshModule as Crtsh

# Phase 2 — Secrets & OSINT (2 tools)
from modules.secrets.gitleaks import GitleaksModule as Gitleaks
from modules.secrets.trufflehog import TrufflehogModule as Trufflehog

# Phase 3 — Live Asset Discovery (2 tools)
from modules.discovery.httpx import HttpxModule as Httpx
from modules.discovery.naabu import NaabuModule as Naabu

# Phase 4 — Surface Intelligence (2 tools)
from modules.surface_intel.whatweb import WhatWebModule as WhatWeb
from modules.surface_intel.wappalyzer import WappalyzerModule as Wappalyzer

# Phase 5 — Enumeration (5 tools, 2 conditional)
from modules.enumeration.katana import KatanaModule as Katana
from modules.enumeration.gau import GauModule as Gau
from modules.enumeration.paramspider import ParamspiderModule as Paramspider
from modules.enumeration.arjun import ArjunModule as Arjun
from modules.enumeration.graphql_voyager import GraphqlVoyagerModule as GraphqlVoyager

# Phase 6 — Content Discovery (2 tools, 1 conditional)
from modules.content_discovery.ffuf import FfufModule as Ffuf
from modules.content_discovery.wpscan import WpscanModule as Wpscan

# Phase 7 — Vulnerability Scanning (5 tools, 3 conditional)
from modules.vuln_scan.nuclei import NucleiModule as Nuclei
from modules.vuln_scan.subjack import SubjackModule as Subjack
from modules.vuln_scan.dalfox import DalfoxModule as Dalfox
from modules.vuln_scan.sqlmap import SQLMapModule as SQLMap

# ═══════════════════════════════════════════════════════════════════
# TOOL REGISTRY — maps YAML tool names to Python classes
# ═══════════════════════════════════════════════════════════════════

TOOL_REGISTRY = {
    # Phase 1 — Passive Recon
    'subfinder':        Subfinder,
    'crtsh':            Crtsh,

    # Phase 2 — Secrets & OSINT
    'gitleaks':         Gitleaks,
    'trufflehog':       Trufflehog,

    # Phase 3 — Live Asset Discovery
    'httpx':            Httpx,
    'naabu':            Naabu,

    # Phase 4 — Surface Intelligence
    'whatweb':          WhatWeb,
    'wappalyzer_cli':   Wappalyzer,

    # Phase 5 — Enumeration
    'katana':           Katana,
    'gau':              Gau,
    'paramspider':      Paramspider,
    'arjun':            Arjun,
    'graphql_voyager':  GraphqlVoyager,

    # Phase 6 — Content Discovery
    'ffuf':             Ffuf,
    'wpscan':           Wpscan,

    # Phase 7 — Vulnerability Scanning
    'nuclei':           Nuclei,
    'nuclei_auth':      Nuclei,
    'subjack':          Subjack,
    'dalfox':           Dalfox,
    'sqlmap':           SQLMap,
}


class OrchestratorV2:
    """
    Professional-grade orchestrator with adaptive resource scheduling.

    Key principles:
    1. The methodology YAML is the single source of truth
    2. No profile filtering — execute exactly what the YAML defines
    3. Adaptive scheduling based on real-time system resources
    4. Checkpoint/resume for long-running scans
    5. Optional Phase 7 with human decision point
    """

    def __init__(self, domain: str, methodology_path: str,
                 checkpoint_file: Optional[str] = None, adaptive: bool = True):
        self.domain = domain
        self.adaptive = adaptive
        self.methodology_path = Path(methodology_path)
        self.checkpoint_file = checkpoint_file or f"output/{domain}/checkpoint.json"

        # Load methodology
        with open(self.methodology_path) as f:
            self.methodology = yaml.safe_load(f)

        # Initialize core components
        self.tag_manager = TagManager()
        self.budget_tracker = BudgetTracker()
        self.scan_history = ScanHistory()
        self.logger = HFLogger(f"output/{domain}")

        # Initialize scheduler
        self.resource_monitor = ResourceMonitor(update_interval=2.0)
        self.tool_profiles = ToolProfiles()
        self.scheduler = AdaptiveScheduler(self.tool_profiles, self.resource_monitor)

        # Runtime state
        self.completed_tools: List[Dict[str, Any]] = []
        self.current_phase = None
        self.scan_start_time = None
        self._shutdown = False

        # Signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.warning(f"Received signal {signum}, initiating graceful shutdown...")
        self._shutdown = True

    def load_checkpoint(self) -> bool:
        """Load existing checkpoint if exists"""
        checkpoint_path = Path(self.checkpoint_file)
        if checkpoint_path.exists():
            try:
                with open(checkpoint_path) as f:
                    data = json.load(f)

                self.completed_tools = data.get('completed_tools', [])
                self.tag_manager.tags = data.get('tags', {})
                logger.info(f"Resumed from checkpoint: {len(self.completed_tools)} tools already completed")
                return True
            except Exception as e:
                logger.error(f"Failed to load checkpoint: {e}")
        return False

    def save_checkpoint(self):
        """Save current state to checkpoint file"""
        checkpoint_dir = Path(self.checkpoint_file).parent
        checkpoint_dir.mkdir(parents=True, exist_ok=True)

        data = {
            'domain': self.domain,
            'phase': self.current_phase,
            'completed_tools': self.completed_tools,
            'tags': self.tag_manager.tags,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Checkpoint saved: {len(self.completed_tools)} tools completed")
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")

    def should_skip_tool(self, tool_config: dict, tool_name: str) -> Tuple[bool, str]:
        """Check if tool should be skipped (already done or conditional)"""
        # Check if already completed in this scan
        if any(ct['tool'] == tool_name for ct in self.completed_tools):
            return True, "Already completed in this scan"

        # Check if_tag condition
        if_tag = tool_config.get('if_tag')
        if if_tag:
            if not self.tag_manager.has(if_tag):
                return True, f"Tag '{if_tag}' not set"

        # Check enabled flag
        if tool_config.get('enabled', True) is False:
            return True, "Tool disabled in methodology"

        return False, ""

    def run_phase(self, phase_name: str, phase_config: dict):
        """Execute a single phase with adaptive scheduling"""
        logger.info(f"Starting phase: {phase_config.get('label', phase_name)}")
        self.current_phase = phase_name

        # Support both 'tools' (phases 1-4) and 'conditional_tools' (phases 5-7)
        tools = phase_config.get('tools') or phase_config.get('conditional_tools') or []
        input_files = phase_config.get('input_files', {})

        # Build list of tools to run
        tools_to_run = []
        for tool_entry in tools:
            # Handle both dict and simple string formats
            if isinstance(tool_entry, dict):
                tool_name = tool_entry.get('tool') or tool_entry.get('name')
                if not tool_name:
                    continue
                tool_config = tool_entry
            else:
                tool_name = tool_entry
                tool_config = {}

            skip, reason = self.should_skip_tool(tool_config, tool_name)
            if skip:
                logger.info(f"Skipping {tool_name}: {reason}")
                if tool_name in TOOL_REGISTRY:
                    self.logger.tool_skipped(tool_name, reason)
                continue

            if tool_name not in TOOL_REGISTRY:
                logger.warning(f"Tool {tool_name} not in registry, skipping")
                continue

            tools_to_run.append({
                'name': tool_name,
                'config': tool_config,
                '_class': TOOL_REGISTRY[tool_name]
            })

        logger.info(f"Phase {phase_name}: {len(tools_to_run)} tools to execute")

        # Adaptive scheduling loop
        completed = 0
        total = len(tools_to_run)

        while tools_to_run and not self._shutdown:
            # Check if we can start another tool
            current_concurrent = len(self.scheduler.get_running_tools())
            capacity = self.resource_monitor.get_capacity()

            # Try to get next tool that fits
            tool_to_start = None
            best_decision = None

            for i, tool_info in enumerate(tools_to_run):
                decision = self.scheduler.can_schedule(
                    tool_info['name'],
                    phase_name,
                    current_concurrent,
                    tool_info.get('config', {})
                )

                if decision.action == 'run':
                    tool_to_start = tool_info
                    best_decision = decision
                    tools_to_run.pop(i)
                    break
                elif decision.action == 'wait' and not tool_to_start:
                    best_decision = decision

            if tool_to_start and best_decision:
                # Start the tool
                tool_name = tool_to_start['name']
                tool_class = tool_to_start['_class']
                tool_config = tool_to_start['config']

                # Merge scheduler-suggested parameters if any
                if best_decision.suggested_parameters:
                    tool_config.update(best_decision.suggested_parameters)

                logger.info(f"Starting {tool_name} (params: {best_decision.suggested_parameters or 'default'})")
                self._run_tool(tool_name, tool_class, tool_config, phase_config)
                completed += 1
            else:
                # Wait for resources or tool completion
                if best_decision:
                    logger.debug(f"Waiting: {best_decision.reason}")

                # Check for critical conditions
                capacity = self.resource_monitor.get_capacity()
                if capacity.pressure_level == 'critical':
                    logger.warning("System under critical pressure, pausing new tools...")

                time.sleep(5)

        logger.info(f"Phase {phase_name} complete: {completed}/{total} tools executed")

    def _run_tool(self, tool_name: str, tool_class, tool_config: dict, phase_config: dict):
        """Execute a single tool with monitoring"""
        start_time = time.time()

        try:
            # Instantiate tool
            tool = tool_class()

            # Build resource estimate for scheduler
            estimate = self.tool_profiles.estimate_tool_resources(
                tool_name,
                tool_config.get('extra_args')
            )
            self.scheduler.register_tool_start(tool_name, estimate)

            # Prepare input files
            input_files = self._resolve_input_files(phase_config)

            # Filter input_files to only those the tool.run() method can accept
            try:
                sig = inspect.signature(tool.run)
                params = sig.parameters
                has_var_keyword = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())
                if not has_var_keyword:
                    accepted = set(name for name, p in params.items()
                                   if p.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD,
                                                inspect.Parameter.KEYWORD_ONLY))
                    standard_args = {'target', 'output_dir', 'tag_manager', 'config'}
                    accepted = accepted - standard_args
                    filtered_input = {k: v for k, v in input_files.items() if k in accepted}
                else:
                    filtered_input = input_files
            except (ValueError, TypeError):
                filtered_input = input_files

            # Run the tool (blocking)
            logger.info(f"Running {tool_name}...")
            result = tool.run(
                target=self.domain,
                output_dir=f"output/{self.domain}",
                tag_manager=self.tag_manager,
                config=tool_config,
                **filtered_input
            )

            # Record completion
            elapsed = time.time() - start_time
            self.logger.tool_complete(tool_name, result, elapsed)

            # Extract tags from tool output
            if hasattr(tool, 'extract_tags') and callable(tool.extract_tags):
                tags = tool.extract_tags(result)
                if tags:
                    for tag, metadata in tags.items():
                        self.tag_manager.add(tag, **metadata) if isinstance(metadata, dict) else self.tag_manager.add(tag)

            # Also call emit_tags if present
            if hasattr(tool, 'emit_tags') and callable(tool.emit_tags):
                tool.emit_tags(result, self.tag_manager)

            # Auto-emit any tags explicitly declared in the API methodology config
            explicit_tags = tool_config.get('tags_emitted', [])
            if isinstance(explicit_tags, list):
                # Ensure we only emit tags if the tool succeeded and returned something
                # We do a basic check here. If result is empty dict, we might not want to emit
                found_something = True
                if isinstance(result, dict):
                    if result.get('count', 1) == 0 or not result.get('results', True):
                        found_something = False
                
                if found_something:
                    for t in explicit_tags:
                        self.tag_manager.add(t, source='methodology_engine')

            # Record in history
            self.completed_tools.append({
                'tool': tool_name,
                'phase': self.current_phase,
                'start_time': start_time,
                'elapsed_seconds': elapsed,
                'status': 'completed'
            })

            # Save checkpoint
            self.save_checkpoint()

            logger.success(f"{tool_name} completed in {elapsed:.1f}s")

        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}")
            self.logger.tool_error(tool_name, e)

            # Record failure so we don't retry
            self.completed_tools.append({
                'tool': tool_name,
                'phase': self.current_phase,
                'start_time': start_time,
                'elapsed_seconds': time.time() - start_time,
                'status': 'failed',
                'error': str(e)
            })
            self.save_checkpoint()

        finally:
            self.scheduler.register_tool_end(tool_name)

    def _resolve_input_files(self, phase_config: dict) -> dict:
        """Resolve input file paths from processed directory"""
        input_mapping = {}
        for key, rel_path in phase_config.get('input_files', {}).items():
            full_path = Path(f"output/{self.domain}/{rel_path}")
            if full_path.exists():
                input_mapping[key] = str(full_path)
            else:
                logger.warning(f"Input file not found: {full_path}")
        return input_mapping

    def run(self):
        """Main execution loop"""
        logger.info(f"Starting HuntForge scan for {self.domain}")
        self.scan_start_time = time.time()

        # Try to resume from checkpoint
        if self.checkpoint_file:
            self.load_checkpoint()

        # Get phases from methodology
        phases = self.methodology.get('phases', {})

        # Execute all phases
        for phase_name, phase_config in phases.items():
            if self._shutdown:
                logger.warning("Shutdown requested, stopping")
                break

            # PHASE 7 SPECIAL HANDLING — human decision point
            if phase_name == 'phase_7_vuln_scan':
                logger.info("Phase 6 complete. Recon is done.")
                self._display_recon_summary()

                try:
                    response = input("\nContinue with vulnerability scanning (Phase 7)? [y/N]: ").strip().lower()
                except EOFError:
                    response = 'n'

                if response != 'y':
                    logger.info("Skipping Phase 7. Scan complete.")
                    break

            self.run_phase(phase_name, phase_config)

            # Post-phase processing: generate declared output files
            self._process_phase_outputs(phase_name, phase_config)

            # Save active tags for reporting
            self.tag_manager.save_to_file(f"output/{self.domain}")

            # Copy active_tags.json to root for report generator
            import shutil
            src = f"output/{self.domain}/processed/active_tags.json"
            dst = f"output/{self.domain}/active_tags.json"
            if os.path.exists(src):
                shutil.copy(src, dst)

            # Free memory between phases
            gc.collect()

        # Scan complete
        elapsed = time.time() - self.scan_start_time
        logger.success(f"Scan completed in {elapsed/3600:.1f} hours")

        # Final checkpoint
        self.save_checkpoint()

        # Generate summary files
        self._generate_summary()

    def _display_recon_summary(self):
        """Show user what was discovered during recon"""
        summary_path = Path(f"output/{self.domain}/processed/scan_summary.json")
        if summary_path.exists():
            with open(summary_path) as f:
                summary = json.load(f)

            print("\n" + "="*60)
            print("RECONNAISSANCE COMPLETE — DISCOVERED ASSETS")
            print("="*60)
            print(f"Target: {self.domain}")
            print(f"Subdomains found: {summary.get('subdomain_count', 0)}")
            print(f"Live hosts: {summary.get('live_host_count', 0)}")
            print(f"Technologies: {', '.join(summary.get('tech_stack', [])[:5])}")
            print(f"Endpoints discovered: {summary.get('endpoint_count', 0)}")
            print(f"Parameters found: {summary.get('parameter_count', 0)}")
            print(f"Critical tags: {', '.join(summary.get('critical_tags', []))}")
            print("="*60)
            print("\nReview the output/ directory before proceeding to Phase 7.")
            print("Vulnerability scanning can be noisy and may trigger security alerts.")
            print("="*60 + "\n")

    def _generate_summary(self):
        """Generate final scan summary"""
        summary = {
            'domain': self.domain,
            'start_time': self.scan_start_time,
            'end_time': time.time(),
            'total_duration_seconds': time.time() - self.scan_start_time,
            'tools_completed': len([t for t in self.completed_tools if t.get('status') == 'completed']),
            'tools_failed': len([t for t in self.completed_tools if t.get('status') == 'failed']),
            'final_tags': self.tag_manager.get_all(),
        }

        summary_path = Path(f"output/{self.domain}/scan_metadata.json")
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)

        logger.info(f"Summary written to {summary_path}")

    def _process_phase_outputs(self, phase_name: str, phase_config: dict):
        """
        Post-phase processing: generate declared output files by merging tool results.
        """
        output_files = phase_config.get('output_files', {})
        if not output_files:
            return

        output_dir = Path(f"output/{self.domain}")
        processed_dir = output_dir / 'processed'
        processed_dir.mkdir(parents=True, exist_ok=True)

        # Handle subdomains_merged (Phase 1)
        if 'subdomains_merged' in output_files:
            merged_path = processed_dir / output_files['subdomains_merged']
            subdomains = set()

            # subfinder.txt (one per line)
            subfinder_path = output_dir / 'raw' / 'subfinder.txt'
            if subfinder_path.exists():
                try:
                    with open(subfinder_path) as f:
                        for line in f:
                            line = line.strip().lower()
                            if line and '.' in line:
                                subdomains.add(line)
                except Exception:
                    pass

            # amass.txt (one per line)
            amass_path = output_dir / 'raw' / 'amass.txt'
            if amass_path.exists():
                try:
                    with open(amass_path) as f:
                        for line in f:
                            line = line.strip().lower()
                            if line and '.' in line:
                                subdomains.add(line)
                except Exception:
                    pass

            # crtsh.json (list of strings)
            crtsh_path = output_dir / 'raw' / 'crtsh.json'
            if crtsh_path.exists():
                try:
                    with open(crtsh_path) as f:
                        data = json.load(f)
                        for entry in data:
                            if isinstance(entry, str):
                                subdomains.add(entry.strip().lower())
                except Exception:
                    pass

            # Write merged list
            if subdomains:
                with open(merged_path, 'w') as f:
                    for sub in sorted(subdomains):
                        f.write(sub + '\n')
                logger.success(f"Merged {len(subdomains)} unique subdomains -> {merged_path}")
            else:
                logger.warning("No subdomains found from Phase 1 tools")
                merged_path.write_text('')


def main():
    """CLI entry point for v2 orchestrator"""
    import argparse

    parser = argparse.ArgumentParser(description="HuntForge Orchestrator V2 (Resource-Aware)")
    parser.add_argument("domain", help="Target domain")
    parser.add_argument("--methodology", default="config/default_methodology.yaml",
                       help="Path to methodology YAML")
    parser.add_argument("--no-checkpoint", action="store_true",
                       help="Disable checkpoint/resume")
    parser.add_argument("--checkpoint-file",
                       help="Path to checkpoint file (default: output/{domain}/checkpoint.json)")

    args = parser.parse_args()

    orch = OrchestratorV2(
        domain=args.domain,
        methodology_path=args.methodology,
        checkpoint_file=None if args.no_checkpoint else (args.checkpoint_file or None),
        adaptive=True
    )

    try:
        orch.run()
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        raise


if __name__ == "__main__":
    logger.remove()
    logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | {message}")
    main()
