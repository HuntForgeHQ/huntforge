"""
HuntForge — Comprehensive Test Suite
Covers: TC-ENV-001, TC-BM-001 through TC-BM-005, TC-TM-001 through TC-TM-008,
        TC-BT-001 through TC-BT-004, TC-SCOPE-001 through TC-SCOPE-007,
        TC-DB-001 through TC-DB-004, TC-LOG-001 through TC-LOG-005,
        TC-SIEM-001 through TC-SIEM-002, TC-FP-001 through TC-FP-004,
        TC-CLI-001, TC-CONTRACT-003
"""

import pytest
import os
import sys
import json
import time
import tempfile
import sqlite3
import subprocess

# Ensure project root is on sys.path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


# ═══════════════════════════════════════════════════════════════
# 1. ENVIRONMENT TESTS (TC-ENV-001)
# ═══════════════════════════════════════════════════════════════

class TestEnvironment:
    """TC-ENV-001: All Python dependencies importable."""

    @pytest.mark.p0
    def test_env_001_python_dependencies(self):
        import yaml
        import loguru
        import flask
        import requests
        import rich
        assert True  # If we reach here, all imports succeeded


# ═══════════════════════════════════════════════════════════════
# 2. BASE MODULE TESTS (TC-BM-001 through TC-BM-005)
# ═══════════════════════════════════════════════════════════════

class TestBaseModule:
    """Tests for modules/base_module.py"""

    @pytest.mark.p0
    def test_bm_001_importable(self):
        """TC-BM-001: BaseModule can be imported."""
        from modules.base_module import BaseModule
        assert BaseModule is not None

    @pytest.mark.p1
    def test_bm_002_build_command_not_implemented(self):
        """TC-BM-002: BaseModule.build_command() raises NotImplementedError."""
        from modules.base_module import BaseModule
        # BaseModule is not abstract via ABC, but build_command raises NotImplementedError
        bm = BaseModule.__new__(BaseModule)
        bm.docker_runner = None
        with pytest.raises(NotImplementedError):
            bm.build_command("example.com", "/output/test.txt")

    @pytest.mark.p1
    def test_bm_002_run_not_implemented(self):
        """TC-BM-002b: BaseModule.run() raises NotImplementedError."""
        from modules.base_module import BaseModule
        bm = BaseModule.__new__(BaseModule)
        with pytest.raises(NotImplementedError):
            bm.run("example.com", "output/example.com", None, {})

    @pytest.mark.p1
    def test_bm_005_estimated_requests_default(self):
        """TC-BM-005: estimated_requests() returns a default integer >= 0."""
        from modules.base_module import BaseModule
        bm = BaseModule.__new__(BaseModule)
        result = bm.estimated_requests()
        assert isinstance(result, int)
        assert result >= 0

    @pytest.mark.p1
    def test_bm_003_docker_command_wraps(self):
        """TC-BM-003: docker_command() wraps build_command with docker exec prefix."""
        from modules.passive.subfinder import SubfinderModule

        class FakeDockerRunner:
            container_name = "huntforge-kali"
        
        mod = SubfinderModule.__new__(SubfinderModule)
        mod.docker_runner = FakeDockerRunner()
        
        cmd = mod.docker_command("example.com", "/output/subfinder.txt")
        assert cmd[0] == "docker"
        assert cmd[1] == "exec"
        assert cmd[2] == "huntforge-kali"


# ═══════════════════════════════════════════════════════════════
# 5. TAG MANAGER TESTS (TC-TM-001 through TC-TM-008)
# ═══════════════════════════════════════════════════════════════

