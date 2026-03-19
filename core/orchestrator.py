# core/orchestrator.py
# Author         : Member 1
# Responsibility : Executes the methodology phases. Runs the 4-Gate check.
# ------------------------------------------------------------

import os
import yaml
import time
import json
from loguru import logger

from core.exceptions import (
    HuntForgeError, DockerNotRunningError, BudgetExceededError,
    BinaryNotFoundError, ToolTimeoutError, ToolExecutionError
)
from core.docker_runner import DockerRunner
from core.tag_manager import TagManager
from core.budget_tracker import BudgetTracker
from core.resource_monitor import ResourceMonitor
from core.hf_logger import HFLogger

# Tool Registry — map YAML config names to Python classes here.
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

TOOL_REGISTRY = {
    'subfinder': Subfinder,
    'amass': Amass,
    'crtsh': Crtsh,
    'theharvester': TheHarvester,
    'assetfinder': Assetfinder,
    'chaos': Chaos,
    'findomain': Findomain,
    'waybackurls': Waybackurls,
    
    'gitleaks': Gitleaks,
    'trufflehog': Trufflehog,
    'github_dorking': GithubDorking,
    'secretfinder': Secretfinder,
    'jsluice': Jsluice,
    'linkfinder': Linkfinder,
    
    'httpx': Httpx,
    'naabu': Naabu,
    'dnsx': Dnsx,
    'puredns': Puredns,
    'gowitness': Gowitness,
    'asnmap': Asnmap,
    
    'whatweb': WhatWeb,
    'wappalyzer': Wappalyzer,
    'nmap_service': NmapService,
    'shodan_cli': ShodanCli,
    'censys_cli': CensysCli,
    
    'katana': Katana,
    'gau': Gau,
    'paramspider': Paramspider,
    'gospider': Gospider,
    'gf_extract': GfExtract,
    'graphql_voyager': GraphqlVoyager,
    'arjun': Arjun,
    
    'ffuf': Ffuf,
    'dirsearch': Dirsearch,
    'feroxbuster': Feroxbuster,
    'wpscan': Wpscan,
    
    'nuclei': Nuclei,
    'subjack': Subjack,
    'dalfox': Dalfox
}


