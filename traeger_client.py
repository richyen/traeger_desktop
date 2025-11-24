#!/usr/bin/env python3
"""
Traeger Grill Client - Control your Traeger grill from your laptop
Based on reverse engineering the Traeger iOS app API calls
"""

import requests
import json
import time
from typing import Dict, Optional, List
import paho.mqtt.client as mqtt
from datetime import datetime


class TraegerClient:
    """Client for interacting with Traeger grills via their API."""
    
    def __init__(self, auth_token: str):
        """
        Initialize the Traeger client.
        
        Args:
            auth_token: JWT token from AWS Cognito (extract from mitmproxy flows)
        """
        self.auth_token = auth_token
        self.base_url = "https://mobile-iot-api.iot.traegergrills.io"
        self.graphql_url = "https://api.kube-gql.prod.traegergrills.io/"
        self.headers = {
            "authorization": auth_token,
            "content-type": "application/json",
            "accept": "*/*",
            "user-agent": "Traeger/1933 CFNetwork/3860.100.1"
        }
        self.grill_id = None
        self.grill_status = {}
        self.mqtt_client = None
        
    def get_grills(self) -> List[Dict]:
        """Get list of grills associated with this account."""
        response = requests.get(
            f"{self.base_url}/users/self",
            headers=self.headers
        )
        response.raise_for_status()
        user_data = response.json()
        
        # Get things (grills) from the user data
        if 'things' in user_data:
            return user_data['things']
        return []
    
    def set_grill(self, grill_id: str):
        """Set the active grill ID."""
        self.grill_id = grill_id
        print(f"Active grill set to: {grill_id}")
    
    def send_command(self, command: str) -> Dict:
        """
        Send a command to the grill.
        
        Args:
            command: Command string to send to the grill
            
        Returns:
            Response from the API
        """
        if not self.grill_id:
            raise ValueError("No grill ID set. Call set_grill() first.")
        
        url = f"{self.base_url}/things/{self.grill_id}/commands"
        payload = {"command": command}
        
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()
    
    def set_temperature(self, temp_fahrenheit: int) -> Dict:
        """
        Set the grill temperature.
        
        Args:
            temp_fahrenheit: Target temperature in Fahrenheit (typically 165-500°F)
            
        Returns:
            Response from the API
        """
        # Command format: "112,<temp>"
        command = f"112,{temp_fahrenheit}"
        print(f"Setting grill temperature to {temp_fahrenheit}°F...")
        return self.send_command(command)
    
    def set_probe_alarm(self, probe_id: int, target_temp: int) -> Dict:
        """
        Set a probe temperature alarm.
        
        Args:
            probe_id: Probe number (0-3 for probes p0-p3)
            target_temp: Target temperature in Fahrenheit
            
        Returns:
            Response from the API
        """
        # Command format: "120,10,p<probe_id>,<temp>"
        # The "10" appears to be a fixed parameter
        command = f"120,10,p{probe_id},{target_temp}"
        print(f"Setting probe {probe_id} alarm to {target_temp}°F...")
        return self.send_command(command)
    
    def clear_probe_alarm(self, probe_id: int) -> Dict:
        """
        Clear a probe temperature alarm.
        
        Args:
            probe_id: Probe number (0-3)
            
        Returns:
            Response from the API
        """
        # Set alarm to 0 to clear it
        command = f"120,10,p{probe_id},0"
        print(f"Clearing probe {probe_id} alarm...")
        return self.send_command(command)
    
    def request_status(self) -> Dict:
        """Request current grill status."""
        # Command "113" appears to request status
        print("Requesting grill status...")
        return self.send_command("113")
    
    def turn_on(self) -> Dict:
        """Turn the grill on."""
        print("Turning grill on...")
        return self.send_command("90,1")
    
    def turn_off(self) -> Dict:
        """Turn the grill off."""
        print("Turning grill off...")
        return self.send_command("90,0")
    
    def get_mqtt_connection(self) -> Dict:
        """Get MQTT WebSocket connection details for real-time updates."""
        response = requests.post(
            f"{self.base_url}/mqtt-connections",
            headers=self.headers,
            json={}
        )
        response.raise_for_status()
        return response.json()
    
    def connect_mqtt(self, on_message_callback=None):
        """
        Connect to MQTT for real-time grill status updates.
        
        Args:
            on_message_callback: Optional callback function for handling messages
        """
        if not self.grill_id:
            raise ValueError("No grill ID set. Call set_grill() first.")
        
        mqtt_info = self.get_mqtt_connection()
        
        # Parse the WebSocket URL to get MQTT broker details
        # Note: The actual implementation would need to handle AWS IoT WebSocket authentication
        print(f"MQTT connection expires at: {datetime.fromtimestamp(mqtt_info['expiresAt'])}")
        print(f"Connection valid for: {mqtt_info['expirationSeconds']} seconds")
        print("\nNote: MQTT WebSocket connection requires additional AWS IoT authentication.")
        print(f"Subscribe to topic: prod/thing/{self.grill_id}/status")
        
        return mqtt_info
    
    def upsert_cook_metadata(self, cook_id: str, protein: str = "manual", 
                            cut: str = "manual", probe_id: str = "p0",
                            target_temp: int = 165) -> Dict:
        """
        Create or update cook metadata (for tracking what you're cooking).
        
        Args:
            cook_id: Cook ID (usually grill_id + timestamp)
            protein: Type of protein (e.g., "beef", "chicken", "pork", "manual")
            cut: Cut of meat (e.g., "steak", "brisket", "manual")
            probe_id: Which probe to use (p0-p3)
            target_temp: Target temperature in Fahrenheit
            
        Returns:
            Response from the GraphQL API
        """
        query = """
        mutation UpsertCookMetadata($cookId: String!, $protein: String, $cut: String, 
                                    $donenessLevel: String, $probeId: String!, 
                                    $targetTemperature: Int!) {
          upsertCookMetadata(
            input: {
              cookId: $cookId, 
              protein: $protein, 
              cut: $cut, 
              donenessLevel: $donenessLevel, 
              probeId: $probeId, 
              targetTemperature: $targetTemperature
            }
          ) {
            __typename
            cookId
            cut
            donenessLevel
            probeId
            protein
            targetTemperature
          }
        }
        """
        
        # Convert Fahrenheit to Celsius for the API
        target_temp_celsius = int((target_temp - 32) * 5 / 9)
        
        variables = {
            "cookId": cook_id,
            "protein": protein,
            "cut": cut,
            "donenessLevel": None,
            "probeId": probe_id,
            "targetTemperature": target_temp_celsius
        }
        
        payload = {
            "operationName": "UpsertCookMetadata",
            "query": query,
            "variables": variables
        }
        
        response = requests.post(self.graphql_url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()


def main():
    """Example usage of the Traeger client."""
    
    # TODO: Replace with your actual auth token from the mitmproxy flows
    # This token will expire, so you'll need to extract a fresh one from your flows
    auth_token = "YOUR_AUTH_TOKEN_HERE"
    
    # Example grill ID from your flows
    grill_id = "682719A9F8B4"
    
    # Initialize client
    client = TraegerClient(auth_token)
    client.set_grill(grill_id)
    
    # Example: Get current status
    print("\n=== Requesting Grill Status ===")
    status = client.request_status()
    print(f"Status response: {status}")
    
    # Example: Set grill temperature
    print("\n=== Setting Temperature ===")
    client.set_temperature(225)
    
    # Example: Set probe alarm
    print("\n=== Setting Probe Alarm ===")
    client.set_probe_alarm(probe_id=0, target_temp=165)
    
    # Example: Create cook metadata
    print("\n=== Creating Cook Metadata ===")
    cook_id = f"{grill_id}{int(time.time())}"
    client.upsert_cook_metadata(
        cook_id=cook_id,
        protein="chicken",
        cut="breast",
        probe_id="p0",
        target_temp=165
    )
    
    # Example: Connect to MQTT for real-time updates
    print("\n=== Getting MQTT Connection Info ===")
    mqtt_info = client.connect_mqtt()
    

if __name__ == "__main__":
    main()
