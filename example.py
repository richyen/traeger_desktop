#!/usr/bin/env python3
"""
Example script showing how to use the Traeger client
"""

from traeger_client import TraegerClient
import json
import time

def main():
    print("="*80)
    print("Traeger Grill Controller - Example Usage")
    print("="*80)
    
    # Load configuration
    print("\n1. Loading configuration...")
    try:
        with open('traeger_config.json', 'r') as f:
            config = json.load(f)
        print(f"   ✓ Config loaded")
        print(f"   ✓ Grill ID: {config['grill_id']}")
    except FileNotFoundError:
        print("   ✗ Error: traeger_config.json not found!")
        print("   Run: python extract_token.py")
        return
    
    # Initialize client
    print("\n2. Initializing Traeger client...")
    client = TraegerClient(config['auth_token'])
    client.set_grill(config['grill_id'])
    print("   ✓ Client ready")
    
    # Example 1: Request status
    print("\n3. Requesting grill status...")
    try:
        status = client.request_status()
        print(f"   ✓ Status requested")
        print(f"   Response: {json.dumps(status, indent=2)}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        print("   Note: Your grill may be offline or token expired")
    
    # Example 2: Set temperature
    print("\n4. Example: Setting grill temperature to 225°F...")
    print("   (Uncomment to actually send this command)")
    # Uncomment the next line to actually set the temperature:
    # client.set_temperature(225)
    print("   Command: 112,225")
    
    # Example 3: Set probe alarm
    print("\n5. Example: Setting probe 0 alarm to 165°F (chicken)...")
    print("   (Uncomment to actually send this command)")
    # Uncomment the next line to actually set the alarm:
    # client.set_probe_alarm(probe_id=0, target_temp=165)
    print("   Command: 120,10,p0,165")
    
    # Example 4: Start a cook session
    print("\n6. Example: Starting a chicken breast cook session...")
    print("   (Uncomment to actually create the session)")
    # Uncomment these lines to actually create a cook session:
    # cook_id = f"{config['grill_id']}{int(time.time())}"
    # client.upsert_cook_metadata(
    #     cook_id=cook_id,
    #     protein="chicken",
    #     cut="breast",
    #     probe_id="p0",
    #     target_temp=165
    # )
    print("   This would create metadata for tracking your cook")
    
    print("\n" + "="*80)
    print("Examples complete!")
    print("\nTo actually send commands, edit this file and uncomment the lines.")
    print("Or use the CLI: python traeger_cli.py --help")
    print("="*80)


if __name__ == '__main__':
    main()
