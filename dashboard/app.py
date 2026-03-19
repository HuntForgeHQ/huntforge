from flask import Flask, render_template, request, jsonify
import os
import json
import sqlite3

app = Flask(__name__)

DB_PATH = os.path.expanduser("~/.huntforge/history.db")

def get_db_connection():
    if not os.path.exists(DB_PATH):
        return None
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    scans = []
    if conn:
        scans = conn.execute('SELECT * FROM scans ORDER BY id DESC LIMIT 50').fetchall()
        conn.close()
    return render_template('index.html', scans=scans)

@app.route('/scan/<int:scan_id>')
def view_scan(scan_id):
    conn = get_db_connection()
    if not conn:
        return "Database not found", 404
        
    scan = conn.execute('SELECT * FROM scans WHERE id = ?', (scan_id,)).fetchone()
    conn.close()
    
    if not scan:
        return "Scan not found", 404
        
    output_dir = scan['output_dir']
    
    # Load tags
    tags = {}
    tags_path = os.path.join(output_dir, 'active_tags.json')
    if os.path.exists(tags_path):
        with open(tags_path, 'r') as f:
            tags = json.load(f)
            
    # Load budget
    budget = {}
    budget_path = os.path.join(output_dir, 'processed', 'budget_status.json')
    if os.path.exists(budget_path):
        with open(budget_path, 'r') as f:
            budget = json.load(f)
            
    return render_template('scan_detail.html', scan=scan, tags=tags, budget=budget)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
