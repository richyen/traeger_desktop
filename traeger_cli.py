#!/usr/bin/env python3
"""
Simple CLI tool for controlling your Traeger grill
"""

import argparse
import json
import sys
import time
from traeger_client import TraegerClient


def load_config():
    """Load configuration from file."""
    try:
        with open('traeger_config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: traeger_config.json not found!")
        print("Run: python extract_token.py first")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Control your Traeger grill from the command line',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Get current grill status
  python traeger_cli.py status
  
  # Set grill temperature to 225°F
  python traeger_cli.py temp 225
  
  # Set probe 0 alarm to 165°F (for chicken)
  python traeger_cli.py probe 0 165
  
  # Clear probe 0 alarm
  python traeger_cli.py probe 0 --clear
  
  # Turn grill on
  python traeger_cli.py power on
  
  # Turn grill off
  python traeger_cli.py power off
  
  # Start a cook session with metadata
  python traeger_cli.py cook start --protein chicken --temp 165
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Status command
    subparsers.add_parser('status', help='Get current grill status')
    
    # Temperature command
    temp_parser = subparsers.add_parser('temp', help='Set grill temperature')
    temp_parser.add_argument('temperature', type=int, help='Temperature in Fahrenheit (165-500)')
    
    # Probe command
    probe_parser = subparsers.add_parser('probe', help='Set or clear probe alarm')
    probe_parser.add_argument('probe_id', type=int, choices=[0, 1, 2, 3], 
                             help='Probe number (0-3)')
    probe_parser.add_argument('temperature', type=int, nargs='?', 
                             help='Target temperature in Fahrenheit')
    probe_parser.add_argument('--clear', action='store_true', 
                             help='Clear the probe alarm')
    
    # Power command
    power_parser = subparsers.add_parser('power', help='Turn grill on or off')
    power_parser.add_argument('state', choices=['on', 'off'], help='Power state')
    
    # Cook command
    cook_parser = subparsers.add_parser('cook', help='Manage cook sessions')
    cook_parser.add_argument('action', choices=['start'], help='Cook action')
    cook_parser.add_argument('--protein', default='manual', 
                            help='Type of protein (beef, chicken, pork, fish, manual)')
    cook_parser.add_argument('--cut', default='manual', 
                            help='Cut of meat (steak, brisket, ribs, breast, etc.)')
    cook_parser.add_argument('--probe', type=int, default=0, choices=[0, 1, 2, 3],
                            help='Probe to use (0-3)')
    cook_parser.add_argument('--temp', type=int, default=165,
                            help='Target temperature in Fahrenheit')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Load configuration
    config = load_config()
    
    # Initialize client
    try:
        client = TraegerClient(config['auth_token'])
        client.set_grill(config['grill_id'])
    except Exception as e:
        print(f"Error initializing client: {e}")
        print("\nYour auth token may have expired. Please:")
        print("1. Capture new flows with mitmproxy")
        print("2. Run: python extract_token.py")
        sys.exit(1)
    
    # Execute command
    try:
        if args.command == 'status':
            print("Requesting grill status...")
            response = client.request_status()
            print(f"Response: {json.dumps(response, indent=2)}")
            
        elif args.command == 'temp':
            if args.temperature < 165 or args.temperature > 500:
                print("Warning: Temperature should be between 165°F and 500°F")
            response = client.set_temperature(args.temperature)
            print(f"✓ Temperature set to {args.temperature}°F")
            
        elif args.command == 'probe':
            if args.clear:
                response = client.clear_probe_alarm(args.probe_id)
                print(f"✓ Probe {args.probe_id} alarm cleared")
            else:
                if not args.temperature:
                    print("Error: Temperature required (or use --clear)")
                    sys.exit(1)
                response = client.set_probe_alarm(args.probe_id, args.temperature)
                print(f"✓ Probe {args.probe_id} alarm set to {args.temperature}°F")
                
        elif args.command == 'power':
            if args.state == 'on':
                response = client.turn_on()
                print("✓ Grill turned on")
            else:
                response = client.turn_off()
                print("✓ Grill turned off")
                
        elif args.command == 'cook':
            if args.action == 'start':
                cook_id = f"{config['grill_id']}{int(time.time())}"
                response = client.upsert_cook_metadata(
                    cook_id=cook_id,
                    protein=args.protein,
                    cut=args.cut,
                    probe_id=f"p{args.probe}",
                    target_temp=args.temp
                )
                print(f"✓ Cook session started:")
                print(f"  Cook ID: {cook_id}")
                print(f"  Protein: {args.protein}")
                print(f"  Cut: {args.cut}")
                print(f"  Probe: p{args.probe}")
                print(f"  Target: {args.temp}°F")
                
                # Also set the probe alarm
                client.set_probe_alarm(args.probe, args.temp)
                print(f"✓ Probe {args.probe} alarm set to {args.temp}°F")
                
    except requests.exceptions.HTTPError as e:
        print(f"API Error: {e}")
        if e.response.status_code == 401:
            print("\nAuthentication failed. Your token may have expired.")
            print("Please capture new flows and run: python extract_token.py")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    import requests
    main()
