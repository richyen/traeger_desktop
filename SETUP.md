# Setup Guide

This guide walks you through setting up mitmproxy to capture your Traeger authentication token.

## Prerequisites

- A Traeger WiFIRE-enabled grill
- The Traeger mobile app installed on your phone (iOS or Android)
- A laptop/computer on the same network as your phone
- Python 3.8 or higher

## Step 1: Install mitmproxy

### On macOS (using Homebrew):
```bash
brew install mitmproxy
```

### On Linux (using pip):
```bash
pip install mitmproxy
```

### On Windows:
Download the installer from https://mitmproxy.org/

## Step 2: Start mitmproxy

```bash
# For command-line interface:
mitmproxy

# Or for web interface (easier for beginners):
mitmweb
```

mitmproxy will start on port 8080 by default.

## Step 3: Configure Your Phone to Use the Proxy

### Find Your Computer's IP Address

**On macOS:**
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

**On Linux:**
```bash
ip addr show | grep "inet " | grep -v 127.0.0.1
```

**On Windows:**
```bash
ipconfig
```

Look for your local IP address (usually starts with 192.168.x.x or 10.0.x.x).

### Configure Proxy on Your Phone

#### iOS:
1. Go to **Settings** → **Wi-Fi**
2. Tap the (i) icon next to your connected network
3. Scroll down to **HTTP Proxy**
4. Select **Manual**
5. Enter:
   - **Server**: Your computer's IP address (e.g., 192.168.1.100)
   - **Port**: 8080
6. Tap **Save**

#### Android:
1. Go to **Settings** → **Wi-Fi**
2. Long-press your connected network
3. Select **Modify network**
4. Show **Advanced options**
5. Set **Proxy** to **Manual**
6. Enter:
   - **Proxy hostname**: Your computer's IP address
   - **Proxy port**: 8080
7. Tap **Save**

## Step 4: Install mitmproxy Certificate on Your Phone

This is required to decrypt HTTPS traffic.

1. **With your phone still proxied**, open Safari (iOS) or Chrome (Android)
2. Navigate to: `http://mitm.it`
3. Tap the icon for your device (Apple or Android)
4. Follow the instructions to install the certificate

### iOS Additional Steps:
1. Go to **Settings** → **General** → **VPN & Device Management**
2. Find the **mitmproxy** certificate
3. Tap **Install** (you may need to enter your passcode)
4. Go to **Settings** → **General** → **About** → **Certificate Trust Settings**
5. Enable full trust for the **mitmproxy** certificate

### Android Additional Steps:
1. The certificate should install automatically
2. If prompted, set a screen lock (PIN/pattern/password) if you haven't already

## Step 5: Capture Traeger API Traffic

1. **Make sure mitmproxy is running** on your computer
2. **Open the Traeger app** on your phone
3. **Use the app normally**: 
   - Check your grill status
   - Change temperature
   - Set probe alarms
   - Navigate through different screens

As you use the app, you'll see HTTP requests appearing in mitmproxy.

## Step 6: Save the Captured Flows

### If using mitmproxy CLI:
1. Press `w` to save
2. Enter filename: `traeger_mitmproxy.flows`
3. Press Enter

### If using mitmweb:
1. Click the **File** menu
2. Select **Save**
3. Save as: `traeger_mitmproxy.flows`

## Step 7: Copy Flows File to Project Directory

Move the saved `traeger_mitmproxy.flows` file to your project's `flows/` directory:

```bash
mv ~/Downloads/traeger_mitmproxy.flows /path/to/traeger-controller/flows/
```

**Note**: The `flows/` directory is excluded from git to protect your privacy. Flow files contain your authentication tokens and personal information.

## Step 8: Remove Proxy Configuration from Your Phone

**Important**: Don't forget to turn off the proxy when you're done!

### iOS:
1. **Settings** → **Wi-Fi** → (i) → **HTTP Proxy**
2. Select **Off**

### Android:
1. **Settings** → **Wi-Fi** → Long-press network → **Modify network**
2. Set **Proxy** to **None**

## Step 9: Extract Authentication Token

Now run the extraction script:

```bash
cd /path/to/traeger-controller
python extract_token.py
```

This will create a `traeger_config.json` file with your authentication token and grill ID.

## Step 10: Test the Setup

Try getting your grill status:

```bash
python traeger_cli.py status
```

If you see grill information, you're all set! 🎉

## Troubleshooting

### "No token found" error
- Make sure you used the Traeger app while mitmproxy was capturing
- The app needs to make authenticated API calls for the token to appear
- Try opening different screens in the app (Home, Cook History, Settings)

### "Certificate verification failed" errors in mitmproxy
- Ensure you installed the mitmproxy certificate on your phone
- On iOS, make sure you enabled "Full Trust" for the certificate
- Try restarting your phone after installing the certificate

### "Connection refused" when using the app
- Verify your computer's IP address is correct
- Make sure mitmproxy is running
- Check that your phone and computer are on the same network
- Try disabling any firewall on your computer temporarily

### Token expires immediately
- The token has a 1-hour lifetime
- Make sure to save the flows soon after capturing them
- If the token is already expired, capture fresh flows

### Can't see Traeger API calls in mitmproxy
- Make sure you're actually using the Traeger app while capturing
- Some calls may be to other domains (Firebase, AWS) - that's normal
- Filter by "traeger" in mitmproxy to see only relevant calls

## Security Notes

- **Never commit `traeger_config.json` to a public repository** - it contains your personal authentication token
- **Remove the proxy configuration** from your phone when you're done
- **Uninstall the mitmproxy certificate** from your phone if you're not going to use this regularly
- **Be aware** that mitmproxy can intercept ALL HTTPS traffic while the proxy is enabled

## Next Steps

Once you have your token extracted, check out:
- [QUICKSTART.md](QUICKSTART.md) - Quick command reference
- [README.md](README.md) - Full documentation
- [AUTHENTICATION_ANALYSIS.md](AUTHENTICATION_ANALYSIS.md) - Technical details on how authentication works
