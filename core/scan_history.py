# core/scan_history.py
# Author         : Member 4
# Responsibility : Record scan metadata to a central database for the dashboard.
# ------------------------------------------------------------

import os
import json
import sqlite3
from datetime import datetime

class ScanHistory:
    def __init__(self, db_path: str = "~/.huntforge/history.db"):
        self.db_path = os.path.expanduser(db_path)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
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
        conn.close()

    def record_start(self, domain: str, output_dir: str) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO scans (domain, start_time, status, output_dir) VALUES (?, ?, ?, ?)',
            (domain, datetime.utcnow().isoformat(), 'RUNNING', output_dir)
        )
        scan_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return scan_id
        
    def record_end(self, scan_id: int, status: str, tag_count: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE scans SET end_time = ?, status = ?, tag_count = ? WHERE id = ?',
            (datetime.utcnow().isoformat(), status, tag_count, scan_id)
        )
        conn.commit()
        conn.close()
