# Traeger Grill Controller - Quick Reference

## Getting Started (First Time)

1. **Extract auth token from your flows:**
   ```bash
   python extract_token.py
   ```

2. **Check what commands are available:**
   ```bash
   python traeger_cli.py --help
   ```

## Common Commands

### Check Grill Status
```bash
python traeger_cli.py status
```

### Set Grill Temperature
```bash
# Low and slow smoking
python traeger_cli.py temp 225

# Medium heat
python traeger_cli.py temp 350

# High heat searing
python traeger_cli.py temp 450
```

### Set Probe Alarms

**Chicken (165°F internal):**
```bash
python traeger_cli.py probe 0 165
```

**Pork Shoulder/Ribs (195-203°F):**
```bash
python traeger_cli.py probe 0 203
```

**Beef Brisket (200-205°F):**
```bash
python traeger_cli.py probe 0 203
```

**Steak (Medium-rare 135°F):**
```bash
python traeger_cli.py probe 0 135
```

### Start a Cook Session

**Chicken Breast:**
```bash
python traeger_cli.py cook start --protein chicken --cut breast --probe 0 --temp 165
```

**Beef Brisket:**
```bash
python traeger_cli.py cook start --protein beef --cut brisket --probe 0 --temp 203
```

**Pork Ribs:**
```bash
python traeger_cli.py cook start --protein pork --cut ribs --probe 0 --temp 195
```

### Clear Probe Alarm
```bash
python traeger_cli.py probe 0 --clear
```

## Temperature Reference

### Poultry
- Chicken breast: 165°F
- Chicken thighs: 175°F
- Turkey: 165°F

### Beef
- Rare: 125°F
- Medium-rare: 135°F
- Medium: 145°F
- Medium-well: 150°F
- Well done: 160°F
- Brisket (pull): 203°F

### Pork
- Pork chops: 145°F
- Pulled pork: 195-203°F
- Ribs: 195°F
- Pork tenderloin: 145°F

### Fish
- Salmon: 145°F
- Tuna (medium-rare): 125°F

## Grill Temperature Guidelines

### Smoking (180-225°F)
- Brisket
- Pork shoulder
- Ribs

### Roasting (325-375°F)
- Whole chicken
- Turkey
- Roasts

### Searing (450-500°F)
- Steaks
- Burgers
- Quick-cooking vegetables

## When Auth Token Expires

Auth tokens typically last 1 hour. When expired:

1. Open Traeger app on your iPhone
2. Make sure mitmproxy is running and capturing traffic
3. Navigate around the app (check grill status, adjust temp, etc.)
4. Save the flows
5. Run `python extract_token.py` again

## Python Library Example

```python
from traeger_client import TraegerClient
import json

# Load config
with open('traeger_config.json') as f:
    config = json.load(f)

# Initialize
client = TraegerClient(config['auth_token'])
client.set_grill(config['grill_id'])

# Set temp and probe
client.set_temperature(225)
client.set_probe_alarm(0, 165)

# Start cook tracking
import time
cook_id = f"{config['grill_id']}{int(time.time())}"
client.upsert_cook_metadata(
    cook_id=cook_id,
    protein="chicken",
    cut="breast",
    probe_id="p0",
    target_temp=165
)
```

## Troubleshooting

### "401 Unauthorized" error
Your auth token expired. Run `python extract_token.py` to get a fresh one.

### "No grill ID set" error
Make sure `traeger_config.json` exists with your grill ID.

### Commands not executing
- Check that your grill is powered on
- Verify WiFi connection on grill
- Wait 5-10 seconds and request status
- Token may have expired

### Can't find mitmproxy flows
Make sure `traeger_mitmproxy.flows` is in the current directory.

## Files Overview

- `traeger_client.py` - Python library for Traeger API
- `traeger_cli.py` - Command-line interface tool
- `extract_token.py` - Extract auth token from flows
- `parse_flows.py` - Analyze mitmproxy flows
- `example.py` - Example usage script
- `traeger_config.json` - Your grill configuration
- `README.md` - Full documentation
- `QUICKSTART.md` - This file

## Safety Reminders

- Never leave grill unattended
- Keep area clear of flammable materials
- Ensure proper ventilation
- This is a convenience tool, not a replacement for supervision
- Follow all manufacturer safety guidelines

## Next Steps

Build this into a full app by adding:
- Web dashboard with live temperature graphs
- Email/SMS alerts when food is done
- Recipe database integration
- Automated cooking programs
- Home Assistant integration
- Mobile-friendly interface
