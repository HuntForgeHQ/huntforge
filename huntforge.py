#!/usr/bin/env python3
"""
HuntForge CLI Entry Point

Responsibilities:
- Parse CLI arguments
- Display Rich terminal UI
- Handle AI prompt → methodology generation
- Load configuration
- Validate scope
- Initialize orchestrator
- Launch scans
"""

import argparse
import os
import sys
import yaml
import json
from pathlib import Path
from dotenv import load_dotenv

# Auto-load .env from project root on every CLI invocation
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from core.orchestrator_v2 import OrchestratorV2 as Orchestrator
from core.scope_enforcer import ScopeEnforcer
from core.scan_history import ScanHistory
from core.tag_manager import TagManager

from ai.methodology_engine import generate_methodology
from ai.report_generator import generate_report as ai_generate_report

# --------------------------------------------------------
# Global Console
# --------------------------------------------------------

console = Console()

# --------------------------------------------------------
# Constants
# --------------------------------------------------------

CONFIG_DIR = os.path.expanduser("~/.huntforge")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_METHOD = "config/default_methodology.yaml"

# --------------------------------------------------------
# UI Components
# --------------------------------------------------------

def print_banner():

    console.print(
        Panel.fit(
            "[bold cyan]HuntForge v1.0[/bold cyan]\n"
            "[dim]AI-Powered Bug Bounty Recon Framework[/dim]",
            border_style="cyan"
        )
    )


def print_scan_summary(domain, profile, methodology):

    table = Table(title="Scan Configuration")

    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Target", domain)
    table.add_row("Profile", profile)
    table.add_row("Methodology", methodology)

    console.print(table)


# --------------------------------------------------------
# Config Loader
# --------------------------------------------------------

def load_user_config():

    if not os.path.exists(CONFIG_FILE):
        return {}

    try:
        with open(CONFIG_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


# --------------------------------------------------------
# AI Methodology Generation
# --------------------------------------------------------

def handle_ai_prompt(prompt):

    console.print("\n[yellow]Generating methodology using AI...[/yellow]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}")
    ) as progress:

        progress.add_task("Contacting AI engine...", total=None)

        method = generate_methodology(prompt)

    if not method:
        console.print("[red]AI failed to generate methodology[/red]")
        sys.exit(1)

    output_path = "config/generated_methodology.yaml"

    os.makedirs("config", exist_ok=True)

    with open(output_path, "w") as f:
        yaml.dump(method, f)

    console.print(
        f"[green]Methodology generated:[/green] {output_path}"
    )


# --------------------------------------------------------
# Scan Execution
# --------------------------------------------------------

def run_scan(domain, methodology_path, profile):

    if not os.path.exists(methodology_path):
        console.print(
            f"[red]Methodology file not found:[/red] {methodology_path}"
        )
        sys.exit(1)

    print_scan_summary(domain, profile, methodology_path)

    # --------------------------------------------------
    # Scope Enforcement (Member 4 component)
    # --------------------------------------------------

    scope = ScopeEnforcer()

    allowed, reason, program = scope.check(domain)

    if not allowed:

        console.print(
            f"[red]Target blocked by scope enforcement[/red]\n"
            f"Reason: {reason}"
        )

        console.print(
            "\n[yellow]If you own this domain you must manually approve it.[/yellow]"
        )

        confirm = console.input(
            f"Type '{domain}' to confirm ownership: "
        )

        if not scope.approve_manual(domain, confirm):
            console.print("[red]Approval failed. Aborting.[/red]")
            sys.exit(1)

    else:

        console.print(
            f"[green]Scope check passed[/green] ({reason})"
        )

    # --------------------------------------------------
    # Start Scan
    # --------------------------------------------------

    console.print("\n[cyan]Launching HuntForge Orchestrator[/cyan]\n")

    history = ScanHistory()
    scan_id = history.record_start(domain, f"output/{domain}")
    status = "FAILED"

    try:

        orch = Orchestrator(
            domain=domain,
            methodology_path=methodology_path,
            profile=profile,
        )

        orch.run()
        status = "COMPLETED"

    except KeyboardInterrupt:

        console.print("\n[yellow]Scan interrupted by user[/yellow]")
        status = "INTERRUPTED"

    except Exception as e:

        console.print(
            f"\n[red]Fatal error:[/red] {e}"
        )
        status = "FAILED"
        sys.exit(1)
        
    finally:
        tag_count = len(orch.tag_manager.get_all()) if 'orch' in locals() else 0
        history.record_end(scan_id, status, tag_count)


