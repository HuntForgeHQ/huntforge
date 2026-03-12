# modules/passive/subfinder.py
# Author         : Member 2
# Responsibility : Run subfinder, parse subdomains,
#                  set tags on tag_manager.
# Inherits from  : BaseModule
# Raises         : OutputParseError (its own output parsing)
# Lets bubble    : BinaryNotFoundError, ToolTimeoutError,
#                  ToolExecutionError → orchestrator catches these
# ------------------------------------------------------------

import os
from huntforge.core.base_module import BaseModule
from core.exceptions  import EmptyOutputError, OutputParseError


class Subfinder(BaseModule):

    def build_command(self, target: str, output_file: str) -> list:
        """
        Builds the subfinder shell command.
        Reads optional switches from self.config via self._cfg().
        """
        cmd = ['subfinder', '-d', target, '-o', output_file, '-silent']

        # Optional: recursive subdomain enumeration
        if self._cfg('recursive', default=False):
            cmd += ['-recursive']

        # Optional: timeout per source (default 30s)
        cmd += ['-timeout', str(self._cfg('timeout', default=30))]

        # Optional: limit number of results
        max_results = self._cfg('max_results')
        if max_results:
            cmd += ['-max-results', str(max_results)]

        # Optional: specific sources only
        sources = self._cfg('sources')
        if sources:
            cmd += ['-sources', ','.join(sources)]

        # Optional: number of threads
        cmd += ['-t', str(self._cfg('threads', default=10))]

        return cmd

    def run(self, target: str, output_dir: str,
            tag_manager, config: dict = None) -> dict:
        """
        Runs subfinder against target.
        Returns standard result dict.
        """
        # Store config so _cfg() and build_command() can read it
        self.config  = config or {}
        output_file  = os.path.join(output_dir, 'raw', 'subfinder.txt')

        # ── Ensure output directory exists ───────────────────────
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        # ── Build and run the command ─────────────────────────────
        command = self.build_command(target, output_file)

        # _run_subprocess() handles:
        #   BinaryNotFoundError  → subfinder not installed
        #   ToolTimeoutError     → subfinder hung
        #   ToolExecutionError   → subfinder bad exit code
        # We do NOT catch these here.
        # They bubble up to orchestrator automatically.
        self._run_subprocess(command)

        # ── Parse the output file ─────────────────────────────────
        # We DO handle our own output parsing here.
        # EmptyOutputError means subfinder found zero subdomains.
        # That is completely normal — not a crash.
        try:
            content    = self._read_output_file(output_file)
            subdomains = self._parse(content)

        except EmptyOutputError:
            # Target has no subdomains — return empty results
            # This is normal. Don't crash. Don't bubble.
            subdomains = []

        return {
            'results':       subdomains,
            'count':         len(subdomains),
            'requests_made': self.estimated_requests()
        }

    def emit_tags(self, result: dict, tag_manager) -> None:
        """
        Sets tags based on what subfinder found.
        Called by orchestrator after run() succeeds.
        """
        if result['count'] == 0:
            return

        tag_manager.add(
            'has_subdomains',
            confidence = 'high',
            evidence   = result['results'][:5],
            source     = 'subfinder'
        )

        # Check for interesting subdomains
        subdomains = result['results']

        if any('admin'   in s for s in subdomains):
            tag_manager.add('has_admin_subdomain',
                            confidence='medium', source='subfinder')

        if any('api'     in s for s in subdomains):
            tag_manager.add('has_api_subdomain',
                            confidence='medium', source='subfinder')

        if any('dev'     in s or 'staging' in s for s in subdomains):
            tag_manager.add('has_dev_subdomain',
                            confidence='medium', source='subfinder')

        if any('mail'    in s for s in subdomains):
            tag_manager.add('has_mail_subdomain',
                            confidence='low', source='subfinder')

    def estimated_requests(self) -> int:
        return 40

    # ── Private helper ────────────────────────────────────────────

    def _parse(self, content: str) -> list:
        """
        Parse subfinder plain text output.
        One subdomain per line.

        Raises OutputParseError if content is completely unparseable.
        In practice subfinder output is very simple so this
        rarely triggers — but it's here for safety.
        """
        try:
            subdomains = [
                line.strip()
                for line in content.splitlines()
                if line.strip() and '.' in line  # basic sanity check
            ]
            return subdomains

        except Exception as e:
            raise OutputParseError(
                f"Could not parse subfinder output: {e}",
                tool = 'subfinder'
            )