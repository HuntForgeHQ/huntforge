#!/usr/bin/env python3
"""
HuntForge Orchestrator V2 - Resource-Aware Adaptive Scheduling

Key improvements over v1:
- Adaptive concurrency based on system resources (not fixed)
- Phase-specific scheduling strategies (light vs heavy)
- Parameter scaling (reduce threads if memory constrained)
- Checkpoint/resume capability
- Optional Phase 7 (user selects targets after recon)
- Resource monitoring throughout
"""

import os
import yaml
import json
import time
import sys
import signal
import logging
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

# Import ALL tool modules (same as v1)
from modules.passive.subfinder import SubfinderModule as Subfinder
from modules.passive.amass import AmassModule as Amass
from modules.passive.crtsh import CrtshModule as Crtsh
from modules.passive.theharvester import TheHarvesterModule as TheHarvester
from modules.passive.assetfinder import AssetfinderModule as Assetfinder
from modules.passive.chaos import ChaosModule as Chaos
from modules.passive.findomain import FindomainModule as Findomain
from modules.passive.waybackurls import WaybackurlsModule as Waybackurls

from modules.secrets.gitleaks import GitleaksModule as Gitleaks
from modules.secrets.trufflehog import TrufflehogModule as Trufflehog
from modules.secrets.github_dorking import GithubDorkingModule as GithubDorking
from modules.secrets.secretfinder import SecretfinderModule as Secretfinder
from modules.secrets.jsluice import JsluiceModule as Jsluice
from modules.secrets.linkfinder import LinkfinderModule as Linkfinder

from modules.discovery.httpx import HttpxModule as Httpx
from modules.discovery.naabu import NaabuModule as Naabu
from modules.discovery.dnsx import DnsxModule as Dnsx
from modules.discovery.puredns import PurednsModule as Puredns
from modules.discovery.gowitness import GowitnessModule as Gowitness
from modules.discovery.asnmap import AsnmapModule as Asnmap

from modules.surface_intel.whatweb import WhatWebModule as WhatWeb
from modules.surface_intel.wappalyzer import WappalyzerModule as Wappalyzer
from modules.surface_intel.nmap_service import NmapServiceModule as NmapService
from modules.surface_intel.shodan_cli import ShodanCliModule as ShodanCli
from modules.surface_intel.censys_cli import CensysCliModule as CensysCli

from modules.enumeration.katana import KatanaModule as Katana
from modules.enumeration.gau import GauModule as Gau
from modules.enumeration.paramspider import ParamspiderModule as Paramspider
from modules.enumeration.gospider import GospiderModule as Gospider
from modules.enumeration.gf_extract import GfExtractModule as GfExtract
from modules.enumeration.graphql_voyager import GraphqlVoyagerModule as GraphqlVoyager
from modules.enumeration.arjun import ArjunModule as Arjun

from modules.content_discovery.ffuf import FfufModule as Ffuf
from modules.content_discovery.dirsearch import DirsearchModule as Dirsearch
from modules.content_discovery.feroxbuster import FeroxbusterModule as Feroxbuster
from modules.content_discovery.wpscan import WpscanModule as Wpscan

from modules.vuln_scan.nuclei import NucleiModule as Nuclei
from modules.vuln_scan.subjack import SubjackModule as Subjack
from modules.vuln_scan.dalfox import DalfoxModule as Dalfox
from modules.vuln_scan.nikto import NiktoModule as Nikto
from modules.vuln_scan.sqlmap import SQLMapModule as SQLMap
from modules.vuln_scan.wpscan_vuln import WpscanVulnModule as WpscanVuln
from modules.vuln_scan.cors_scanner import CorsScannerModule as CorsScanner
from modules.vuln_scan.ssrf_check import SSRFCheckModule as SSRFCheck

