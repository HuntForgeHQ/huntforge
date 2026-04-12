# core/smart_timeout_v2.py
# Author         : Antigravity (AI)
# Responsibility : Production-grade activity-aware monitoring for long-running tools.
#                  Uses hybrid detection (Output + CPU/IO activity) and 
#                  graceful termination.
# ------------------------------------------------------------

import os
import time
import signal
import threading
import subprocess
from typing import Optional, List, Dict, Any
import psutil
from loguru import logger
from core.exceptions import ToolTimeoutError, ToolExecutionError


class SmartTimeoutV2:
    """
    Advanced process runner with hybrid activity monitoring.
    
    Decision Logic:
    1. If output file grows or stdout is produced -> EXTEND
    2. Else if process shows CPU or IO delta > threshold -> EXTEND
    3. Else (completely silent and idle) -> TERMINATE
    """

    # Default settings
    DEFAULT_TIMEOUT = 300
    MAX_EXTENSIONS = 10
    EXTENSION_SECONDS = 300
    MONITOR_INTERVAL = 15  # Check deltas every 15s
    ACTIVITY_THRESHOLD_BYTES = 10240  # 10KB IO delta (prevents noise extension)
    ACTIVITY_THRESHOLD_CPU = 0.5    # 0.5% CPU delta

    # Tool-specific profiles
    PROFILES = {
        "nuclei": {
            "extension_seconds": 600,
            "max_extensions": 15,
            "activity_threshold_cpu": 0.2, # Nuclei can be very quiet but active
        },
        "dalfox": {
            "extension_seconds": 120,
        },
        "katana": {
            "extension_seconds": 450,
            "activity_threshold_bytes": 512, # Low IO threshold for crawling
        }
    }

    def __init__(
        self,
        command: List[str],
        timeout: int = None,
        output_file: str = None,
        tool_name: str = None,
        max_extensions: int = None,
        extension_seconds: int = None,
        is_docker: bool = False,
    ):
        self.command = command
        self.tool_name = tool_name or (command[0].split('/')[-1] if command else "unknown")
        
        # Load profile if exists
        profile = self.PROFILES.get(self.tool_name.lower(), {})
        
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self.output_file = output_file
        self.max_extensions = max_extensions if max_extensions is not None else profile.get("max_extensions", self.MAX_EXTENSIONS)
        self.extension_seconds = extension_seconds or profile.get("extension_seconds", self.EXTENSION_SECONDS)
        self.is_docker = is_docker

        # Thresholds
        self.activity_threshold_bytes = profile.get("activity_threshold_bytes", self.ACTIVITY_THRESHOLD_BYTES)
        self.activity_threshold_cpu = profile.get("activity_threshold_cpu", self.ACTIVITY_THRESHOLD_CPU)

        self._process: Optional[subprocess.Popen] = None
        self._ps_proc: Optional[psutil.Process] = None
        self._extensions_used = 0
        self._start_time = 0
        self._last_activity_check = 0
        self._last_io_counters = None
        self._last_cpu_time = 0
        self._last_file_size = 0
        self._stop_event = threading.Event()
        self._timed_out = False

    def validate_inputs(self) -> bool:
        """
        Pre-execution validation logic.
        Ensures obvious failure conditions are caught before spawning process.
        """
        if not self.command:
            logger.error(f"[{self.tool_name}] Empty command provided.")
            return False

        profile = self.PROFILES.get(self.tool_name.lower(), {})
        required_args = profile.get("required_args", [])

        # Check for required flags or input patterns
        cmd_str = " ".join(self.command).lower()
        for arg in required_args:
            if arg.lower() not in cmd_str:
                logger.error(f"[{self.tool_name}] Missing required argument: {arg}")
                return False

        # If it's dalfox, specifically look for a target input file if --url isn't present
        if self.tool_name.lower() == "dalfox":
            if not any(mode in cmd_str for mode in ["url", "file", "pipe", "sxss"]):
                # Look for a .txt/json filename in the command that might be a list
                possible_files = [arg for arg in self.command if arg.endswith('.txt') or arg.endswith('.json')]
                if not possible_files:
                    logger.error(f"[{self.tool_name}] No target URL or input file provided.")
                    return False
                for f in possible_files:
                    if not os.path.exists(f) or os.path.getsize(f) == 0:
                        logger.error(f"[{self.tool_name}] Input file {f} is missing or empty.")
                        return False

        return True

    def run(self) -> str:
        """
        Main execution entry point. Returns stdout string.
        """
        if not self.validate_inputs():
            raise ToolExecutionError(f"Pre-execution validation failed for {self.tool_name}", tool=self.tool_name)

        if self.output_file and os.path.exists(self.output_file):
            self._last_file_size = os.path.getsize(self.output_file)

        logger.info(f"SmartTimeoutV2: Starting {self.tool_name} (Initial Timeout: {self.timeout}s)")
        
        self._start_time = time.time()
        self._process = subprocess.Popen(
            self.command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1, # Line buffered for better interactivity
            universal_newlines=True
        )
        
        try:
            self._ps_proc = psutil.Process(self._process.pid)
            # Initialize metrics
            self._update_metrics()
        except psutil.NoSuchProcess:
            pass # Process might have finished instantly

        # Start background monitor
        monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        monitor_thread.start()

        try:
            stdout, stderr = self._process.communicate()
            self._stop_event.set()
        except Exception:
            self._stop_event.set()
            self._terminate_gracefully()
            raise

        if self._timed_out:
            raise ToolTimeoutError(
                f"Tool '{self.tool_name}' killed after reaching max timeout extensions.",
                tool=self.tool_name
            )

        if self._process.returncode != 0:
            # Check if it produced output despite error (partial success)
            if self._has_new_output():
                logger.warning(f"{self.tool_name} exited with error {self._process.returncode} but produced output.")
                return stdout
            
            raise ToolExecutionError(
                f"'{self.tool_name}' failed with exit code {self._process.returncode}. stderr: {stderr[:500]}",
                tool=self.tool_name
            )

        logger.info(f"SmartTimeoutV2: {self.tool_name} finished successfully.")
        return stdout

    def _monitor_loop(self):
        """
        Background thread to check for timeouts and activity.
        """
        next_check = self._start_time + self.timeout
        
        while not self._stop_event.is_set():
            now = time.time()
            if now < next_check:
                time.sleep(1)
                continue
            
            # Check process state
            if self._process.poll() is not None:
                break

            # Process is still running but reached timeout point
            is_active = self._check_activity()
            
            if is_active:
                self._extensions_used += 1
                logger.info(
                    f"SmartTimeoutV2: Extending {self.tool_name} by {self.extension_seconds}s "
                    f"({self._extensions_used}/∞) - Activity detected."
                )
                next_check = now + self.extension_seconds
            else:
                self._timed_out = True
                reason = "Inactivity"
                logger.warning(f"SmartTimeoutV2: Terminating {self.tool_name} - Reason: {reason}")
                self._terminate_gracefully()
                break

    def _get_total_cpu_time(self, proc: psutil.Process) -> float:
        """Sums user and system CPU times for a process."""
        try:
            times = proc.cpu_times()
            return times.user + times.system
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return 0.0

    def _update_metrics(self):
        """Captures current process metrics."""
        try:
            self._last_cpu_time = self._get_total_cpu_time(self._ps_proc)
            self._last_io_counters = self._ps_proc.io_counters()
            if self.output_file and os.path.exists(self.output_file):
                self._last_file_size = os.path.getsize(self.output_file)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    def _check_activity(self) -> bool:
        """
        Determines if the process is "active" based on multiple signals.
        """
        if self._has_new_output():
            self._update_metrics()
            return True
        
        # Check CPU / IO delta
        try:
            curr_cpu = self._get_total_cpu_time(self._ps_proc)
            curr_io = self._ps_proc.io_counters()
            
            cpu_delta = curr_cpu - self._last_cpu_time
            io_delta_read = curr_io.read_bytes - self._last_io_counters.read_bytes
            io_delta_write = curr_io.write_bytes - self._last_io_counters.write_bytes
            
            # Save for next check
            self._last_cpu_time = curr_cpu
            self._last_io_counters = curr_io

            # Log metrics for debugging
            logger.debug(f"[{self.tool_name}] Activity check: CPU Delta={cpu_delta:.3f}, IO Delta (R/W)={io_delta_read}/{io_delta_write}")

            if cpu_delta > self.activity_threshold_cpu:
                return True
            if (io_delta_read + io_delta_write) > self.activity_threshold_bytes:
                return True
                
            # Check children if this is a parent process
            for child in self._ps_proc.children(recursive=True):
                try:
                    c_cpu = self._get_total_cpu_time(child)
                    if c_cpu > 0: # Any activity from children counts
                        # We don't track deltas for all children individually, 
                        # but if any child is using CPU, the job is alive.
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

        except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
            pass

        return False

    def _has_new_output(self) -> bool:
        """Checks if the output file grew since last check."""
        if not self.output_file or not os.path.exists(self.output_file):
            return False
            
        current_size = os.path.getsize(self.output_file)
        if current_size > self._last_file_size:
            self._last_file_size = current_size
            return True
        return False

    def _terminate_gracefully(self):
        """
        Implements SIGTERM -> Wait -> SIGKILL.
        Ensures child processes are also cleaned up.
        """
        if not self._process or self._process.poll() is not None:
            return

        logger.info(f"SmartTimeoutV2: Attempting graceful shutdown for {self.tool_name} (pid {self._process.pid})")
        
        try:
            # 1. SIGTERM (Terminate)
            parent = psutil.Process(self._process.pid)
            children = parent.children(recursive=True)
            
            parent.terminate()
            for child in children:
                try:
                    child.terminate()
                except psutil.NoSuchProcess:
                    continue
            
            # 2. Wait
            gone, alive = psutil.wait_procs([parent] + children, timeout=5)
            
            # 3. SIGKILL (Kill remaining)
            for p in alive:
                logger.warning(f"SmartTimeoutV2: Process {p.pid} refused to exit, killing.")
                try:
                    p.kill()
                except psutil.NoSuchProcess:
                    continue
                    
        except Exception as e:
            logger.error(f"Error during termination of {self.tool_name}: {e}")
            # Fallback
            try:
                self._process.kill()
            except:
                pass