# --------------------------------------------------------
# Report Generator
# --------------------------------------------------------

def generate_report(domain):

    output_dir = f"output/{domain}"
    tags_file = os.path.join(output_dir, "active_tags.json")

    if not os.path.exists(tags_file):
        console.print("[red]No scan data found for this domain[/red]")
        return

    # Reconstruct TagManager state
    tm = TagManager()
    with open(tags_file, 'r') as f:
        tm.tags = json.load(f)

    console.print("[cyan]Contacting Claude API for executive report...[/cyan]")
    ai_generate_report(domain, tm, output_dir)
    
    report_path = os.path.join(output_dir, 'logs', 'ai_report.md')
    if os.path.exists(report_path):
        console.print(f"[green]Report ready:[/green] {report_path}")


# --------------------------------------------------------
# Resume Scan
# --------------------------------------------------------

def resume_scan(domain):

    console.print(
        f"[cyan]Resuming scan for {domain}[/cyan]"
    )

    console.print(
        "[yellow]Resume functionality coming in v1.1[/yellow]"
    )


# --------------------------------------------------------
# CLI Argument Parser
# --------------------------------------------------------

def build_parser():

    parser = argparse.ArgumentParser(
        prog="huntforge",
        description="AI Powered Bug Bounty Recon Framework"
    )

    sub = parser.add_subparsers(dest="command")

    # --------------------------------------------------
    # scan
    # --------------------------------------------------

    scan = sub.add_parser(
        "scan",
        help="Run a reconnaissance scan"
    )

    scan.add_argument(
        "domain",
        help="Target domain"
    )

    scan.add_argument(
        "--profile",
        choices=["lite", "medium", "full", "professional"],
        default="professional",
        help="Machine resource profile (lite: 4-8GB, medium: 8-16GB, full: 16GB+, professional: 8-16GB optimized)"
    )

    scan.add_argument(
        "--methodology",
        default=DEFAULT_METHOD,
        help="Path to YAML methodology file"
    )

    # --------------------------------------------------
    # ai
    # --------------------------------------------------

    ai = sub.add_parser(
        "ai",
        help="Generate scan methodology using AI"
    )

    ai.add_argument(
        "prompt",
        help="Instruction prompt for AI"
    )

    # --------------------------------------------------
    # report
    # --------------------------------------------------

    report = sub.add_parser(
        "report",
        help="Generate or open report"
    )

    report.add_argument(
        "domain"
    )

    # --------------------------------------------------
    # resume
    # --------------------------------------------------

    resume = sub.add_parser(
        "resume",
        help="Resume a previous scan"
    )

    resume.add_argument(
        "domain"
    )

    return parser


# --------------------------------------------------------
# Main Entry
# --------------------------------------------------------

def main():

    print_banner()

    parser = build_parser()

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "scan":

        run_scan(
            domain=args.domain,
            methodology_path=args.methodology,
            profile=args.profile
        )

    elif args.command == "ai":

        handle_ai_prompt(
            prompt=args.prompt
        )

    elif args.command == "report":

        generate_report(
            domain=args.domain
        )

    elif args.command == "resume":

        resume_scan(
            domain=args.domain
        )


# --------------------------------------------------------

if __name__ == "__main__":
    main()