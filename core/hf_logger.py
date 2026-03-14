"""
core/hf_logger.py — HuntForge Structured Event Logger
Member 3 (Blue Team 1) — Logging & Detection

Interface draft: method signatures only, no logic.

Responsibilities:
  - Writes human-readable colored terminal output (via loguru)
  - Writes structured JSON event log (machine-readable, SIEM-compatible)
    → output_dir/logs/scan_events.jsonl

Event types emitted:
  SCAN_START | SCAN_END | PHASE_START | PHASE_END |
  TOOL_START | TOOL_COMPLETE | TOOL_SKIPPED | TOOL_ERROR | TAG_SET

Called by:
  - core/orchestrator.py  (Member 1)
  - core/tag_manager.py   (Member 1)
  - modules/base_module.py (Member 1)

Consumed by:
  - core/siem_formatter.py      (Member 3 — converts events to CEF/ECS)
  - dashboard/app.py            (Member 4 — reads scan_events.jsonl)
  - data/tool_fingerprints.json (Member 3 — enriches TOOL_START events)
"""

import json
import os
import time
from datetime import datetime
from typing import Any

from loguru import logger


class HFLogger:
    """
    HuntForge's structured event logger.

    Writes two outputs simultaneously:
      1. Human-readable coloured terminal output  (via loguru)
      2. Structured JSON event log per scan        (scan_events.jsonl)
    """

    def __init__(self, output_dir: str) -> None:
        """
        Initialise the logger for a single scan session.

        Sets up the JSONL output path at:
            <output_dir>/logs/scan_events.jsonl
        Creates the directory if it does not exist.

        Args:
            output_dir: Root output directory for this scan
                        (e.g. "output/example.com").
        """
        ...

    # ── Scan Lifecycle ────────────────────────────────────────────────

    def scan_start(self, domain: str) -> None:
        """
        Record the beginning of a full HuntForge scan.

        Emits event: SCAN_START
        Logs:  INFO  "[HuntForge] Scan started: <domain>"

        Args:
            domain: Target domain being scanned (e.g. "example.com").
        """
        ...

    def scan_end(self, final_tags: dict[str, Any]) -> None:
        """
        Record the completion of a full scan and summarise results.

        Emits event: SCAN_END  (includes total duration + final tag set)
        Logs:  SUCCESS  "[HuntForge] Scan complete in <human_duration>"

        Args:
            final_tags: Dict of all tags collected during the scan,
                        as returned by TagManager.all().
        """
        ...

    # ── Phase Lifecycle ───────────────────────────────────────────────

    def phase_start(self, phase_name: str, label: str) -> None:
        """
        Record the start of a methodology phase.

        Emits event: PHASE_START
        Logs:  INFO  "[Phase] ── <label> ──────────────"

        Args:
            phase_name: Internal phase key from methodology YAML
                        (e.g. "passive_recon").
            label:      Human-readable phase label
                        (e.g. "Passive Reconnaissance").
        """
        ...

    def phase_end(self, phase_name: str) -> None:
        """
        Record the end of a methodology phase and its duration.

        Emits event: PHASE_END  (includes duration since phase_start)
        Logs:  INFO  "[Phase] <phase_name> done in <duration>s"

        Args:
            phase_name: Internal phase key — must match a prior phase_start call.
        """
        ...

    # ── Tool Lifecycle ────────────────────────────────────────────────

    def tool_start(self, tool_name: str) -> None:
        """
        Record that a recon tool is about to execute.

        Looks up tool_fingerprints.json to include weight and
        detection_risk metadata in the event payload.

        Emits event: TOOL_START  (includes weight, detection_risk from fingerprint DB)
        Logs:  INFO  "  [Tool] Starting: <tool_name>"

        Args:
            tool_name: Module-level tool identifier (e.g. "subfinder").
        """
        ...

    def tool_complete(self, tool_name: str, count: int) -> None:
        """
        Record successful completion of a tool and its result count.

        Emits event: TOOL_COMPLETE  (includes result count, elapsed duration)
        Logs:  SUCCESS  "  [Tool] <tool_name>: <count> results in <duration>s"

        Args:
            tool_name: Must match a prior tool_start call.
            count:     Number of results returned by the tool
                       (e.g. len(instance.results)).
        """
        ...

    def tool_skipped(self, tool_name: str, reason: str) -> None:
        """
        Record that a tool was intentionally skipped before execution.

        Called by orchestrator when any of the 4-gate checks fail
        (tag condition, efficiency filter, or budget limit).

        Emits event: TOOL_SKIPPED  (includes skip reason string)
        Logs:  DEBUG  "  [Skip] <tool_name> — <reason>"

        Args:
            tool_name: Tool that was skipped.
            reason:    Human-readable skip reason, e.g.:
                         "tag=cdn_detected conf=None < required=medium"
                         "efficiency_filter: data already sufficient"
                         "budget_exceeded"
        """
        ...

    def tool_error(self, tool_name: str, error: Exception) -> None:
        """
        Record an unhandled exception raised during tool execution.

        Emits event: TOOL_ERROR  (includes str(error))
        Logs:  ERROR  "  [Error] <tool_name>: <error>"

        Args:
            tool_name: Tool that raised the exception.
            error:     The caught exception object.
        """
        ...

    # ── Tag Events ────────────────────────────────────────────────────

    def tag_set(self, tag: str, confidence: str, source: str) -> None:
        """
        Record that the tag manager has set or updated an intelligence tag.

        Emits event: TAG_SET
        Logs:  INFO  "  [Tag] <tag> = <confidence> (src:<source>)"

        Args:
            tag:        Tag name (e.g. "cdn_detected", "waf_present").
            confidence: Confidence level string: "low" | "medium" | "high".
            source:     What produced the tag
                        (e.g. "passive_recon_completion", "subfinder").
        """
        ...

    # ── Private Helpers ───────────────────────────────────────────────

    def _write_event(self, event_type: str, data: dict[str, Any]) -> None:
        """
        Serialise and append one structured event to scan_events.jsonl.

        Each line written is a self-contained JSON object:
            {"event": "<EVENT_TYPE>", "ts": "<ISO-8601>", ...data fields}

        Args:
            event_type: String constant identifying the event
                        (e.g. "TOOL_START", "PHASE_END").
            data:       Dict of event-specific fields to merge into the record.
        """
        ...

    def _ts(self) -> str:
        """
        Return current UTC time as an ISO-8601 string.

        Returns:
            e.g. "2025-06-01T14:32:05.123456"
        """
        ...

    def _human_duration(self, seconds: float) -> str:
        """
        Convert a float duration in seconds to a human-readable string.

        Examples:
            3.5  → "3.5s"
            90.0 → "1m 30s"

        Args:
            seconds: Elapsed time in seconds.

        Returns:
            Formatted string for display in log messages.
        """
        ...

    def _get_fingerprint(self, tool_name: str) -> dict[str, Any]:
        """
        Look up a tool's metadata from data/tool_fingerprints.json.

        Returns the fingerprint dict for the given tool if found,
        otherwise returns an empty dict (callers must handle missing keys).

        Used by tool_start() to attach weight and detection_risk to events.

        Args:
            tool_name: Tool identifier to look up.

        Returns:
            Dict with keys such as "weight", "detection_risk", "category", etc.
            Empty dict if the tool is not registered in the fingerprint DB.
        """
        ...