class Orchestrator:
    """
    Heart of HuntForge. Runs the entire scan based on YAML methodology.
    """

    def __init__(self, domain: str, methodology_path: str, profile: str = 'mid'):
        self.domain = domain
        self.output_dir = os.path.join('output', domain)
        
        # Load config
        with open(methodology_path, 'r') as f:
            self.methodology = yaml.safe_load(f)
            
        # Extract budget config
        budget_cfg = self.methodology.get('budget', {})
        self.budget_tracker = BudgetTracker(
            max_requests=budget_cfg.get('max_requests'),
            max_time_minutes=budget_cfg.get('max_time_minutes')
        )

        # Setup Core Components
        self.docker_runner = DockerRunner()
        self.tag_manager = TagManager()
        self.hf_log = HFLogger(self.output_dir)
        
        # Resource monitor thresholds based on profile
        if profile == 'low':
            self.resource_monitor = ResourceMonitor(cpu_threshold=60, ram_threshold=70)
        elif profile == 'high':
            self.resource_monitor = ResourceMonitor(cpu_threshold=95, ram_threshold=95)
        else: # mid
            self.resource_monitor = ResourceMonitor(cpu_threshold=80, ram_threshold=85)

        # Ensure output structure exists
        for d in ['raw', 'processed', 'logs']:
            os.makedirs(os.path.join(self.output_dir, d), exist_ok=True)

    def run(self):
        """Main execution loop for all phases."""
        logger.info(f"Starting HuntForge scan on {self.domain}")
        self.hf_log.scan_start(self.domain)
        
        try:
            # Pre-flight check
            if not self.docker_runner.is_container_running():
                raise DockerNotRunningError("Container 'huntforge-kali' must be running.")

            phases = self.methodology.get('phases', {})
            
            for phase_name, phase_config in phases.items():
                try:
                    self._run_phase(phase_name, phase_config)
                except BudgetExceededError as e:
                    logger.warning(f"Scan aborted: {e}")
                    self.hf_log.tool_error('orchestrator', e)
                    break
                except Exception as e:
                    logger.error(f"Phase {phase_name} failed: {e}")
                    
        finally:
            # End of scan tasks
            self.tag_manager.save_to_file(self.output_dir)
            self.hf_log.scan_end(self.tag_manager.get_all())
            
            # Save budget status
            budget_path = os.path.join(self.output_dir, 'processed', 'budget_status.json')
            with open(budget_path, 'w') as f:
                json.dump(self.budget_tracker.log_status(), f, indent=2)

    def _run_phase(self, phase_name: str, phase_config: dict):
        """Execute a single phase."""
        label = phase_config.get('label', phase_name)
        self.hf_log.phase_start(phase_name, label)
        logger.info(f"--- Phase: {label} ---")
        
        # Tools can be in 'tools' or 'conditional_tools'
        tools = phase_config.get('tools', {})
        conditional_tools = phase_config.get('conditional_tools', [])
        
        # Normalize into a list of tuples: (tool_name, tool_config)
        tool_queue = []
        if isinstance(tools, dict):
            for t_name, t_cfg in tools.items():
                tool_queue.append((t_name, t_cfg))
        
        for ct in conditional_tools:
            t_name = ct.get('tool')
            tool_queue.append((t_name, ct))
            
        for tool_name, tool_config in tool_queue:
            if not tool_config.get('enabled', True):
                self.hf_log.tool_skipped(tool_name, "disabled in methodology")
                continue
                
            self._run_tool(tool_name, tool_config, phase_config)
            
        self.tag_manager.save_to_file(self.output_dir)
        self.hf_log.phase_end(phase_name)

    def _run_tool(self, tool_name: str, tool_config: dict, phase_config: dict):
        """Runs the 4-Gate check and executes a tool."""
        
        # 1. Implementation Check (Is it built?)
        if tool_name not in TOOL_REGISTRY:
            self.hf_log.tool_skipped(tool_name, "Tool not implemented yet in Python")
            return
            
        module_class = TOOL_REGISTRY[tool_name]
        module_instance = module_class(docker_runner=self.docker_runner)
        
        # 2. Gate 1: Tag Check
        if not tool_config.get('always', False):
            if_tag = tool_config.get('if_tag')
            if if_tag:
                min_conf = tool_config.get('min_confidence', 'low')
                if not self.tag_manager.has(if_tag, min_confidence=min_conf):
                    self.hf_log.tool_skipped(tool_name, f"tag={if_tag} conf < {min_conf}")
                    return
        
        # 3. Gate 2: Budget Check
        est_req = module_instance.estimated_requests()
        if phase_config.get('budget_applies', True):
            if not self.budget_tracker.within_limits(est_req):
                self.hf_log.tool_skipped(tool_name, "budget_exceeded: tool would blow budget limits")
                return
                
        # 4. Gate 3: Resource Check (Spin until safe or timeout)
        retries = 10
        while not self.resource_monitor.ok() and retries > 0:
            logger.debug(f"Host resources too high, waiting before running {tool_name}...")
            time.sleep(5)
            retries -= 1
            
        if not self.resource_monitor.ok():
            self.hf_log.tool_skipped(tool_name, "resource_monitor: host CPU/RAM critically high, skipping tool for safety")
            return

        # 5. Gate 4: Execution
        self.hf_log.tool_start(tool_name)
        logger.info(f"Running tool: {tool_name}")
        
        try:
            start_time = time.time()
            result = module_instance.run(self.domain, self.output_dir, self.tag_manager, config=tool_config.get('config', {}))
            
            # 6. Post-execution: Charge Budget & Emit Tags
            self.budget_tracker.add_requests(result.get('requests_made', 0))
            module_instance.emit_tags(result, self.tag_manager)
            
            # Log completion
            count = result.get('count', 0)
            self.hf_log.tool_complete(tool_name, count)
            logger.success(f"{tool_name} completed in {time.time() - start_time:.1f}s — Found {count} items")
            
            # Hook the tag logic so HFLogger knows what was added by this tool
            # (In reality TagManager updates are silent; we can log tag_set directly inside emit_tags or here.
            #  For now HFLogger doesn't auto-hook TagManager, so this is just the required call to tool_complete)
            
        except (HuntForgeError, Exception) as e:
            self.hf_log.tool_error(tool_name, e)
            logger.error(f"Error in {tool_name}: {e}")
