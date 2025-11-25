# 🔥 Traeger Desktop - Temperature Monitoring Dashboard

A web-based temperature monitoring dashboard for Traeger WiFIRE grills with historical data tracking. The one feature the official app is missing!

## Features

- 📊 **Real-time temperature monitoring** - Live graphs of grill and probe temps
- 📈 **Historical data** - Track all your cooks over time (RecTeq-style!)
- 🎨 **Beautiful web dashboard** - Clean, responsive interface
- 🐳 **Docker-based** - Simple `docker-compose up` and you're running
- 💾 **Persistent storage** - All cook data saved to SQLite database
- 🔐 **Auto-login** - Store credentials in `.env` file

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/richyen/traeger_desktop.git
cd traeger_desktop
```

### 2. Configure Authentication

Copy the example environment file:

```bash
cp .env.example .env
```

**Option A: Email/Password (Recommended)**

Edit `.env` with your Traeger account credentials:

```bash
TRAEGER_EMAIL=your.email@example.com
TRAEGER_PASSWORD=your_password
```

**Option B: Token (Advanced)**

If you have an auth token from `traeger_config.json`:

```bash
TRAEGER_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 3. Start the Dashboard

```bash
docker-compose up -d
```

That's it! Open your browser to:

**http://localhost:5000**

## Usage

### Start Monitoring
```bash
docker-compose up -d
```

### View Logs
```bash
docker-compose logs -f
```

### Stop Monitoring
```bash
docker-compose down
```

### Reset All Data (Fresh Start)
```bash
docker-compose down -v
```

## How It Works

1. **Automatic Login** - Uses credentials from `.env` to authenticate with Traeger
2. **Continuous Monitoring** - Polls your grill every 30 seconds
3. **Data Storage** - Saves all readings to SQLite database in Docker volume
4. **Web Dashboard** - Flask app serves real-time and historical data
5. **Auto-Restart** - If connection drops, automatically reconnects

## Web Interface

The dashboard shows:
- **Current temperatures** - Real-time grill and probe temps
- **Live graph** - Last 2 hours of data, auto-updating
- **Historical view** - All past cooks with date filters
- **Cook statistics** - Duration, min/max/avg temps per cook session

## Troubleshooting

### "Authentication failed"
- Check your email/password in `.env`
- Ensure you can log into the Traeger app

### "No grill found"
- Verify your grill is powered on
- Check WiFi connection on the grill

### Dashboard not loading
```bash
docker-compose logs app
```

## Backup Your Data

```bash
docker cp traeger-monitor:/app/data/traeger.db ./backup_$(date +%Y%m%d).db
```

## License

MIT License

---

**Enjoy your enhanced Traeger experience!** 🔥🥩
