# core/base_module.py
# Author      : Member 1
# Responsibility : Define the interface every tool module must follow.
#                 Handle all subprocess-level errors in one place.
#                 Member 2 inherits this — never rewrites subprocess logic.
#                 Executes all commands via DockerRunner.
# ------------------------------------------------------------

import os
import subprocess
import shutil
from core.exceptions import (
    BinaryNotFoundError,
    EmptyOutputError,
    ToolExecutionError,
    ToolTimeoutError,
    DockerNotRunningError
)
from core.docker_runner import DockerRunner


class BaseModule:
    """
    Parent class for every tool module in HuntForge.

    Member 2 creates child classes like this:

        from modules.base_module import BaseModule

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
    """

    def __init__(self, docker_runner: DockerRunner = None):
        """
        Orchestrator injects a shared DockerRunner.
        If running standalone for testing, instantiate a new one.

        Auto-detects if running inside the Docker container: if the 'docker'
        binary is not found in PATH, we assume we're inside the container and
        will run commands directly via subprocess (no docker exec needed).
        """
        # Detect execution context: if docker CLI is available, we're on host and should use DockerRunner.
        # If docker CLI is NOT available, we're inside the container and run directly.
        self._docker_cli_available = shutil.which('docker') is not None

        if self._docker_cli_available:
            # Use provided docker_runner or create a new one
            self.docker_runner = docker_runner or DockerRunner()
        else:
            # Inside container - run commands directly, ignore docker_runner
            self.docker_runner = None

    # ── 4 Methods Member 2 Must Implement ────────────────────────

    def build_command(self, target: str, output_file: str) -> list:
        """
        Returns the exact shell command to run as a list of strings.

        Member 2 MUST override this. No safe default exists.

        Example return value:
            ['subfinder', '-d', 'example.com',
             '-o', '/output/example.com/raw/subfinder.txt',
             '-silent']
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement build_command()."
        )

    def run(self, target: str, output_dir: str,
            tag_manager, config: dict = None) -> dict:
        """
        Execute the tool and return results in standard format.

        Member 2 MUST override this. No safe default exists.

        Parameters:
            target      : domain being scanned e.g. 'example.com'
            output_dir  : base output path e.g. 'output/example.com'
            tag_manager : TagManager instance
            config      : dict from YAML config block — optional switches

        Must return:
            {
                'results':       list,
                'count':         int,
                'requests_made': int
            }
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement run()."
        )

    def emit_tags(self, result: dict, tag_manager) -> None:
        """
        Read the result dict and set tags on tag_manager.

        Member 2 SHOULD override this for most tools.
        Default: does nothing. Safe to leave as-is if tool
        doesn't produce findings that other phases depend on.
        """
        pass

    def estimated_requests(self) -> int:
        """
        Return a rough estimate of HTTP requests this tool will make.
        Used by BudgetTracker in Gate 3 before deciding to run the tool.

        Member 2 SHOULD override this. Default: 100.
        """
        return 100

    def extract_tags(self, result: dict) -> dict:
        """
        Extract tags from tool result. Called by orchestrator after run().

        Default: returns empty dict. Override in subclass if the tool
        needs to set tags via return value instead of emit_tags().
        """
        return {}

    # ── Internal Core Methods ─────────────────────────────────────

    def docker_command(self, target: str, output_file: str) -> list:
        """
        Wraps build_command() with the necessary docker exec prefix.
        Used if a module legitimately needs to see the raw docker command.
        Not available when running inside the container (docker CLI not present).
        """
        if self.docker_runner is None:
            raise RuntimeError(
                "docker_command() is not available when running inside the container. "
                "Use build_command() to get the raw command without docker prefix."
            )
        return ["docker", "exec", self.docker_runner.container_name] + self.build_command(target, output_file)

    def _run_subprocess(self, command: list) -> str:
        """
        Execute a shell command. Depending on execution context:
        - If running on host (docker CLI available): exec via DockerRunner into container.
        - If running inside container: run command directly via subprocess.

        Handles checking if the binary exists and then executes.

        Exceptions (ToolTimeoutError, ToolExecutionError, DockerNotRunningError)
        bubble up to the orchestrator.
        """
        tool_binary = command[0]
        timeout_seconds = self._cfg('timeout', default=300)

        if self.docker_runner is not None:
            # ── Docker mode: host running orchestrator, use docker exec ─────
            # Step 1: Check binary is installed INSIDE container
            try:
                check = self.docker_runner.exec_raw(['which', tool_binary], timeout=5)
                if check.returncode != 0:
                    raise BinaryNotFoundError(
                        f"'{tool_binary}' is not installed inside the Kali container.",
                        tool=tool_binary
                    )
            except Exception as e:
                # If exec_raw fails (e.g., DockerNotRunningError), bubble it up
                if isinstance(e, BinaryNotFoundError):
                    raise
                # Calling is_container_running() will raise DockerNotRunningError if down
                self.docker_runner.is_container_running()

            # Step 2: Run the tool via DockerRunner
            return self.docker_runner.exec(command, timeout=timeout_seconds)
        else:
            # ── Direct mode: already inside container, run locally ─────
            # Check binary exists using shutil.which
            if not shutil.which(tool_binary):
                raise BinaryNotFoundError(
                    f"'{tool_binary}' is not installed or not in PATH.",
                    tool=tool_binary
                )

            # Run the command directly
            try:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds
                )
            except subprocess.TimeoutExpired:
                raise ToolTimeoutError(
                    f"'{tool_binary}' timed out after {timeout_seconds}s.",
                    tool=tool_binary
                )

            if result.returncode != 0:
                raise ToolExecutionError(
                    f"'{tool_binary}' exited with code {result.returncode}. "
                    f"stderr: {result.stderr[:500].strip()}",
                    tool=tool_binary
                )

            return result.stdout

    def _read_output_file(self, host_filepath: str) -> str:
        """
        Read the output file a tool wrote to disk (from the Host perspective).

        Matches original behavior, reading the mapped `./output/...` file.
        Raises EmptyOutputError if file is missing or empty.
        """
        if not os.path.exists(host_filepath):
            raise EmptyOutputError(
                f"Output file was not created: {host_filepath}. "
                f"Tool may have failed silently.",
                tool=self.__class__.__name__
            )

        content = open(host_filepath, 'r', encoding='utf-8').read().strip()

        if not content:
            raise EmptyOutputError(
                f"Output file exists but is empty: {host_filepath}.",
                tool=self.__class__.__name__
            )

        return content

    def _cfg(self, key: str, default=None):
        """
        Safely read a value from self.config dict.
        """
        if not hasattr(self, 'config') or self.config is None:
            return default
        return self.config.get(key, default)