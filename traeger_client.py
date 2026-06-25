#!/usr/bin/env python3
"""
Traeger Grill Client - Control your Traeger grill from your laptop
Based on reverse engineering the Traeger iOS app API calls
"""

import requests
import json
import time
from typing import Dict, Optional, List
from datetime import datetime


class TraegerClient:
    """Client for interacting with Traeger grills via their API."""
    
    def __init__(self, auth_token: str = None):
        """
        Initialize the Traeger client.
        
        Args:
            auth_token: JWT token (idToken) from Traeger auth (optional if using login())
        """
        self.auth_token = auth_token
        self.access_token = None
        self.refresh_token = None
        self.base_url = "https://mobile-iot-api.iot.traegergrills.io"
        self.graphql_url = "https://api.kube-gql.prod.traegergrills.io/"
        self.auth_url = "https://auth-api.iot.traegergrills.io"
        self.headers = {
            "authorization": auth_token if auth_token else "",
            "content-type": "application/json",
            "accept": "*/*",
            "user-agent": "Platform: iOS, OS Version: 26.0, App Version: 3.12.0, Device Model: iPhone"
        }
        self.grill_id = None
        self.grill_status = {}
    
    def login(self, email: str, password: str) -> bool:
        """
        Login with email and password using Traeger's auth API.
        
        Args:
            email: Traeger account email
            password: Traeger account password
            
        Returns:
            True if login successful, False otherwise
        """
        try:
            # Use Traeger's auth API endpoint
            headers = {
                "Content-Type": "application/json",
                "Accept": "*/*",
                "User-Agent": "Platform: iOS, OS Version: 26.0, App Version: 3.12.0, Device Model: iPhone",
                "content-language": "en"
            }
            
            payload = {
                "username": email,
                "password": password
            }
            
            response = requests.post(
                f"{self.auth_url}/tokens",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                # Extract tokens from response
                self.auth_token = result.get('idToken')  # Used for authorization
                self.access_token = result.get('accessToken')
                self.refresh_token = result.get('refreshToken')
                
                # Update headers with the idToken for API calls
                self.headers['authorization'] = self.auth_token
                return True
            else:
                print(f"Login failed: {response.status_code} - {response.text}")
                return False
            
        except Exception as e:
            print(f"Login error: {e}")
            return False
        
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
        # Command format: "11,<temp>" (per reverse-engineered Traeger iOS app)
        command = f"11,{temp_fahrenheit}"
        print(f"Setting grill temperature to {temp_fahrenheit}°F...")
        return self.send_command(command)
    
    def set_probe_alarm(self, probe_id: int, target_temp: int) -> Dict:
        """
        Set a probe temperature alarm.
        
        Args:
            probe_id: Probe number (0-3 for probes p0-p3) -- kept for API
                compatibility; the underlying Traeger firmware only exposes a
                single probe target via command 14.
            target_temp: Target temperature in Fahrenheit
            
        Returns:
            Response from the API
        """
        # Command format: "14,<temp>" (per reverse-engineered Traeger iOS app)
        command = f"14,{target_temp}"
        print(f"Setting probe alarm to {target_temp}°F (probe_id={probe_id} ignored)...")
        return self.send_command(command)
    
    def clear_probe_alarm(self, probe_id: int) -> Dict:
        """
        Clear a probe temperature alarm.
        
        Args:
            probe_id: Probe number (0-3) -- ignored; see set_probe_alarm.
            
        Returns:
            Response from the API
        """
        # Set probe alarm to 0 to clear it.
        command = "14,0"
        print(f"Clearing probe alarm (probe_id={probe_id} ignored)...")
        return self.send_command(command)
    
    def request_status(self, parse: bool = True) -> Dict:
        """
        Ask the grill to publish its current status. The actual telemetry is
        delivered asynchronously over MQTT (topic
        ``prod/thing/update/<thingName>``); this REST call only nudges the
        grill to publish a fresh update.
        
        Args:
            parse: Ignored; kept for backwards compatibility.
            
        Returns:
            Raw REST response from the command endpoint (usually ``{}``).
        """
        # Command "90" requests a state push.
        return self.send_command("90")
    
    def parse_status(self, status_response: Dict) -> Dict:
        """
        Parse status response to extract temperature and state data.
        
        The status response format needs to be determined from actual grill responses.
        This is a placeholder implementation that attempts to handle common formats.
        
        Args:
            status_response: Raw status response from the grill
            
        Returns:
            Parsed status dictionary with temperatures and state
        """
        parsed = {
            'grill_temp': None,
            'set_temp': None,
            'probe0_temp': None,
            'probe1_temp': None,
            'probe2_temp': None,
            'probe3_temp': None,
            'status': 'unknown',
            'raw': status_response
        }
        
        # Try to parse different response formats
        # TODO: Update this based on actual status response format from your grill
        
        # Common fields that might be in the response
        if isinstance(status_response, dict):
            # Check for direct temperature fields
            parsed['grill_temp'] = status_response.get('grill_temp') or status_response.get('grillTemp')
            parsed['set_temp'] = status_response.get('set_temp') or status_response.get('setTemp')
            
            # Check for probe temperatures
            for i in range(4):
                # Try various field name patterns
                probe_key = f'probe{i}_temp'
                alt_key = f'probe{i}Temp'
                parsed[probe_key] = status_response.get(probe_key) or status_response.get(alt_key)
            
            # Check for status/state field
            parsed['status'] = status_response.get('status') or status_response.get('state', 'unknown')
        
        return parsed
    
    def turn_on(self) -> Dict:
        """Turn the grill on."""
        print("Turning grill on...")
        return self.send_command("90,1")
    
    def turn_off(self) -> Dict:
        """Turn the grill off."""
        print("Turning grill off...")
        return self.send_command("90,0")
    
    def get_status_from_api(self) -> Dict:
        """
        Get current grill status from the REST API.

        The Traeger mobile API exposes a single `/users/self` endpoint that
        returns the user's grills (under the `things` key), with each grill's
        latest reported state embedded in the same payload. We pick the entry
        matching the active `grill_id`.

        Returns:
            Current grill status (the matching `things` entry), or {} if not
            found.
        """
        if not self.grill_id:
            raise ValueError("No grill ID set. Call set_grill() first.")

        response = requests.get(
            f"{self.base_url}/users/self",
            headers=self.headers
        )
        response.raise_for_status()
        data = response.json()

        for thing in data.get('things', []) or []:
            if thing.get('thingName') == self.grill_id:
                return thing

        return {}
    
    def get_mqtt_connection(self) -> Dict:
        """Get MQTT WebSocket connection details for real-time updates."""
        response = requests.post(
            f"{self.base_url}/mqtt-connections",
            headers=self.headers,
            json={}
        )
        response.raise_for_status()
        return response.json()

    def start_mqtt_listener(self, on_status_callback=None, topics=None):
        """
        Open a long-lived MQTT WebSocket connection to AWS IoT and stream
        status updates from the grill.

        Every received message is JSON-decoded (when possible) and stored on
        ``self.grill_status``. The optional ``on_status_callback(topic, payload)``
        is invoked for each message.

        Returns the underlying ``paho.mqtt.client.Client`` instance. Call
        ``client.loop_stop(); client.disconnect()`` to tear it down.
        """
        # Imported lazily so the rest of the client works without paho-mqtt.
        import paho.mqtt.client as mqtt
        from urllib.parse import urlparse

        if not self.grill_id:
            raise ValueError("No grill ID set. Call set_grill() first.")

        info = self.get_mqtt_connection()
        signed_url = info['signedUrl']
        parsed = urlparse(signed_url)
        host = parsed.hostname
        # paho's ws path must include the query string (SigV4 params).
        ws_path = parsed.path + ('?' + parsed.query if parsed.query else '')

        client_id = f"traeger-desktop-{self.grill_id}-{int(time.time())}"

        # paho-mqtt 2.x requires choosing a callback API version.
        if hasattr(mqtt, 'CallbackAPIVersion'):
            mqttc = mqtt.Client(
                client_id=client_id,
                transport='websockets',
                callback_api_version=mqtt.CallbackAPIVersion.VERSION1,
            )
        else:  # paho-mqtt 1.x fallback
            mqttc = mqtt.Client(client_id=client_id, transport='websockets')

        mqttc.ws_set_options(path=ws_path)
        mqttc.tls_set()

        if topics is None:
            # Traeger publishes the grill's full status payload to
            # ``prod/thing/update/<thingName>`` (this is the topic the iOS
            # app subscribes to). The AWS IoT policy on the JWT only allows
            # subscribing to this specific topic -- other variants are
            # rejected and trigger an immediate broker-side disconnect.
            topics = [f"prod/thing/update/{self.grill_id}"]

        def _on_connect(client, userdata, flags, rc):
            if rc == 0:
                print(f"[MQTT] connected to {host}, subscribing to {topics}")
                for t in topics:
                    client.subscribe(t, qos=0)
            else:
                print(f"[MQTT] connect failed rc={rc}")

        def _on_disconnect(client, userdata, rc):
            print(f"[MQTT] disconnected rc={rc}")

        def _on_message(client, userdata, msg):
            try:
                payload = json.loads(msg.payload.decode('utf-8'))
            except Exception:
                payload = {'_raw': msg.payload[:500].decode('utf-8', errors='replace')}
            payload['_topic'] = msg.topic
            self.grill_status = payload
            if on_status_callback:
                try:
                    on_status_callback(msg.topic, payload)
                except Exception as cb_err:
                    print(f"[MQTT] callback error: {cb_err}")

        mqttc.on_connect = _on_connect
        mqttc.on_disconnect = _on_disconnect
        mqttc.on_message = _on_message

        mqttc.connect(host, 443, keepalive=60)
        mqttc.loop_start()
        return mqttc
    
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
