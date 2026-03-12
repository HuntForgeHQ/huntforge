# core/resource_monitor.py
# Author         : Member 1
# Responsibility : Check if laptop resources are safe
#                  before running a phase.
#                  Gate 4 in orchestrator calls ok().
# Dependency     : psutil  (pip install psutil)
# ------------------------------------------------------------

import psutil


# Thresholds — if usage exceeds these, gate fails
CPU_THRESHOLD = 85   # don't run if CPU above 80%
RAM_THRESHOLD = 85   # don't run if RAM above 85%


class ResourceMonitor:
    """
    Checks laptop CPU and RAM before each phase runs.
    Orchestrator calls ok() in Gate 4.
    If ok() returns False — phase is skipped.
    Scan continues — never crashes because of resources.

    Example:
        monitor = ResourceMonitor()

        if monitor.ok():
            # safe to run phase
        else:
            # skip phase — laptop is struggling
    """

    def __init__(self,
                 cpu_threshold: int = CPU_THRESHOLD,
                 ram_threshold: int = RAM_THRESHOLD):
        """
        Parameters:
            cpu_threshold : max allowed CPU % before gate fails
                            default: 80
            ram_threshold : max allowed RAM % before gate fails
                            default: 85

        Thresholds can be overridden by machine_profiles.yaml:
            aggressive profile → cpu_threshold=90, ram_threshold=90
            passive profile    → cpu_threshold=60, ram_threshold=70
        """
        self.cpu_threshold = cpu_threshold
        self.ram_threshold = ram_threshold

    def ok(self) -> bool:
        """
        Main method — orchestrator calls this in Gate 4.
        Returns True if laptop can handle more work.
        Returns False if laptop is struggling.

        Checks both CPU and RAM.
        Both must be below threshold to return True.

        Example:
            monitor.ok()  →  True   (CPU 45%, RAM 60%)
            monitor.ok()  →  False  (CPU 92%, RAM 60%)
            monitor.ok()  →  False  (CPU 45%, RAM 89%)
        """
        return self.cpu() < self.cpu_threshold and \
               self.ram() < self.ram_threshold

    def cpu(self) -> float:
        """
        Returns current CPU usage as a percentage.
        interval=1 means it measures over 1 second — more accurate
        than instant reading.

        Example:
            monitor.cpu()  →  45.2
        """
        return psutil.cpu_percent(interval=1)

    def ram(self) -> float:
        """
        Returns current RAM usage as a percentage.

        Example:
            monitor.ram()  →  67.4
        """
        return psutil.virtual_memory().percent

    def status(self) -> dict:
        """
        Returns full resource status as a dict.
        Used by logger and dashboard to show resource usage.

        Example return:
        {
            'cpu_percent':     45.2,
            'ram_percent':     67.4,
            'cpu_threshold':   80,
            'ram_threshold':   85,
            'ok':              True
        }
        """
        cpu = self.cpu()
        ram = self.ram()

        return {
            'cpu_percent':   cpu,
            'ram_percent':   ram,
            'cpu_threshold': self.cpu_threshold,
            'ram_threshold': self.ram_threshold,
            'ok':            cpu < self.cpu_threshold and \
                             ram < self.ram_threshold
        }

    def __repr__(self) -> str:
        return (
            f"ResourceMonitor("
            f"CPU={self.cpu()}% / {self.cpu_threshold}% limit, "
            f"RAM={self.ram()}% / {self.ram_threshold}% limit, "
            f"ok={self.ok()})"
        )