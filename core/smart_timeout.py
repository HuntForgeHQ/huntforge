# core/smart_timeout.py
# Author         : Member 1
# Responsibility : Smart timeout logic for HuntForge tools.
#                  Instead of killing a tool immediately on timeout:
#                  1. Check if the tool has produced any output (file on disk or stdout)
#                  2. If YES → extend the timeout, let the tool finish
#                  3. If NO  → kill the process, raise ToolTimeoutError
# ------------------------------------------------------------

import os
import time
import threading
import subprocess
from typing import Optional, Callable
from loguru import logger
from core.exceptions import ToolTimeoutError


class SmartTimeoutRunner:
    """
    Runs a subprocess with smart timeout behavior.
    
    Instead of a hard kill at timeout, checks if progress has been made.
    If the tool is producing output, it gets extended time.
    If it's truly hung (no output), it gets killed.
    """
    
    DEFAULT_TIMEOUT = 300
    MAX_EXTENSIONS = 5
    EXTENSION_SECONDS = 300
    OUTPUT_CHECK_INTERVAL = 10
    
    def __init__(
        self,
        command: list,
        timeout: int = None,
        output_file: str = None,
        max_extensions: int = None,
        extension_seconds: int = None,
        tool_name: str = None,
        is_docker: bool = False,
    ):
        self.command = command
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self.output_file = output_file
        self.max_extensions = max_extensions if max_extensions is not None else self.MAX_EXTENSIONS
        self.extension_seconds = extension_seconds if extension_seconds is not None else self.EXTENSION_SECONDS
        self.tool_name = tool_name or (command[0] if command else 'unknown')
        self.is_docker = is_docker
        
        self._process = None
        self._timed_out = False
        self._extensions_used = 0
        self._killed = False
        self._initial_file_size = 0
        self._last_output_time = None

    def run(self) -> str:
        if self.output_file and os.path.exists(self.output_file):
            self._initial_file_size = os.path.getsize(self.output_file)
        
        logger.info(
            f"SmartTimeout: Starting {self.tool_name} "
            f"(timeout={self.timeout}s, max_extensions={self.max_extensions})"
        )
        
        self._process = subprocess.Popen(
            self.command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        
        self._last_output_time = time.time()
        
        checker = threading.Thread(
            target=self._timeout_checker,
            daemon=True,
        )
        checker.start()
        
        try:
            stdout, stderr = self._process.communicate()
        except Exception:
            if self._timed_out:
                raise ToolTimeoutError(
                    f"'{self.tool_name}' timed out after {self._get_total_timeout()}s "
                    f"with no output produced. Process killed.",
                    tool=self.tool_name
                )
            raise
        
        if self._process.returncode != 0:
            has_partial_output = self._has_new_output()
            if has_partial_output:
                logger.warning(
                    f"'{self.tool_name}' exited with code {self._process.returncode} "
                    f"but produced partial output. Treating as partial success."
                )
                return stdout
            
            from core.exceptions import ToolExecutionError
            raise ToolExecutionError(
                f"'{self.tool_name}' exited with code {self._process.returncode}. "
                f"stderr: {stderr[:500].strip()}",
                tool=self.tool_name
            )
        
        logger.info(
            f"SmartTimeout: {self.tool_name} completed naturally "
            f"(extensions_used={self._extensions_used})"
        )
        return stdout

    def _timeout_checker(self):
        if not self._wait_or_done(self.timeout):
            return
        
        if self._process.poll() is not None:
            return
        
        logger.warning(
            f"SmartTimeout: {self.tool_name} reached initial timeout ({self.timeout}s). "
            f"Checking for output..."
        )
        
        if self._has_new_output():
            self._handle_extension()
        else:
            self._kill_process("No output produced by timeout")
    
    def _wait_or_done(self, seconds: float) -> bool:
        start = time.time()
        while time.time() - start < seconds:
            if self._process.poll() is not None:
                return False
            time.sleep(self.OUTPUT_CHECK_INTERVAL)
        return True
    
    def _handle_extension(self):
        while self._extensions_used < self.max_extensions:
            self._extensions_used += 1
            total_so_far = self._get_total_timeout()
            
            logger.info(
                f"SmartTimeout: Extending {self.tool_name} by {self.extension_seconds}s "
                f"(extension {self._extensions_used}/{self.max_extensions}, "
                f"total={total_so_far + self.extension_seconds}s) — output detected"
            )
            
            if not self._wait_or_done(self.extension_seconds):
                return
            
            if self._process.poll() is not None:
                return
            
            if self._has_new_output():
                continue
            else:
                if self._extensions_used < self.max_extensions:
                    if not self._wait_or_done(min(60, self.extension_seconds)):
                        return
                    if self._process.poll() is not None:
                        return
                    if self._has_new_output():
                        continue
                
                self._kill_process(
                    f"No new output after {self._extensions_used} extensions "
                    f"({total_so_far}s total)"
                )
                return
        
        if self._process.poll() is None:
            self._kill_process(
                f"Max extensions ({self.max_extensions}) reached "
                f"({self._get_total_timeout()}s total)"
            )
    
    def _has_new_output(self) -> bool:
        if not self.output_file:
            if self._process and self._process.poll() is None:
                return True
            return False
        
        if not os.path.exists(self.output_file):
            return False
        
        current_size = os.path.getsize(self.output_file)
        if current_size > self._initial_file_size:
            self._initial_file_size = current_size
            self._last_output_time = time.time()
            return True
        
        return False
    
    def _kill_process(self, reason: str):
        self._timed_out = True
        self._killed = True
        
        logger.warning(
            f"SmartTimeout: Killing {self.tool_name} — {reason}"
        )
        
        try:
            self._process.kill()
            self._process.wait(timeout=5)
        except Exception:
            pass
    
    def _get_total_timeout(self) -> int:
        return self.timeout + (self._extensions_used * self.extension_seconds)
