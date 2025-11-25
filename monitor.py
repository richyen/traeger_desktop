#!/usr/bin/env python3
"""
Background temperature monitoring service
Continuously polls Traeger API and saves to database
"""

import time
import sqlite3
import os
import sys
from datetime import datetime
from traeger_client import TraegerClient

DB_PATH = os.environ.get('DB_PATH', '/app/data/traeger.db')
POLL_INTERVAL = int(os.environ.get('POLL_INTERVAL', '30'))  # seconds

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
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

def save_reading(grill_id, grill_temp, probe1_temp, probe2_temp, set_temp):
    """Save temperature reading to database"""
    conn = get_db()
    conn.execute('''
        INSERT INTO temperature_readings 
        (timestamp, grill_temp, probe1_temp, probe2_temp, set_temp, grill_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        datetime.now().isoformat(),
        grill_temp,
        probe1_temp,
        probe2_temp,
        set_temp,
        grill_id
    ))
    conn.commit()
    conn.close()

def monitor_loop(client, grill_id):
    """Main monitoring loop"""
    print(f"🔥 Starting temperature monitoring (polling every {POLL_INTERVAL}s)...")
    
    while True:
        try:
            # Get current status
            status = client.get_status_from_api(grill_id)
            
            if status:
                grill_temp = status.get('grill_temp')
                probe1_temp = status.get('probe1_temp')
                probe2_temp = status.get('probe2_temp')
                set_temp = status.get('set_temp')
                
                # Save to database
                save_reading(grill_id, grill_temp, probe1_temp, probe2_temp, set_temp)
                
                # Print status
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"[{timestamp}] Grill: {grill_temp}°F", end='')
                if probe1_temp:
                    print(f" | Probe1: {probe1_temp}°F", end='')
                if probe2_temp:
                    print(f" | Probe2: {probe2_temp}°F", end='')
                if set_temp:
                    print(f" | Target: {set_temp}°F", end='')
                print()
            else:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ⚠️  Could not fetch status")
            
        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ❌ Error: {e}")
        
        # Wait before next poll
        time.sleep(POLL_INTERVAL)

def main():
    """Main entry point"""
    # Get credentials from environment
    token = os.environ.get('TRAEGER_TOKEN')
    email = os.environ.get('TRAEGER_EMAIL')
    password = os.environ.get('TRAEGER_PASSWORD')
    
    if not token and not (email and password):
        print("❌ Error: Must provide either TRAEGER_TOKEN or both TRAEGER_EMAIL and TRAEGER_PASSWORD")
        print("\nTo get your token:")
        print("1. Check traeger_config.json if you have it")
        print("2. Or extract from flows: python extract_token.py")
        print("\nOr set TRAEGER_EMAIL and TRAEGER_PASSWORD in .env file")
        sys.exit(1)
    
    # Initialize database
    os.makedirs('/app/data', exist_ok=True)
    init_db()
    
    # Create client
    client = TraegerClient(token) if token else TraegerClient()
    
    try:
        if token:
            print("🔐 Using provided token...")
        else:
            print(f"🔐 Logging in as {email}...")
            if not client.login(email, password):
                print("❌ Authentication failed!")
                sys.exit(1)
            print("✅ Login successful!")
        
        # Get grills
        print("🔍 Fetching grills...")
        grills = client.get_grills()
        
        if not grills:
            print("❌ No grills found!")
            sys.exit(1)
        
        grill = grills[0]
        grill_id = grill['thingName']
        grill_name = grill.get('friendlyName', grill_id)
        
        print(f"✅ Connected to grill: {grill_name} ({grill_id})")
        
        # Start monitoring
        monitor_loop(client, grill_id)
        
    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
