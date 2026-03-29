# core/tag_manager.py
# Author         : Member 1
# Responsibility : Store and retrieve tags set by tool modules.
#                  Acts as the shared knowledge board for the scan.
#                  Every tool reads from and writes to this.
# ------------------------------------------------------------

from datetime import datetime


# Confidence ranking — higher number = more confident
CONFIDENCE_RANK = {
    'low':    1,
    'medium': 2,
    'high':   3,
}


class TagManager:
    """
    Shared knowledge board for the entire scan.

    Tool modules write to it via add().
    Orchestrator reads from it via has() for gate checks.
    Dashboard reads from it via get_all() to display findings.
    Saved to active_tags.json at end of scan.

    Example usage:

        # Module sets a tag:
        tag_manager.add(
            tag        = 'has_subdomains',
            confidence = 'high',
            evidence   = ['api.example.com', 'admin.example.com'],
            source     = 'subfinder'
        )

        # Orchestrator checks a tag:
        if tag_manager.has('has_subdomains'):
            # run phase 2

        # Orchestrator checks with minimum confidence:
        if tag_manager.has('has_wordpress', min_confidence='medium'):
            # run wordpress scanner
    """

    def __init__(self):
        # Internal store — dict of tag_name → tag_data
        self._tags = {}

    @property
    def tags(self):
        return self._tags

    @tags.setter
    def tags(self, value):
        self._tags = value

    # ── Write ─────────────────────────────────────────────────────

    def add(self, tag: str, confidence: str = 'low',
            evidence: list = None, source: str = '') -> None:
        """
        Set a tag on the knowledge board.

        If the tag already exists — only update it if the new
        confidence is HIGHER than the existing one.
        Never downgrade a tag's confidence.

        Parameters:
            tag        : tag name e.g. 'has_subdomains'
            confidence : 'low', 'medium', or 'high'
            evidence   : list of examples that prove this tag
                         e.g. ['api.example.com', 'admin.example.com']
            source     : which tool set this tag e.g. 'subfinder'

        Example:
            tag_manager.add(
                tag        = 'has_subdomains',
                confidence = 'high',
                evidence   = ['api.example.com'],
                source     = 'subfinder'
            )
        """
        # Validate confidence value
        if confidence not in CONFIDENCE_RANK:
            confidence = 'low'

        # If tag already exists — only upgrade, never downgrade
        if tag in self._tags:
            existing_rank = CONFIDENCE_RANK[self._tags[tag]['confidence']]
            new_rank      = CONFIDENCE_RANK[confidence]

            if new_rank <= existing_rank:
                # New confidence is same or lower — don't overwrite
                return

        # Set the tag
        self._tags[tag] = {
            'confidence': confidence,
            'evidence':   evidence or [],
            'source':     source,
            'set_at':     datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    # ── Read ──────────────────────────────────────────────────────

    def has(self, tag: str, min_confidence: str = 'low') -> bool:
        """
        Check if a tag exists with at least the given confidence.

        Used by orchestrator in Gate 1 before running a phase.

        Parameters:
            tag            : tag name to check
            min_confidence : minimum required confidence level
                             'low' / 'medium' / 'high'
                             default: 'low' (tag just needs to exist)

        Returns:
            True  if tag exists AND confidence >= min_confidence
            False otherwise

        Example:
            # Just check if tag exists:
            tag_manager.has('has_subdomains')

            # Check with minimum confidence:
            tag_manager.has('has_wordpress', min_confidence='medium')
        """
        if tag not in self._tags:
            return False

        existing_rank = CONFIDENCE_RANK[self._tags[tag]['confidence']]
        required_rank = CONFIDENCE_RANK.get(min_confidence, 1)

        return existing_rank >= required_rank

    def get(self, tag: str) -> dict:
        """
        Get the full data for a specific tag.

        Returns None if tag doesn't exist.

        Example:
            data = tag_manager.get('has_subdomains')
            # Returns:
            # {
            #     'confidence': 'high',
            #     'evidence':   ['api.example.com'],
            #     'source':     'subfinder',
            #     'set_at':     '2024-01-01 12:00:00'
            # }
        """
        return self._tags.get(tag, None)

    def get_all(self) -> dict:
        """
        Get every tag currently set.

        Used by:
            Dashboard — to display all findings
            Report generator — to include in final report
            save_to_file() — to write active_tags.json

        Returns:
            dict of all tags and their data
        """
        return dict(self._tags)

    def get_by_confidence(self, confidence: str) -> dict:
        """
        Get all tags at a specific confidence level.

        Example:
            high_confidence = tag_manager.get_by_confidence('high')
        """
        return {
            tag: data
            for tag, data in self._tags.items()
            if data['confidence'] == confidence
        }

    # ── Utility ───────────────────────────────────────────────────

    def count(self) -> int:
        """Total number of tags currently set."""
        return len(self._tags)

    def save_to_file(self, output_dir: str) -> None:
        """
        Save all tags to active_tags.json.
        Called by orchestrator at end of each phase.
        Dashboard reads this file to display live progress.

        Output format:
        {
            "has_subdomains": {
                "confidence": "high",
                "evidence":   ["api.example.com"],
                "source":     "subfinder",
                "set_at":     "2024-01-01 12:00:00"
            },
            ...
        }
        """
        import json
        import os

        filepath = os.path.join(output_dir, 'processed', 'active_tags.json')
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, 'w') as f:
            json.dump(self._tags, f, indent=2)

    def __repr__(self) -> str:
        """Print-friendly summary of all tags."""
        if not self._tags:
            return "TagManager: no tags set"
        lines = ["TagManager:"]
        for tag, data in self._tags.items():
            lines.append(
                f"  {tag:<35} "
                f"{data['confidence']:<8} "
                f"(source: {data['source']})"
            )
        return '\n'.join(lines)