# core/docker_runner.py
# Author         : Member 1
# Responsibility : Wraps all `docker exec` calls.
#                  Ensures tools run inside the Kali container but output
#                  is accessible on the host.
# ------------------------------------------------------------

import subprocess
from core.exceptions import DockerNotRunningError, ToolExecutionError, ToolTimeoutError


class DockerRunner:
    """
    Executes commands inside the HuntForge Docker container.
    """

    def __init__(self, container_name: str = "huntforge-kali"):
        self.container_name = container_name

    def is_container_running(self) -> bool:
        """
        Check if the target Docker container is currently reporting as 'running'.
        """
        check = subprocess.run(
            ['docker', 'inspect', '-f', '{{.State.Running}}', self.container_name],
            capture_output=True,
            text=True
        )
        return check.returncode == 0 and check.stdout.strip() == 'true'

    def exec(self, command: list, timeout: int = 300) -> str:
        """
        Execute a shell command inside the docker container.
        This behaves exactly like subprocess.run but prefixes the command with `docker exec`.

        Parameters:
            command : list of strings e.g. ['subfinder', '-d', 'example.com']
            timeout : int seconds until process is killed

        Returns:
            stdout of the command as a string

        Raises:
            DockerNotRunningError : If the container is down
            ToolTimeoutError      : If execution exceeds timeout
            ToolExecutionError    : If the tool returns a non-zero exit code
        """
        if not self.is_container_running():
            raise DockerNotRunningError(
                f"Docker container '{self.container_name}' is not running. "
                f"Start it with: docker-compose up -d"
            )

        docker_cmd = ['docker', 'exec', self.container_name] + command
        tool_binary = command[0]

        try:
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
        except subprocess.TimeoutExpired:
            raise ToolTimeoutError(
                f"'{tool_binary}' timed out after {timeout}s inside container.",
                tool=tool_binary
            )

        if result.returncode != 0:
            raise ToolExecutionError(
                f"'{tool_binary}' exited with code {result.returncode}. "
                f"stderr: {result.stderr[:500].strip()}",
                tool=tool_binary
            )

        return result.stdout

    def exec_raw(self, command: list, timeout: int = 300) -> subprocess.CompletedProcess:
        """
        Execute a shell command inside the docker container and return the full 
        CompletedProcess object. Use this only when a tool relies on parsing stderr 
        or handling specific non-zero exit codes.
        """
        if not self.is_container_running():
            raise DockerNotRunningError(
                f"Docker container '{self.container_name}' is not running. "
                f"Start it with: docker-compose up -d"
            )

        docker_cmd = ['docker', 'exec', self.container_name] + command
        tool_binary = command[0]

        try:
            return subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
        except subprocess.TimeoutExpired:
            raise ToolTimeoutError(
                f"'{tool_binary}' timed out after {timeout}s inside container.",
                tool=tool_binary
            )
