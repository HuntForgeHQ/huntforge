# core/scan_history.py
# Author         : Member 4
# Responsibility : Record scan metadata to a central database for the dashboard.
# ------------------------------------------------------------

import os
import json
import sqlite3
from datetime import datetime
from typing import Optional

class ScanHistory:
    def __init__(self, db_path: str = "~/.huntforge/history.db"):
        self.db_path = os.path.expanduser(db_path)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    status TEXT NOT NULL,
                    tag_count INTEGER,
                    output_dir TEXT
                )
            ''')
            conn.commit()

    def record_start(self, domain: str, output_dir: str) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO scans (domain, start_time, status, output_dir) VALUES (?, ?, ?, ?)',
                (domain, datetime.utcnow().isoformat(), 'RUNNING', output_dir)
            )
            conn.commit()
            if cursor.lastrowid is None:
                raise RuntimeError("Failed to insert scan record")
            return cursor.lastrowid

    def record_end(self, scan_id: int, status: str, tag_count: int):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE scans SET end_time = ?, status = ?, tag_count = ? WHERE id = ?',
                (datetime.utcnow().isoformat(), status, tag_count, scan_id)
            )
            conn.commit()

    def get_recent(self, limit: int = 50) -> list:
        """Returns the most recent scans, newest first, up to `limit` rows."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM scans ORDER BY id DESC LIMIT ?',
                (limit,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_scan(self, scan_id: int) -> Optional[dict]:
        """Returns a single scan record by ID, or None if not found."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM scans WHERE id = ?',
                (scan_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
