from flask import Flask, render_template, request, jsonify, abort
import os
import json
import sqlite3

app = Flask(__name__)

DB_PATH = os.path.expanduser("~/.huntforge/history.db")

def get_db_connection():
    if not os.path.exists(DB_PATH):
        return None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error:
        return None

@app.route('/')
def index():
    conn = get_db_connection()
    scans = []
    if conn:
        try:
            scans = conn.execute('SELECT * FROM scans ORDER BY id DESC LIMIT 50').fetchall()
        except sqlite3.Error:
            scans = []
        finally:
            conn.close()
    return render_template('index.html', scans=scans)

@app.route('/scan/<int:scan_id>')
def view_scan(scan_id):
    conn = get_db_connection()
    if not conn:
        return render_template('scan_detail.html', scan=None, tags={}, budget={}), 404

    try:
        scan = conn.execute('SELECT * FROM scans WHERE id = ?', (scan_id,)).fetchone()
    except sqlite3.Error:
        scan = None
    finally:
        conn.close()

    if not scan:
        return render_template('scan_detail.html', scan=None, tags={}, budget={}), 404

    output_dir = scan['output_dir']

    tags = {}
    tags_path = os.path.join(output_dir, 'active_tags.json')
    try:
        if os.path.exists(tags_path):
            with open(tags_path, 'r') as f:
                tags = json.load(f)
    except (json.JSONDecodeError, OSError):
        tags = {}

    budget = {}
    budget_path = os.path.join(output_dir, 'processed', 'budget_status.json')
    try:
        if os.path.exists(budget_path):
            with open(budget_path, 'r') as f:
                budget = json.load(f)
    except (json.JSONDecodeError, OSError):
        budget = {}

    return render_template('scan_detail.html', scan=scan, tags=tags, budget=budget)

@app.route('/scan/<int:scan_id>/output/<path:filename>')
def view_scan_output(scan_id, filename):
    conn = get_db_connection()
    if not conn:
        abort(404)

    try:
        scan = conn.execute('SELECT * FROM scans WHERE id = ?', (scan_id,)).fetchone()
    except sqlite3.Error:
        scan = None
    finally:
        conn.close()

    if not scan:
        abort(404)

    filepath = os.path.normpath(os.path.join(scan['output_dir'], filename))
    if not filepath.startswith(os.path.normpath(scan['output_dir'])):
        abort(403)

    if not os.path.isfile(filepath):
        abort(404)

    content = ''
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except OSError:
        abort(500)

    return render_template('scan_output.html', scan=scan, filename=filename, content=content)

if __name__ == '__main__':
    port = int(os.environ.get('FLASK_RUN_PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