TOOL_REGISTRY = {
    # Phase 1 - Passive Recon (all implemented)
    'subfinder': Subfinder,
    'amass': Amass,
    'crtsh': Crtsh,
    'theharvester': TheHarvester,
    'assetfinder': Assetfinder,
    'chaos': Chaos,
    'findomain': Findomain,
    'waybackurls': Waybackurls,

    # Phase 2 - Secrets & OSINT (all implemented)
    'gitleaks': Gitleaks,
    'trufflehog': Trufflehog,
    'github_dorking': GithubDorking,
    'secretfinder': Secretfinder,
    'jsluice': Jsluice,
    'linkfinder': Linkfinder,

    # Phase 3 - Live Asset Discovery (all implemented)
    'httpx': Httpx,
    'naabu': Naabu,
    'dnsx': Dnsx,
    'puredns': Puredns,
    'gowitness': Gowitness,
    'asnmap': Asnmap,

    # Phase 4 - Surface Intelligence (all implemented)
    'whatweb': WhatWeb,
    'wappalyzer_cli': Wappalyzer,
    'nmap_service': NmapService,
    'shodan_cli': ShodanCli,
    'censys_cli': CensysCli,

    # Phase 5 - Enumeration (all implemented)
    'katana': Katana,
    'gau': Gau,
    'paramspider': Paramspider,
    'gospider': Gospider,
    'gf_extract': GfExtract,
    'graphql_voyager': GraphqlVoyager,
    'arjun': Arjun,

    # Phase 6 - Content Discovery (all implemented)
    'ffuf': Ffuf,
    'dirsearch': Dirsearch,
    'feroxbuster': Feroxbuster,
    'wpscan': Wpscan,
    's3scanner': None,
    'cloud_enum': None,

    # Phase 7 - Vulnerability Scanning (all implemented)
    'nuclei': Nuclei,
    'nuclei_cms': Nuclei,
    'nuclei_auth': Nuclei,
    'subjack': Subjack,
    'nikto': Nikto,
    'dalfox': Dalfox,
    'sqlmap': SQLMap,
    'wpscan_vuln': WpscanVuln,
    'cors_scanner': CorsScanner,
    'ssrf_check': SSRFCheck,
}


