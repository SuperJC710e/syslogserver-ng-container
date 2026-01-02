# Simple Syslog Viewer

A lightweight syslog receiver with a clean web interface for viewing logs in real-time.

## Features

- ✅ Receives syslog messages via UDP and TCP on port 514
- ✅ Modern, dark-themed web interface
- ✅ Real-time log updates (refreshes every 2 seconds)
- ✅ Filter logs by text
- ✅ Auto-scroll toggle
- ✅ Persistent log storage to disk (survives container restarts)
- ✅ Stores last 1000 log entries in memory for fast access
- ✅ Shows source IP and timestamp for each log
- ✅ Lightweight and simple to deploy
- ✅ Pre-built container images available on GitHub Container Registry
- ✅ Automated builds via GitHub Actions

## Quick Start

### Using Docker Compose (Recommended)

The easiest way to get started is using the pre-built image from GitHub Container Registry:

```bash
docker compose pull
docker compose up -d
```

Then access the web interface at: `http://localhost:8080`

Logs are persisted in the `./logs` directory on your host machine.

### Using Pre-built Container Image

```bash
# Pull the latest image
docker pull ghcr.io/superjc710e/syslogserver-ng-container:latest

# Run the container with persistent logs
docker run -d \
  -p 514:514/udp \
  -p 514:514/tcp \
  -p 8080:8080 \
  -v ./logs:/app/logs \
  --name syslog-viewer \
  ghcr.io/superjc710e/syslogserver-ng-container:latest
```

### Building Locally

If you want to build the image yourself:

```bash
# Build the image
docker build -t syslog-viewer .

# Run the container
docker run -d \
  -p 514:514/udp \
  -p 514:514/tcp \
  -p 8080:8080 \
  -v ./logs:/app/logs \
  --name syslog-viewer \
  syslog-viewer
```

### Running Directly with Python

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application (requires root for port 514)
sudo python syslog_viewer.py
```

Or run on non-privileged ports:

```bash
python syslog_viewer.py --syslog-port 5140 --web-port 8080
```

## Configuration

Command-line options:

- `--syslog-port`: Port for syslog (UDP and TCP, default: 514)
- `--web-port`: Port for web interface (default: 8080)
- `--host`: Host to bind to (default: 0.0.0.0)

Example:
```bash
python syslog_viewer.py --syslog-port 5140 --web-port 8888 --host 127.0.0.1
```

## Testing

Send a test syslog message:

```bash
# Using logger command
logger -n localhost -P 514 "Test syslog message"

# Using netcat
echo "Test message from netcat" | nc -u localhost 514

# Using Python
python -c "import socket; s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.sendto(b'Test from Python', ('localhost', 514))"
```

## Port 514 Note

Port 514 is a privileged port (< 1024), so you need:
- Run as root/sudo, OR
- Use a different port (e.g., 5140), OR
- Use Docker (which handles port binding)

## Web Interface Features

- **Filter**: Type to filter logs by any text (timestamp, source, or message)
- **Auto-scroll**: Toggle automatic scrolling to newest logs
- **Clear Display**: Clear the display (logs still being received)
- **Refresh**: Manual refresh of log display
- **Statistics**: Shows total logs, filtered logs, and last update time

## Persistent Storage

Logs are automatically saved to `/app/logs/syslog.jsonl` inside the container in JSON Lines format. When using the provided docker-compose configuration, this maps to `./logs` on your host machine.

**Features:**

- All received syslog messages are immediately written to disk
- Logs persist across container restarts
- On startup, the last 1000 log entries are loaded into memory
- Log file grows indefinitely (consider implementing log rotation for production use)

**Log File Location:**

- **In container:** `/app/logs/syslog.jsonl`
- **On host (with docker-compose):** `./logs/syslog.jsonl`

## Container Registry

Pre-built images are automatically published to GitHub Container Registry on every commit to the main branch:

```text
ghcr.io/superjc710e/syslogserver-ng-container:latest
ghcr.io/superjc710e/syslogserver-ng-container:main
```

The GitHub Actions workflow builds multi-platform images (amd64 and arm64).

## Architecture

- **Backend**: Python with Flask web framework
- **Syslog**: UDP and TCP servers using Python's socketserver
- **Storage**: Persistent JSON Lines file + in-memory deque (last 1000 entries)
- **Frontend**: Vanilla JavaScript with auto-refresh
- **Container**: Multi-platform (amd64/arm64) Docker images

## License

MIT License - feel free to use and modify as needed!
