# scripts/test_smart_timeout_v2.py
import sys
import os
import time
import subprocess
import threading

# Add Project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.smart_timeout_v2 import SmartTimeoutV2
from core.exceptions import ToolTimeoutError, ToolExecutionError
from loguru import logger

def simulate_busy_silent_tool(output_file):
    """Simulates a tool that uses CPU but produces no output for a while."""
    script = """
import time
import os
import sys

# Consume CPU for 20 seconds silently
start = time.time()
while time.time() - start < 15:
    _ = [x*x for x in range(1000)] # Busy work

print("Final discovery!")
"""
    cmd = [sys.executable, "-c", script]
    # We'll set a very short initial timeout of 5s to trigger an extension
    runner = SmartTimeoutV2(command=cmd, timeout=5, tool_name="busy_tool")
    logger.info("--- Testing Busy Silent Tool (Should Extend) ---")
    start = time.time()
    result = runner.run()
    duration = time.time() - start
    logger.success(f"Busy tool finished after {duration:.2f}s. Result: {result.strip()}")

def simulate_hung_tool():
    """Simulates a tool that hangs (idle, no output)."""
    script = """
import time
time.sleep(30)
"""
    cmd = [sys.executable, "-c", script]
    # Set tiny extension seconds so test doesn't wait 5 minutes
    runner = SmartTimeoutV2(command=cmd, timeout=5, extension_seconds=5, max_extensions=1, tool_name="hung_tool")
    logger.info("--- Testing Hung Tool (Should Fail after extension) ---")
    try:
        runner.run()
    except ToolTimeoutError:
        logger.success("Hung tool was correctly killed after inactivity.")

def test_validation():
    """Tests pre-flight validation."""
    logger.info("--- Testing Pre-flight Validation (Dalfox) ---")
    cmd = ["dalfox", "random_command"] # Missing -b or --url
    runner = SmartTimeoutV2(command=cmd, tool_name="dalfox")
    try:
        runner.run()
    except ToolExecutionError as e:
        logger.success(f"Validation correctly blocked invalid dalfox command: {e}")

if __name__ == "__main__":
    test_validation()
    simulate_busy_silent_tool("test_output.txt")
    simulate_hung_tool()
