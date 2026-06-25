#!/usr/bin/env python3
"""
Background temperature monitoring service
Continuously polls Traeger API and saves to database
"""

import time
import sqlite3
import os
import sys
import json
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

def _extract_temps(raw):
    """Extract grill/probe/set temps from a Traeger MQTT status payload.

    Traeger publishes a JSON document with sub-objects such as ``status``,
    ``details``, ``limits``, ``settings``, ``features`` and ``acc``. The live
    telemetry we care about lives under ``status``:

        status.grill           -> current grill temperature
        status.set             -> grill setpoint
        status.probe           -> probe 1 temperature (built-in meat probe)
        status.acc / acc[*]    -> accessory probes (if any)

    Field names are reused across firmware versions, but we still defensively
    fall back to common alternates so this code keeps working if Traeger
    tweaks the shape.
    """
    if not isinstance(raw, dict):
        return None, None, None, None

    candidates = [raw]
    for key in ('status', 'state', 'reported', 'shadow'):
        v = raw.get(key)
        if isinstance(v, dict):
            candidates.append(v)
            inner = v.get('reported') if isinstance(v.get('reported'), dict) else None
            if inner:
                candidates.append(inner)

    def first(*keys):
        for c in candidates:
            for k in keys:
                if k in c and c[k] is not None:
                    return c[k]
        return None

    grill_temp = first('grill', 'grill_temp', 'grillTemp', 'grillTemperature')
    set_temp = first('set', 'set_temp', 'setTemp', 'setTemperature', 'grill_set_temp')
    probe1_temp = first('probe', 'probe_a', 'probeA', 'probe1', 'probe1_temp', 'probe0', 'probe0_temp')
    probe2_temp = first('probe_b', 'probeB', 'probe2', 'probe2_temp')

    # Fall back to the accessory probes list for a second probe reading.
    if probe2_temp is None:
        status = raw.get('status') if isinstance(raw.get('status'), dict) else None
        acc_list = (status or raw).get('acc') if isinstance((status or raw).get('acc'), list) else None
        if acc_list:
            # Look for a probe-type accessory with a temperature reading.
            for acc in acc_list:
                if not isinstance(acc, dict):
                    continue
                if acc.get('type') in ('probe', 'probeMeat') or 'probe' in str(acc.get('uuid', '')).lower():
                    for k in ('value', 'temp', 'temperature', 'current'):
                        if acc.get(k) is not None:
                            probe2_temp = acc[k]
                            break
                    if probe2_temp is not None:
                        break

    return grill_temp, probe1_temp, probe2_temp, set_temp


def monitor_loop(client, grill_id):
    """Main monitoring loop.

    Telemetry from a Traeger grill is only available over MQTT (AWS IoT
    WebSocket). We open a persistent MQTT connection that updates
    ``client.grill_status`` whenever the grill publishes a message, then
    every ``POLL_INTERVAL`` seconds we snapshot the latest values into the
    database. The signed MQTT URL expires after ~1h, so we refresh the
    connection well before that.
    """
    print("🔌 Opening MQTT connection to AWS IoT for live telemetry...")
    mqttc = client.start_mqtt_listener()
    connection_started_at = time.time()
    # Refresh the signed URL before it expires (default expiry ~3600s).
    refresh_after_seconds = 55 * 60

    # Nudge the grill to publish its current state right away (otherwise it
    # only publishes on changes, so a sleeping grill never appears).
    try:
        time.sleep(2)  # give MQTT subscribe time to settle first
        client.request_status()
        print("📡 Sent status-request (cmd 90) so the grill publishes its state.")
    except Exception as e:
        print(f"   (warn) initial status-request failed: {e}")

    print(f"🔥 Saving readings every {POLL_INTERVAL}s...")
    logged_schema = False

    while True:
        try:
            # Refresh signed URL / MQTT connection before it expires.
            if time.time() - connection_started_at > refresh_after_seconds:
                print("🔄 Refreshing MQTT connection (signed URL nearing expiry)...")
                try:
                    mqttc.loop_stop()
                    mqttc.disconnect()
                except Exception as stop_err:
                    print(f"   (warn) error stopping old MQTT client: {stop_err}")
                mqttc = client.start_mqtt_listener()
                connection_started_at = time.time()

            status = client.grill_status or {}

            if status:
                if not logged_schema:
                    try:
                        top_keys = list(status.keys()) if isinstance(status, dict) else type(status).__name__
                        print(f"📜 MQTT status top-level keys: {top_keys}")
                        sample = json.dumps(status, default=str)[:1500]
                        print(f"📜 Sample payload: {sample}")
                    except Exception:
                        pass
                    logged_schema = True

                grill_temp, probe1_temp, probe2_temp, set_temp = _extract_temps(status)

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
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ⏳ Waiting for first MQTT status message...")
            
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

        # The client needs grill_id set on it so subsequent API calls know
        # which grill to query.
        client.grill_id = grill_id

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
