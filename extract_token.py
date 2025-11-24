#!/usr/bin/env python3
"""
Extract authentication token from mitmproxy flows file
"""

from mitmproxy import io
from mitmproxy.exceptions import FlowReadException
import json


def extract_auth_token(filename='flows/traeger_mitmproxy.flows'):
    """Extract the most recent auth token from flows."""
    
    auth_tokens = []
    
    with open(filename, "rb") as logfile:
        freader = io.FlowReader(logfile)
        try:
            for flow in freader.stream():
                if hasattr(flow, 'request'):
                    request = flow.request
                    
                    # Look for Traeger API calls with auth
                    if 'traeger' in request.host.lower():
                        headers = dict(request.headers)
                        if 'authorization' in headers:
                            token = headers['authorization']
                            auth_tokens.append({
                                'token': token,
                                'host': request.host,
                                'path': request.path,
                                'method': request.method
                            })
        except FlowReadException as e:
            print(f"Error reading flows: {e}")
    
    if auth_tokens:
        # Return the last (most recent) token
        latest = auth_tokens[-1]
        print(f"Found {len(auth_tokens)} API calls with auth tokens")
        print(f"\nLatest auth token from:")
        print(f"  Host: {latest['host']}")
        print(f"  Path: {latest['path']}")
        print(f"\nAuth Token:")
        print(latest['token'])
        print("\n" + "="*80)
        print("Copy this token and use it in traeger_client.py")
        print("Note: This token will expire (typically after 1 hour)")
        print("="*80)
        
        # Save to a config file
        config = {
            'auth_token': latest['token'],
            'grill_id': '682719A9F8B4',  # From your flows
            'extracted_at': str(auth_tokens[-1])
        }
        
        with open('traeger_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        print("\nConfiguration saved to traeger_config.json")
        
        return latest['token']
    else:
        print("No auth tokens found in flows!")
        return None


if __name__ == '__main__':
    extract_auth_token()