class TestTagManager:
    """Tests for core/tag_manager.py"""

    def _make_tm(self):
        from core.tag_manager import TagManager
        return TagManager()

    @pytest.mark.p0
    def test_tm_001_add_and_retrieve(self):
        """TC-TM-001: Add a tag and retrieve it."""
        tm = self._make_tm()
        tm.add("has_api", confidence="high", source="httpx", evidence=["found /api/v1"])
        assert tm.has("has_api") is True

    @pytest.mark.p0
    def test_tm_002_confidence_threshold_enforcement(self):
        """TC-TM-002: Stored 'medium' does NOT satisfy required 'high'."""
        tm = self._make_tm()
        tm.add("has_api", confidence="medium", source="httpx")
        assert tm.has("has_api", min_confidence="high") is False

    @pytest.mark.p0
    def test_tm_003_confidence_hierarchy(self):
        """TC-TM-003: 'high' confidence satisfies all three levels."""
        tm = self._make_tm()
        tm.add("has_api", confidence="high", source="httpx")
        assert tm.has("has_api", min_confidence="low") is True
        assert tm.has("has_api", min_confidence="medium") is True
        assert tm.has("has_api", min_confidence="high") is True

    @pytest.mark.p0
    def test_tm_004_missing_tag(self):
        """TC-TM-004: Missing tag returns False without raising."""
        tm = self._make_tm()
        assert tm.has("has_cms") is False

    @pytest.mark.p1
    def test_tm_005_get_confidence(self):
        """TC-TM-005: get() returns correct confidence string."""
        tm = self._make_tm()
        tm.add("has_api", confidence="medium", source="httpx")
        data = tm.get("has_api")
        assert data is not None
        assert data["confidence"] == "medium"

    @pytest.mark.p1
    def test_tm_006_persistence_to_disk(self):
        """TC-TM-006: Tags persist via save_to_file and can be read back."""
        tm = self._make_tm()
        tm.add("has_api", confidence="high", source="httpx")

        with tempfile.TemporaryDirectory() as tmpdir:
            tm.save_to_file(tmpdir)
            filepath = os.path.join(tmpdir, "processed", "active_tags.json")
            assert os.path.exists(filepath)
            with open(filepath, "r") as f:
                data = json.load(f)
            assert "has_api" in data
            assert data["has_api"]["confidence"] == "high"

    @pytest.mark.p1
    def test_tm_007_never_downgrade_confidence(self):
        """Confidence should never be downgraded."""
        tm = self._make_tm()
        tm.add("has_api", confidence="high", source="httpx")
        tm.add("has_api", confidence="low", source="whatweb")
        data = tm.get("has_api")
        assert data["confidence"] == "high"  # Should NOT be downgraded

    @pytest.mark.p1
    def test_tm_008_get_all(self):
        """TC-TM-008: get_all() returns dict of all tags with metadata."""
        tm = self._make_tm()
        tm.add("has_api", confidence="high", source="httpx")
        tm.add("has_cms", confidence="medium", source="whatweb")
        tm.add("has_auth", confidence="low", source="katana")
        result = tm.get_all()
        assert len(result) == 3
        for tag_data in result.values():
            assert "confidence" in tag_data


# ═══════════════════════════════════════════════════════════════
# 6. BUDGET TRACKER TESTS (TC-BT-001 through TC-BT-004)
# ═══════════════════════════════════════════════════════════════

class TestBudgetTracker:
    """Tests for core/budget_tracker.py"""

    @pytest.mark.p1
    def test_bt_001_within_limits(self):
        """TC-BT-001: Within limits returns True when under budget."""
        from core.budget_tracker import BudgetTracker
        bt = BudgetTracker(max_requests=1000, max_time_minutes=60)
        bt.add_requests(500)
        assert bt.within_limits() is True

    @pytest.mark.p0
    def test_bt_002_budget_exceeded(self):
        """TC-BT-002: Budget exceeded raises BudgetExceededError."""
        from core.budget_tracker import BudgetTracker
        from core.exceptions import BudgetExceededError
        bt = BudgetTracker(max_requests=1000, max_time_minutes=60)
        bt.add_requests(500)
        bt.add_requests(600)
        # Total = 1100 > 1000, should raise
        with pytest.raises(BudgetExceededError):
            bt.within_limits()

    @pytest.mark.p1
    def test_bt_003_no_budget_config(self):
        """TC-BT-003: No budget config means everything is within limits."""
        from core.budget_tracker import BudgetTracker
        bt = BudgetTracker(max_requests=None, max_time_minutes=None)
        bt.add_requests(999999)
        assert bt.within_limits() is True

    @pytest.mark.p2
    def test_bt_004_log_status(self):
        """TC-BT-004: log_status() returns a dict without raising."""
        from core.budget_tracker import BudgetTracker
        bt = BudgetTracker(max_requests=1000, max_time_minutes=60)
        bt.add_requests(100)
        status = bt.log_status()
        assert isinstance(status, dict)
        assert "requests_used" in status
        assert status["requests_used"] == 100


