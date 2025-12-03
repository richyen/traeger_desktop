# 🔥 Traeger Desktop - Temperature Monitoring Dashboard

A web-based temperature monitoring dashboard for Traeger WiFIRE grills with historical data tracking. The one feature the official app is missing!

## Features

- 📊 **Real-time temperature monitoring** - Live graphs of grill and probe temps
- 📈 **Historical data** - Track all your cooks over time (RecTeq-style!)
- 🎨 **Beautiful web dashboard** - Clean, responsive interface
- 🐳 **Docker-based** - Simple `docker-compose up` and you're running
- 💾 **Persistent storage** - All cook data saved to SQLite database
- 🔐 **Simple auth** - Just provide your Traeger email and password

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/richyen/traeger_desktop.git
cd traeger_desktop

# 2. Create config file
cp .env.example .env

# 3. Edit .env with your Traeger email and password
nano .env

# 4. Start it up!
docker compose up -d
```

**Dashboard URL**: http://localhost:5005

That's it! The app will automatically authenticate and start monitoring your grill.


## Configuration

Edit `.env` to customize settings:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TRAEGER_EMAIL` | ✅ Yes | - | Your Traeger account email |
| `TRAEGER_PASSWORD` | ✅ Yes | - | Your Traeger account password |
| `DB_PATH` | No | `/app/data/traeger.db` | Database location |
| `POLL_INTERVAL` | No | `30` | Seconds between temperature polls |

## Common Commands

```bash
# View logs
docker compose logs -f monitor   # Temperature monitoring
docker compose logs -f app       # Web dashboard

# Stop and restart
docker compose down
docker compose up -d

# Complete cleanup (removes database too!)
docker compose down -v
```

## How It Works

The application automatically handles authentication using Traeger's official API:

1. **Login**: Authenticates with Traeger's auth API using your credentials
2. **Token Management**: Automatically obtains and manages JWT tokens
3. **Monitoring**: Polls your grill every 30 seconds
4. **Storage**: Saves all temperature readings to SQLite database
5. **Dashboard**: Flask web app displays real-time and historical data

No manual token extraction needed - just provide your email and password!

## Troubleshooting

### Authentication Failed
- Verify your email and password in `.env` are correct
- Test that you can log into the Traeger mobile app
- Check logs: `docker compose logs monitor`

### No Grills Found
- Make sure your grill is registered in the Traeger app
- Verify your grill is connected to WiFi
- Check that it appears in the mobile app

### Dashboard Not Loading
- Check services are running: `docker compose ps`
- Try http://localhost:5005 or http://127.0.0.1:5005
- View logs: `docker compose logs app`

## Backup Your Data

```bash
docker cp traeger-monitor:/app/data/traeger.db ./backup_$(date +%Y%m%d).db
```

## License

MIT License

---

**Enjoy your enhanced Traeger experience!** 🔥🥩
