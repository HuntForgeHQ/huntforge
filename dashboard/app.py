from flask import Flask, render_template, request, jsonify, abort
import os
import json
import sqlite3

app = Flask(__name__)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.expanduser("~/.huntforge/history.db")

def resolve_output_dir(path):
    if not path:
        return None
    if os.path.isabs(path) and os.path.exists(path):
        return path
    # Try relative to project root
    abs_path = os.path.abspath(os.path.join(PROJECT_ROOT, path))
    if os.path.exists(abs_path):
        return abs_path
    # Try as-is (might be relative to dashboard CWD)
    if os.path.exists(path):
        return os.path.abspath(path)
    return None

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
    stats = {
        'total_targets': 0,
        'active_scans': 0,
        'total_tags': 0,
        'status_counts': {'COMPLETED': 0, 'FAILED': 0, 'RUNNING': 0, 'INTERRUPTED': 0}
    }
    
    if conn:
        try:
            scans = conn.execute('SELECT * FROM scans ORDER BY id DESC LIMIT 50').fetchall()
            
            unique_domains = set()
            for row in scans:
                unique_domains.add(row['domain'])
                if row['status'] == 'RUNNING':
                    stats['active_scans'] += 1
                stats['total_tags'] += (row['tag_count'] or 0)
                
                status_upper = row['status'].upper() if row['status'] else 'UNKNOWN'
                if status_upper in stats['status_counts']:
                    stats['status_counts'][status_upper] += 1
                else:
                    stats['status_counts'][status_upper] = 1
                    
            stats['total_targets'] = len(unique_domains)
            
        except sqlite3.Error as e:
            scans = []
        finally:
            conn.close()
            
    return render_template('index.html', scans=scans, stats=stats)

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

    output_dir = resolve_output_dir(scan['output_dir']) or scan['output_dir']

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
                budget_raw = json.load(f)
                # Map legacy and current keys for UI resilience
                budget = {
                    'requests_used': budget_raw.get('requests_used', budget_raw.get('requests_made', 0)),
                    'max_requests': budget_raw.get('max_requests', 'unlimited'),
                    'elapsed_minutes': budget_raw.get('elapsed_minutes', round(budget_raw.get('elapsed_seconds', 0) / 60, 2)),
                    'percent_used': budget_raw.get('percent_used', 0)
                }
    except (json.JSONDecodeError, OSError):
        budget = {}

    output_files = {'raw': [], 'processed': [], 'logs': []}
    if os.path.exists(output_dir):
        for sub in ['raw', 'processed', 'logs']:
            target_dir = os.path.join(output_dir, sub)
            if os.path.exists(target_dir):
                for f in os.listdir(target_dir):
                    if os.path.isfile(os.path.join(target_dir, f)):
                        output_files[sub].append(f"{sub}/{f}")

    return render_template('scan_detail.html', scan=scan, tags=tags, budget=budget, output_files=output_files)

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

    base_dir = resolve_output_dir(scan['output_dir']) or scan['output_dir']
    filepath = os.path.normpath(os.path.join(base_dir, filename))
    if not filepath.startswith(os.path.normpath(base_dir)):
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

@app.route('/api/scan/<int:scan_id>/urls', methods=['GET'])
def get_scan_urls(scan_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'DB connection failed'}), 500

    scan = conn.execute('SELECT * FROM scans WHERE id = ?', (scan_id,)).fetchone()
    conn.close()

    if not scan:
        return jsonify({'error': 'Scan not found'}), 404

    output_dir = resolve_output_dir(scan['output_dir']) or scan['output_dir']
    urls = set()
    
    all_urls_path = os.path.join(output_dir, 'processed', 'all_urls.txt')
    if os.path.exists(all_urls_path):
        try:
            with open(all_urls_path, 'r') as f:
                urls.update(line.strip() for line in f if line.strip())
        except Exception:
            pass

    params_path = os.path.join(output_dir, 'processed', 'parameters.json')
    if os.path.exists(params_path):
        try:
            with open(params_path, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    urls.update(str(item) for item in data)
        except Exception:
            pass
            
    return jsonify({'urls': sorted(urls)})

@app.route('/api/scan/<int:scan_id>/launch-precision', methods=['POST'])
def launch_precision_strike(scan_id):
    data = request.json
    if not data or 'urls' not in data:
        return jsonify({'error': 'Invalid request payload'}), 400
        
    urls = data['urls']
    if not urls:
        return jsonify({'error': 'No URLs provided'}), 400

    conn = get_db_connection()
    scan = conn.execute('SELECT domain, output_dir FROM scans WHERE id = ?', (scan_id,)).fetchone()
    conn.close()

    if not scan:
        return jsonify({'error': 'Scan not found'}), 404

    output_dir = resolve_output_dir(scan['output_dir']) or scan['output_dir']
    os.makedirs(output_dir, exist_ok=True)
    
    precision_path = os.path.join(output_dir, 'precision_targets.txt')
    with open(precision_path, 'w') as f:
        f.write('\n'.join(urls))
        
    import subprocess
    import sys
    
    # Launch totally detached
    subprocess.Popen(
        [sys.executable, 'huntforge.py', 'precision', scan['domain'], '--file', precision_path],
        cwd=PROJECT_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    return jsonify({'status': 'ok', 'message': 'Precision Strike Launched!'})


if __name__ == '__main__':
    port = int(os.environ.get('FLASK_RUN_PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