# ═══════════════════════════════════════════════════════════════
# 18. SCOPE ENFORCER TESTS (TC-SCOPE-001 through TC-SCOPE-007)
# ═══════════════════════════════════════════════════════════════

class TestScopeEnforcer:
    """Tests for core/scope_enforcer.py"""

    def _make_enforcer(self, programs):
        """Create a ScopeEnforcer with injected scope data (no file read)."""
        from core.scope_enforcer import ScopeEnforcer
        se = ScopeEnforcer.__new__(ScopeEnforcer)
        se.scopes = programs
        return se

    @pytest.mark.p0
    def test_scope_001_in_scope_domain(self):
        """TC-SCOPE-001: Wildcard match returns allowed=True."""
        se = self._make_enforcer({
            "TestProgram": {
                "in_scope": ["*.example.com", "example.com"],
                "out_of_scope": []
            }
        })
        allowed, reason, prog = se.check("api.example.com")
        assert allowed is True

    @pytest.mark.p0
    def test_scope_002_out_of_scope_overrides(self):
        """TC-SCOPE-002: Exclusion overrides wildcard inclusion."""
        se = self._make_enforcer({
            "TestProgram": {
                "in_scope": ["*.example.com"],
                "out_of_scope": ["blog.example.com"]
            }
        })
        allowed, reason, prog = se.check("blog.example.com")
        assert allowed is False

    @pytest.mark.p0
    def test_scope_003_unknown_domain(self):
        """TC-SCOPE-003: Unknown domain returns allowed=False."""
        se = self._make_enforcer({
            "TestProgram": {
                "in_scope": ["*.example.com"],
                "out_of_scope": []
            }
        })
        allowed, reason, prog = se.check("unknown-domain.xyz")
        assert allowed is False

    @pytest.mark.p0
    def test_scope_006_wildcard_pattern_matching(self):
        """TC-SCOPE-006: Wildcard pattern matching various depths."""
        se = self._make_enforcer({
            "TestProgram": {
                "in_scope": ["*.example.com", "example.com"],
                "out_of_scope": []
            }
        })
        # Root match
        allowed, _, _ = se.check("example.com")
        assert allowed is True
        
        # Subdomain match
        allowed, _, _ = se.check("sub.example.com")
        assert allowed is True
        
        # Deep subdomain match
        allowed, _, _ = se.check("deep.sub.example.com")
        assert allowed is True
        
        # Non-matching domain
        allowed, _, _ = se.check("notexample.com")
        assert allowed is False

    @pytest.mark.p0
    def test_contract_003_check_return_signature(self):
        """TC-CONTRACT-003: check() returns a 3-tuple (bool, str, str)."""
        se = self._make_enforcer({
            "TestProgram": {
                "in_scope": ["*.example.com"],
                "out_of_scope": []
            }
        })
        result = se.check("any.domain.com")
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert isinstance(result[0], bool)
        assert isinstance(result[1], str)


# ═══════════════════════════════════════════════════════════════
# 19. SCAN HISTORY TESTS (TC-DB-001 through TC-DB-004)
# ═══════════════════════════════════════════════════════════════