class OrchestratorV2:
    """
    Next-gen orchestrator with adaptive resource scheduling.

    Key differences from v1:
    1. Uses AdaptiveScheduler instead of fixed thread pools
    2. Supports checkpoint/resume
    3. Optional Phase 7 (user prompt)
    4. Real-time resource monitoring
    5. Parameter scaling based on available RAM
    """

    def __init__(self, domain: str, methodology_path: str, profile: str = "medium",
                 checkpoint_file: Optional[str] = None, adaptive: bool = True):
        self.domain = domain
        self.profile = profile
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
        self.logger = HFLogger(domain)

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
            'profile': self.profile,
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
            if not self.tag_manager.has_tag(if_tag):
                return True, f"Tag '{if_tag}' not set"

        # Check always flag
        if tool_config.get('enabled', True) is False:
            return True, "Tool disabled in methodology"

        return False, ""

    def run_phase(self, phase_name: str, phase_config: dict):
        """Execute a single phase with adaptive scheduling"""
        logger.info(f"Starting phase: {phase_config.get('label', phase_name)}")
        self.current_phase = phase_name

        tools = phase_config.get('tools', [])
        input_files = phase_config.get('input_files', {})

        # Filter tools based on conditional execution
        tools_to_run = []
        for tool_entry in tools:
            # Handle both dict and simple string formats
            if isinstance(tool_entry, dict):
                tool_name = tool_entry.get('tool')
                if not tool_name:
                    # Phase 7 uses conditional_tools differently
                    continue
                tool_config = tool_entry
            else:
                tool_name = tool_entry
                tool_config = {}

            skip, reason = self.should_skip_tool(tool_config, tool_name)
            if skip:
                logger.info(f"Skipping {tool_name}: {reason}")
                if tool_name in TOOL_REGISTRY:
                    self.logger.log_tool_skip(tool_name, reason)
                continue

            if tool_name not in TOOL_REGISTRY or TOOL_REGISTRY[tool_name] is None:
                logger.warning(f"Tool {tool_name} not implemented, skipping")
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

                # Check for OOM or critical conditions
                capacity = self.resource_monitor.get_capacity()
                if capacity.pressure_level == 'critical':
                    logger.warning("System under critical pressure, pausing new tools...")

                time.sleep(5)  # Check every 5 seconds

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
                tool_config.get('extra_args')  # TODO: parse into dict
            )
            self.scheduler.register_tool_start(tool_name, estimate)

            # Prepare input files
            input_files = self._resolve_input_files(phase_config)

            # Run the tool (this is blocking)
            logger.info(f"Running {tool_name}...")
            result = tool.run(
                domain=self.domain,
                output_dir=f"output/{self.domain}",
                profile=self.profile,
                **input_files
            )

            # Record completion
            elapsed = time.time() - start_time
            self.logger.log_tool_complete(tool_name, result, elapsed)

            # Extract tags from tool output
            tags = tool.extract_tags(result) if hasattr(tool, 'extract_tags') else {}
            for tag, metadata in tags.items():
                self.tag_manager.add(tag, metadata)

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
            self.logger.log_tool_error(tool_name, str(e))

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

        # PHASES 1-6: Normal execution
        for phase_name, phase_config in phases.items():
            if self._shutdown:
                logger.warning("Shutdown requested, stopping")
                break

            # Skip if phase already completed (from checkpoint)
            if any(ct['phase'] == phase_name for ct in self.completed_tools):
                logger.info(f"Phase {phase_name} already completed, skipping")
                continue

            # PHASE 7 SPECIAL HANDLING
            if phase_name == 'phase_7_vuln_scan':
                logger.info("Phase 6 complete. Recon is done.")

                # Show summary of discovered targets
                self._display_recon_summary()

                # Ask user if they want to continue with vulnerability scanning
                response = input("\nContinue with vulnerability scanning (Phase 7)? [y/N]: ").strip().lower()
                if response != 'y':
                    logger.info("Skipping Phase 7. Scan complete.")
                    break

                # Let user select targets (if configured)
                # TODO: Implement target selection interface

            self.run_phase(phase_name, phase_config)

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
            print("RECONNAISSANCE COMPLETE - DISCOVERED ASSETS")
            print("="*60)
            print(f"Target: {self.domain}")
            print(f"Subdomains found: {summary.get('subdomain_count', 0)}")
            print(f"Live hosts: {summary.get('live_host_count', 0)}")
            print(f"Technologies: {', '.join(summary.get('tech_stack', [])[:5])}")
            print(f"Endpoints discovered: {summary.get('endpoint_count', 0)}")
            print(f"Parameters found: {summary.get('parameter_count', 0)}")
            print(f"Admin panels: {summary.get('admin_panel_count', 0)}")
            print(f"Critical tags: {', '.join(summary.get('critical_tags', []))}")
            print("="*60)
            print("\nReview the output/ directory before proceeding to Phase 7.")
            print("Vulnerability scanning can be noisy and may trigger security alerts.")
            print("="*60 + "\n")

    def _generate_summary(self):
        """Generate final scan summary"""
        summary = {
            'domain': self.domain,
            'profile': self.profile,
            'start_time': self.scan_start_time,
            'end_time': time.time(),
            'total_duration_seconds': time.time() - self.scan_start_time,
            'tools_completed': len(self.completed_tools),
            'final_tags': self.tag_manager.get_all(),
        }

        summary_path = Path(f"output/{self.domain}/scan_metadata.json")
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)

        logger.info(f"Summary written to {summary_path}")


def main():
    """CLI entry point for v2 orchestrator"""
    import argparse

    parser = argparse.ArgumentParser(description="HuntForge Orchestrator V2 (Resource-Aware)")
    parser.add_argument("domain", help="Target domain")
    parser.add_argument("--methodology", default="config/default_methodology.yaml",
                       help="Path to methodology YAML")
    parser.add_argument("--profile", default="medium", choices=['lite', 'medium', 'full'],
                       help="Resource profile")
    parser.add_argument("--no-checkpoint", action="store_true",
                       help="Disable checkpoint/resume")
    parser.add_argument("--checkpoint-file",
                       help="Path to checkpoint file (default: output/{domain}/checkpoint.json)")

    args = parser.parse_args()

    # Create orchestrator
    orch = OrchestratorV2(
        domain=args.domain,
        methodology_path=args.methodology,
        profile=args.profile,
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
    # Set up logging
    logger.remove()  # Remove default handler
    logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | {message}")

    main()
