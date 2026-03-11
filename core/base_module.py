# core/base_module.py
# Author      : Member 1
# Responsibility : Define the interface every tool module must follow.
#                 Handle all subprocess-level errors in one place.
#                 Member 2 inherits this — never rewrites subprocess logic.
# ------------------------------------------------------------

import subprocess
import os
from core.exceptions import (
    BinaryNotFoundError,
    ToolTimeoutError,
    ToolExecutionError,
    EmptyOutputError
)


class BaseModule:
    """
    Parent class for every tool module in HuntForge.

    Member 2 creates child classes like this:

        from core.base_module import BaseModule

        class Subfinder(BaseModule):
            def build_command(self, target, output_file): ...
            def run(self, target, output_dir, tag_manager, config): ...
            def emit_tags(self, result, tag_manager): ...
            def estimated_requests(self): ...

    The orchestrator calls ONLY these 4 methods on every module:
        module.run()
        module.emit_tags()
        module.estimated_requests()
        module.build_command()  (called internally by run())

    Subprocess execution and output file reading are handled
    by the two helpers below. Member 2 calls these helpers —
    they never write subprocess.run() themselves.
    """

    # ── 4 Methods Member 2 Must Implement ────────────────────────

    def build_command(self, target: str, output_file: str) -> list:
        """
        Returns the exact shell command to run as a list of strings.

        Member 2 MUST override this. No safe default exists.

        Example return value:
            ['subfinder', '-d', 'example.com',
             '-o', 'output/example.com/raw/subfinder.txt',
             '-silent']

        The command list is passed directly to subprocess.run()
        so every element must be a separate string — never one
        long string with spaces.

        Wrong:  ['subfinder -d example.com -silent']
        Right:  ['subfinder', '-d', 'example.com', '-silent']
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement build_command(). "
            f"Return the shell command as a list of strings."
        )

    def run(self, target: str, output_dir: str,
            tag_manager, config: dict = None) -> dict:
        """
        Execute the tool and return results in standard format.

        Member 2 MUST override this. No safe default exists.

        Parameters:
            target      : domain being scanned e.g. 'example.com'
            output_dir  : base output path e.g. 'output/example.com'
            tag_manager : TagManager instance — read tags to make
                          decisions, don't set tags here (use emit_tags)
            config      : dict from YAML config block — optional switches

        Must ALWAYS return this exact shape:
            {
                'results':       list,   # parsed findings
                'count':         int,    # len(results)
                'requests_made': int     # for budget tracking
            }

        Never return None. Never return a different dict shape.
        If the tool found nothing — return count=0 and results=[].
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement run(). "
            f"Must return dict with keys: results, count, requests_made."
        )

    def emit_tags(self, result: dict, tag_manager) -> None:
        """
        Read the result dict and set tags on tag_manager.

        Member 2 SHOULD override this for most tools.
        Default: does nothing. Safe to leave as-is if tool
        doesn't produce findings that other phases depend on.

        Called by orchestrator AFTER run() completes successfully.
        Never called if run() raised an exception.

        Example:
            def emit_tags(self, result, tag_manager):
                if result['count'] > 0:
                    tag_manager.add(
                        'has_subdomains',
                        confidence = 'high',
                        evidence   = result['results'][:5]
                    )
        """
        pass

    def estimated_requests(self) -> int:
        """
        Return a rough estimate of HTTP requests this tool will make.
        Used by BudgetTracker in Gate 3 before deciding to run the tool.

        Member 2 SHOULD override this.
        Default: 100 — conservative safe estimate.

        Be honest — underestimating wastes budget on surprise overruns.
        Overestimating causes the gate to skip the tool unnecessarily.
        """
        return 100

    # ── 2 Helpers Member 2 Uses Inside run() ─────────────────────
    # Member 2 calls these. They never rewrite this logic themselves.

    def _run_subprocess(self, command: list) -> str:
        """
        Execute a shell command and return its stdout as a string.

        Handles all subprocess-level errors and raises clean
        HuntForge exceptions. Member 2 does NOT wrap this in
        try/except — those exceptions bubble to the orchestrator.

        Parameters:
            command : list of strings e.g.
                      ['subfinder', '-d', 'example.com', '-silent']

        Returns:
            stdout of the command as a plain string

        Raises:
            BinaryNotFoundError  : tool binary not installed
            ToolTimeoutError     : tool exceeded timeout
            ToolExecutionError   : tool returned non-zero exit code
        """
        tool_binary = command[0]

        # ── Step 1: Check binary is installed ────────────────────
        check = subprocess.run(
            ['which', tool_binary],
            capture_output = True,
            text           = True
        )
        if check.returncode != 0:
            raise BinaryNotFoundError(
                f"'{tool_binary}' is not installed or not in PATH. "
                f"Run: bash scripts/install_tools.sh",
                tool = tool_binary
            )

        # ── Step 2: Run the tool ──────────────────────────────────
        timeout_seconds = self._cfg('timeout', default=300)

        try:
            result = subprocess.run(
                command,
                capture_output = True,
                text           = True,
                timeout        = timeout_seconds
            )
        except subprocess.TimeoutExpired:
            raise ToolTimeoutError(
                f"'{tool_binary}' timed out after {timeout_seconds}s. "
                f"Increase timeout in methodology config if needed.",
                tool = tool_binary
            )
        except FileNotFoundError:
            # Edge case: 'which' passed but binary disappeared mid-scan
            raise BinaryNotFoundError(
                f"'{tool_binary}' disappeared during execution.",
                tool = tool_binary
            )

        # ── Step 3: Check exit code ───────────────────────────────
        if result.returncode != 0:
            raise ToolExecutionError(
                f"'{tool_binary}' exited with code {result.returncode}. "
                f"stderr: {result.stderr[:300].strip()}",
                tool = tool_binary
            )

        return result.stdout

    def _read_output_file(self, filepath: str) -> str:
        """
        Read the output file a tool wrote to disk.

        Member 2 uses this instead of open() directly.
        Raises EmptyOutputError if file is missing or empty.

        Member 2 decides whether to catch EmptyOutputError or not:
            - If empty means 'nothing found' (normal) → catch it,
              return empty list, don't crash.
            - If empty always means something is wrong → let it
              bubble to the orchestrator.

        Parameters:
            filepath : full path to output file
                       e.g. 'output/example.com/raw/subfinder.txt'

        Returns:
            file contents as a string (guaranteed non-empty)

        Raises:
            EmptyOutputError : file doesn't exist or is empty
        """
        if not os.path.exists(filepath):
            raise EmptyOutputError(
                f"Output file was not created: {filepath}. "
                f"Tool may have failed silently.",
                tool = self.__class__.__name__
            )

        content = open(filepath, 'r', encoding='utf-8').read().strip()

        if not content:
            raise EmptyOutputError(
                f"Output file exists but is empty: {filepath}.",
                tool = self.__class__.__name__
            )

        return content

    def _cfg(self, key: str, default=None):
        """
        Safely read a value from self.config dict.
        Returns default if key doesn't exist or config is None.

        Member 2 uses this inside build_command() to read
        optional switches from the YAML config block.

        Example:
            timeout = self._cfg('timeout', default=30)
            # Returns config['timeout'] if set, else 30

            if self._cfg('recursive', default=False):
                cmd += ['-recursive']
        """
        if not hasattr(self, 'config') or self.config is None:
            return default
        return self.config.get(key, default)