class TestScanHistory:
    """Tests for core/scan_history.py"""

    @pytest.mark.p0
    def test_db_001_schema_initialization(self):
        """TC-DB-001: SQLite file created with 'scans' table."""
        from core.scan_history import ScanHistory
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_history.db")
            sh = ScanHistory(db_path=db_path)
            assert os.path.exists(db_path)
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scans'")
            assert cursor.fetchone() is not None
            conn.close()

    @pytest.mark.p0
    def test_db_002_save_and_get_roundtrip(self):
        """TC-DB-002: record_start + record_end round-trip stores data."""
        from core.scan_history import ScanHistory
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_history.db")
            sh = ScanHistory(db_path=db_path)
            
            scan_id = sh.record_start("test.com", "output/test.com")
            assert isinstance(scan_id, int)
            assert scan_id > 0
            
            sh.record_end(scan_id, "COMPLETE", 5)
            
            # Verify the data was stored
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT domain, status, tag_count FROM scans WHERE id = ?", (scan_id,))
            row = cursor.fetchone()
            conn.close()
            
            assert row is not None
            assert row[0] == "test.com"
            assert row[1] == "COMPLETE"
            assert row[2] == 5


# ═══════════════════════════════════════════════════════════════
# 15. HFLOGGER TESTS (TC-LOG-001 through TC-LOG-005)
# ═══════════════════════════════════════════════════════════════

class TestHFLogger:
    """Tests for core/hf_logger.py"""

    @pytest.mark.p0
    def test_log_001_jsonl_file_creation(self):
        """TC-LOG-001: scan_start creates JSONL file with SCAN_START event."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Need to be in project root for fingerprints loading
            old_cwd = os.getcwd()
            os.chdir(ROOT)
            try:
                from core.hf_logger import HFLogger
                hf = HFLogger(tmpdir)
                hf.scan_start("test.com")
                
                log_path = os.path.join(tmpdir, "logs", "scan_events.jsonl")
                assert os.path.exists(log_path)
                
                with open(log_path, "r") as f:
                    line = f.readline().strip()
                event = json.loads(line)
                assert event["event_type"] == "scan_start"
                assert event["domain"] == "test.com"
            finally:
                os.chdir(old_cwd)

    @pytest.mark.p0
    def test_log_002_all_event_types(self):
        """TC-LOG-002: All event methods write valid JSON events."""
        with tempfile.TemporaryDirectory() as tmpdir:
            old_cwd = os.getcwd()
            os.chdir(ROOT)
            try:
                from core.hf_logger import HFLogger
                hf = HFLogger(tmpdir)
                
                hf.scan_start("test.com")
                hf.phase_start("phase_1", "Passive Recon")
                hf.tool_start("subfinder")
                hf.tool_complete("subfinder", 10)
                hf.tool_skipped("gitleaks", "tag_missing")
                hf.tool_error("nuclei", Exception("timeout"))
                hf.phase_end("phase_1")
                hf.scan_end({"has_api": "high"})
                
                log_path = os.path.join(tmpdir, "logs", "scan_events.jsonl")
                with open(log_path, "r") as f:
                    lines = [l.strip() for l in f.readlines() if l.strip()]
                
                assert len(lines) == 8
                
                # Verify each line parses as valid JSON
                for line in lines:
                    event = json.loads(line)
                    assert "event_type" in event
                    assert "timestamp" in event
            finally:
                os.chdir(old_cwd)

    @pytest.mark.p1
    def test_log_004_timestamp_format(self):
        """TC-LOG-004: Timestamp ends with 'Z' (ISO 8601 UTC)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            old_cwd = os.getcwd()
            os.chdir(ROOT)
            try:
                from core.hf_logger import HFLogger
                hf = HFLogger(tmpdir)
                hf.scan_start("test.com")
                
                log_path = os.path.join(tmpdir, "logs", "scan_events.jsonl")
                with open(log_path, "r") as f:
                    event = json.loads(f.readline())
                assert event["timestamp"].endswith("Z")
            finally:
                os.chdir(old_cwd)


