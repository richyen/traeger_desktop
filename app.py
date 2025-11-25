#!/usr/bin/env python3
"""
Traeger Temperature Monitoring Web Dashboard
Flask application serving real-time and historical temperature data
"""

from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta
import sqlite3
import os
from traeger_client import TraegerClient

app = Flask(__name__)

DB_PATH = os.environ.get('DB_PATH', '/app/data/traeger.db')

# Global Traeger client instance (shared with monitor.py via environment)
_traeger_client = None

def get_traeger_client():
    """Get or create Traeger client instance"""
    global _traeger_client
    if _traeger_client is None:
        token = os.environ.get('TRAEGER_TOKEN')
        email = os.environ.get('TRAEGER_EMAIL')
        password = os.environ.get('TRAEGER_PASSWORD')
        
        if not token and not (email and password):
            return None
        
        if token:
            _traeger_client = TraegerClient(token)
        else:
            _traeger_client = TraegerClient()
            if not _traeger_client.login(email, password):
                return None
        
        # Get first grill
        grills = _traeger_client.get_grills()
        if grills:
            _traeger_client.grill_id = grills[0]['thingName']
    
    return _traeger_client

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database schema"""
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS temperature_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME NOT NULL,
            grill_temp REAL,
            probe1_temp REAL,
            probe2_temp REAL,
            set_temp INTEGER,
            grill_id TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE INDEX IF NOT EXISTS idx_timestamp 
        ON temperature_readings(timestamp DESC)
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/current')
def current_temps():
    """Get most recent temperature reading"""
    conn = get_db()
    result = conn.execute('''
        SELECT * FROM temperature_readings 
        ORDER BY timestamp DESC 
        LIMIT 1
    ''').fetchone()
    conn.close()
    
    if result:
        return jsonify({
            'timestamp': result['timestamp'],
            'grill_temp': result['grill_temp'],
            'probe1_temp': result['probe1_temp'],
            'probe2_temp': result['probe2_temp'],
            'set_temp': result['set_temp']
        })
    return jsonify({})

@app.route('/api/recent')
def recent_temps():
    """Get last 2 hours of data for live graph"""
    hours = int(request.args.get('hours', 2))
    cutoff = datetime.now() - timedelta(hours=hours)
    
    conn = get_db()
    results = conn.execute('''
        SELECT timestamp, grill_temp, probe1_temp, probe2_temp, set_temp
        FROM temperature_readings 
        WHERE timestamp >= ?
        ORDER BY timestamp ASC
    ''', (cutoff.isoformat(),)).fetchall()
    conn.close()
    
    data = {
        'timestamps': [],
        'grill_temps': [],
        'probe1_temps': [],
        'probe2_temps': [],
        'set_temps': []
    }
    
    for row in results:
        data['timestamps'].append(row['timestamp'])
        data['grill_temps'].append(row['grill_temp'])
        data['probe1_temps'].append(row['probe1_temp'] if row['probe1_temp'] else None)
        data['probe2_temps'].append(row['probe2_temp'] if row['probe2_temp'] else None)
        data['set_temps'].append(row['set_temp'] if row['set_temp'] else None)
    
    return jsonify(data)

@app.route('/api/history')
def history():
    """Get historical data with date filters"""
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    
    query = 'SELECT * FROM temperature_readings WHERE 1=1'
    params = []
    
    if start_date:
        query += ' AND timestamp >= ?'
        params.append(start_date)
    if end_date:
        query += ' AND timestamp <= ?'
        params.append(end_date)
    
    query += ' ORDER BY timestamp DESC LIMIT 10000'
    
    conn = get_db()
    results = conn.execute(query, params).fetchall()
    conn.close()
    
    data = [{
        'timestamp': row['timestamp'],
        'grill_temp': row['grill_temp'],
        'probe1_temp': row['probe1_temp'],
        'probe2_temp': row['probe2_temp'],
        'set_temp': row['set_temp']
    } for row in results]
    
    return jsonify(data)

@app.route('/api/stats')
def stats():
    """Get cooking statistics"""
    conn = get_db()
    
    # Get overall stats
    overall = conn.execute('''
        SELECT 
            COUNT(*) as total_readings,
            MIN(timestamp) as first_reading,
            MAX(timestamp) as last_reading,
            AVG(grill_temp) as avg_grill_temp,
            MAX(grill_temp) as max_grill_temp
        FROM temperature_readings
    ''').fetchone()
    
    # Get today's stats
    today = datetime.now().date().isoformat()
    today_stats = conn.execute('''
        SELECT 
            COUNT(*) as readings_today,
            AVG(grill_temp) as avg_temp_today,
            MIN(timestamp) as cook_start,
            MAX(timestamp) as cook_end
        FROM temperature_readings
        WHERE DATE(timestamp) = ?
    ''', (today,)).fetchone()
    
    conn.close()
    
    return jsonify({
        'overall': {
            'total_readings': overall['total_readings'],
            'first_reading': overall['first_reading'],
            'last_reading': overall['last_reading'],
            'avg_grill_temp': round(overall['avg_grill_temp'], 1) if overall['avg_grill_temp'] else None,
            'max_grill_temp': overall['max_grill_temp']
        },
        'today': {
            'readings': today_stats['readings_today'],
            'avg_temp': round(today_stats['avg_temp_today'], 1) if today_stats['avg_temp_today'] else None,
            'cook_start': today_stats['cook_start'],
            'cook_end': today_stats['cook_end']
        }
    })

@app.route('/api/control/grill-temp', methods=['POST'])
def set_grill_temp():
    """Set grill temperature"""
    data = request.get_json()
    temp = data.get('temperature')
    
    if not temp or not isinstance(temp, (int, float)):
        return jsonify({'success': False, 'error': 'Invalid temperature'}), 400
    
    temp = int(temp)
    if temp < 165 or temp > 500:
        return jsonify({'success': False, 'error': 'Temperature must be between 165-500°F'}), 400
    
    client = get_traeger_client()
    if not client:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        result = client.set_temperature(temp)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/control/probe-target', methods=['POST'])
def set_probe_target():
    """Set probe target temperature"""
    data = request.get_json()
    probe_id = data.get('probe_id')
    temp = data.get('temperature')
    
    if probe_id not in [0, 1]:
        return jsonify({'success': False, 'error': 'Probe ID must be 0 or 1'}), 400
    
    if not temp or not isinstance(temp, (int, float)):
        return jsonify({'success': False, 'error': 'Invalid temperature'}), 400
    
    temp = int(temp)
    if temp < 0 or temp > 500:
        return jsonify({'success': False, 'error': 'Temperature must be between 0-500°F (0 to clear)'}), 400
    
    client = get_traeger_client()
    if not client:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        if temp == 0:
            result = client.clear_probe_alarm(probe_id)
        else:
            result = client.set_probe_alarm(probe_id, temp)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    # Initialize database
    os.makedirs('/app/data', exist_ok=True)
    init_db()
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)
