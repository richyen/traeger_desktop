# Traeger Grill Controller

Control your Traeger WiFIRE-enabled grill from your laptop using Python. This was reverse-engineered from the Traeger iOS/Android app API calls.

## Features

- ✅ Read current grill temperature
- ✅ Set grill temperature
- ✅ Set probe temperature alarms
- ✅ Clear probe alarms
- ✅ Turn grill on/off
- ✅ Track cook sessions with metadata
- 🔄 Real-time status updates via MQTT (partially implemented)

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/yourusername/traeger-controller.git
cd traeger-controller
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Capture Your Authentication Token

You'll need to use mitmproxy to capture your authentication token from the Traeger app. See **[SETUP.md](SETUP.md)** for detailed instructions.

**Quick version:**
1. Install and run mitmproxy on your computer
2. Configure your phone to proxy through your computer
3. Install mitmproxy's certificate on your phone
4. Use the Traeger app while capturing traffic
5. Save the flows to `flows/traeger_mitmproxy.flows`
6. Run: `python extract_token.py`

This creates `traeger_config.json` with your token and grill ID.

**Note**: The `flows/` directory is excluded from git for privacy.

### 3. Start Controlling Your Grill!

```bash
# Check grill status
python traeger_cli.py status

# Set temperature to 225°F
python traeger_cli.py temp 225

# Set probe 0 alarm to 165°F
python traeger_cli.py probe 0 165
```

**Note**: Auth tokens expire after about 1 hour. See [SETUP.md](SETUP.md) for how to capture new tokens.

## Usage

### Command Line Interface

The `traeger_cli.py` script provides an easy-to-use command-line interface:

#### Get Grill Status
```bash
python traeger_cli.py status
```

#### Set Grill Temperature
```bash
# Set to 225°F (great for smoking)
python traeger_cli.py temp 225

# Set to 375°F (for roasting)
python traeger_cli.py temp 375
```

#### Set Probe Alarm
```bash
# Set probe 0 alarm to 165°F (chicken safe temp)
python traeger_cli.py probe 0 165

# Set probe 1 alarm to 203°F (perfect brisket)
python traeger_cli.py probe 1 203
```

#### Clear Probe Alarm
```bash
python traeger_cli.py probe 0 --clear
```

#### Power Control
```bash
# Turn grill on
python traeger_cli.py power on

# Turn grill off (will run shutdown cycle)
python traeger_cli.py power off
```

#### Start Cook Session with Metadata
```bash
# Chicken breast cook
python traeger_cli.py cook start --protein chicken --cut breast --probe 0 --temp 165

# Beef brisket cook
python traeger_cli.py cook start --protein beef --cut brisket --probe 0 --temp 203

# Pork ribs cook
python traeger_cli.py cook start --protein pork --cut ribs --probe 0 --temp 195
```

### Python Library

You can also use `traeger_client.py` as a library in your own scripts:

```python
from traeger_client import TraegerClient
import json

# Load config
with open('traeger_config.json', 'r') as f:
    config = json.load(f)

# Initialize client
client = TraegerClient(config['auth_token'])
client.set_grill(config['grill_id'])

# Set temperature
client.set_temperature(225)

# Set probe alarm
client.set_probe_alarm(probe_id=0, target_temp=165)

# Get status
status = client.request_status()
print(status)
```

## API Commands Discovered

From analyzing your mitmproxy flows, here are the commands:

| Command | Format | Description |
|---------|--------|-------------|
| Set Temperature | `112,<temp>` | Set grill temperature in °F |
| Set Probe Alarm | `120,10,p<id>,<temp>` | Set probe alarm (id: 0-3) |
| Request Status | `113` | Request current grill status |
| Power On | `90,1` | Turn grill on |
| Power Off | `90,0` | Turn grill off |

## Files

- `traeger_client.py` - Main Python client library
- `traeger_cli.py` - Command-line interface
- `extract_token.py` - Extract auth token from mitmproxy flows
- `parse_flows.py` - Parse and analyze mitmproxy flows
- `traeger_config.json` - Configuration file (created by extract_token.py)
- `traeger_api_calls.json` - Detailed API call analysis

## API Endpoints

Based on your flows:

### REST API
- **Base URL**: `https://mobile-iot-api.iot.traegergrills.io`
- **GraphQL**: `https://api.kube-gql.prod.traegergrills.io/`

### Key Endpoints
- `GET /users/self` - Get user profile and grills
- `POST /things/{grill_id}/commands` - Send commands to grill
- `POST /mqtt-connections` - Get MQTT WebSocket connection for real-time updates
- `PUT /users/self/firebase-tokens` - Update push notification tokens

## Documentation

- **[SETUP.md](SETUP.md)** - Detailed mitmproxy setup and token capture guide
- **[QUICKSTART.md](QUICKSTART.md)** - Command reference and usage examples
- **[AUTHENTICATION_ANALYSIS.md](AUTHENTICATION_ANALYSIS.md)** - Technical deep-dive on how authentication works

## Next Steps / TODO

Here are ideas for expanding this into a full-featured app:

### Short Term
- [ ] Parse grill status responses to show current temp, probe temps, etc.
- [ ] Add real-time MQTT connection for live temperature monitoring
- [ ] Create a simple web dashboard (Flask/FastAPI)
- [ ] Add temperature history logging and graphing

### Medium Term
- [ ] Implement OAuth flow to get tokens without mitmproxy
- [ ] Support multiple grills
- [ ] Add cook presets (e.g., "smoke chicken", "sear steak")
- [ ] Temperature alerts via email/SMS
- [ ] Cook timer functionality

### Long Term
- [ ] Build a full desktop GUI (PyQt/tkinter)
- [ ] Mobile-friendly web interface
- [ ] Integration with recipe databases
- [ ] Automated cooking programs (e.g., "reverse sear")
- [ ] Home Assistant integration
- [ ] Alexa/Google Home voice control

## Understanding the Traeger API

The Traeger app uses:
1. **AWS Cognito** for authentication (JWT tokens)
2. **REST API** for commands and configuration
3. **GraphQL** for complex queries (recipes, user data, cook metadata)
4. **MQTT over WebSocket** for real-time grill status updates
5. **AWS IoT** for device-to-cloud communication

## Safety Notes

⚠️ **Important Safety Reminders**:
- Never leave your grill unattended, even with remote monitoring
- Ensure proper ventilation when using your grill
- Keep flammable materials away from the grill
- Follow all manufacturer safety guidelines
- This tool is for convenience, not a replacement for proper supervision

## Troubleshooting

### "Authentication failed" error
Your token expired. Run `python extract_token.py` to get a fresh token.

### "No grill ID set" error
Make sure `traeger_config.json` exists and contains your grill ID.

### Can't connect to grill
- Ensure your grill is powered on and connected to WiFi
- Check that the Traeger app can connect to your grill
- Verify your auth token is valid

### Commands don't seem to work
Some commands may take a few seconds to execute on the grill. Try requesting status after 5-10 seconds.

## Contributing

Contributions are welcome! This project was reverse-engineered from the Traeger mobile app. As you discover more API endpoints and commands, please contribute them back.

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Disclaimer

This is an unofficial client for Traeger grills, created through reverse engineering. It is not affiliated with, endorsed by, or supported by Traeger Grills or Traeger Pellet Grills, LLC. Use at your own risk.

## License

MIT License - Feel free to modify and extend this for your own use!