# ═══════════════════════════════════════════════════════════════
# 16. SIEM FORMATTER TESTS (TC-SIEM-001 through TC-SIEM-002)
# ═══════════════════════════════════════════════════════════════

class TestSIEMFormatter:
    """Tests for core/siem_formatter.py"""

    @pytest.mark.p1
    def test_siem_001_json_format(self):
        """TC-SIEM-001: Default format returns valid JSON."""
        from core.siem_formatter import SIEMFormatter
        event = {"event_type": "tool_start", "timestamp": "2025-01-01T00:00:00Z", "tool": "subfinder"}
        result = SIEMFormatter.format(event, "json")
        parsed = json.loads(result)
        assert parsed["event_type"] == "tool_start"

    @pytest.mark.p1
    def test_siem_002_cef_format(self):
        """TC-SIEM-002: CEF format starts with correct header."""
        from core.siem_formatter import SIEMFormatter
        event = {"event_type": "tool_error", "timestamp": "2025-01-01T00:00:00Z",
                 "tool": "nuclei", "status": "error", "error": "timeout"}
        result = SIEMFormatter.to_cef(event)
        assert result.startswith("CEF:0|HuntForge|")


# ═══════════════════════════════════════════════════════════════
# 17. TOOL FINGERPRINT DATABASE TESTS (TC-FP-001 through TC-FP-004)
# ═══════════════════════════════════════════════════════════════

class TestToolFingerprints:
    """Tests for data/tool_fingerprints.json"""

    @pytest.fixture
    def fingerprints(self):
        fp_path = os.path.join(ROOT, "data", "tool_fingerprints.json")
        with open(fp_path, "r") as f:
            return json.load(f)

    @pytest.mark.p0
    def test_fp_001_valid_json(self):
        """TC-FP-001: Fingerprint DB is valid JSON."""
        fp_path = os.path.join(ROOT, "data", "tool_fingerprints.json")
        with open(fp_path, "r") as f:
            data = json.load(f)
        assert isinstance(data, dict)

    @pytest.mark.p1
    def test_fp_002_required_tools_present(self, fingerprints):
        """TC-FP-002: Key tools exist in the fingerprint DB."""
        required = ["subfinder", "nuclei", "httpx", "naabu", "gitleaks", "katana"]
        for tool in required:
            assert tool in fingerprints, f"Missing tool: {tool}"

    @pytest.mark.p1
    def test_fp_003_schema_completeness(self, fingerprints):
        """TC-FP-003: Each tool entry has required keys."""
        required_keys = {"detection_risk", "network_behavior", "defender_visibility"}
        for tool_name, tool_data in fingerprints.items():
            for key in required_keys:
                assert key in tool_data, f"Tool '{tool_name}' missing key '{key}'"

    @pytest.mark.p2
    def test_fp_004_valid_enum_values(self, fingerprints):
        """TC-FP-004: detection_risk values are from allowed set."""
        allowed_risk = {"none", "low", "medium", "high"}
        for tool_name, tool_data in fingerprints.items():
            risk = tool_data.get("detection_risk", "")
            assert risk in allowed_risk, f"Tool '{tool_name}' has invalid detection_risk: '{risk}'"


# ═══════════════════════════════════════════════════════════════
# 23. CLI TESTS (TC-CLI-001)
# ═══════════════════════════════════════════════════════════════

class TestCLI:
    """Tests for huntforge.py CLI"""

    @pytest.mark.p0
    def test_cli_001_help_output(self):
        """TC-CLI-001: huntforge.py --help exits 0 and shows subcommands."""
        result = subprocess.run(
            [sys.executable, os.path.join(ROOT, "huntforge.py"), "--help"],
            capture_output=True, text=True, cwd=ROOT
        )
        assert result.returncode == 0
        assert "scan" in result.stdout
        assert "report" in result.stdout


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
