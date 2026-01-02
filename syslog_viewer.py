#!/usr/bin/env python3
"""
Simple Syslog Receiver with Web Interface
Receives syslog messages on UDP/TCP port 514 and displays them via a web interface
Includes automatic log rotation based on file size
"""

import socketserver
import threading
from datetime import datetime
from collections import deque
from flask import Flask, render_template, jsonify
import argparse
import json
import os
from pathlib import Path
import logging
import gzip
import shutil
import time

# Store logs in memory (keep last 1000 entries)
log_buffer = deque(maxlen=1000)

# Log file path
LOG_DIR = Path('/app/logs')
LOG_FILE = LOG_DIR / 'syslog.jsonl'

# Log rotation settings
MAX_LOG_SIZE = 100 * 1024 * 1024  # 100MB per file
MAX_LOG_FILES = 10  # Keep 10 rotated files
ROTATION_CHECK_INTERVAL = 60  # Check every 60 seconds

# Thread-safe file writing
file_lock = threading.Lock()

def ensure_log_directory():
    """Create log directory if it doesn't exist"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Log directory: {LOG_DIR}")


def rotate_logs():
    """Rotate log files, compress old ones"""
    try:
        if not LOG_FILE.exists():
            return

        file_size = LOG_FILE.stat().st_size

        # Only rotate if file exceeds max size
        if file_size < MAX_LOG_SIZE:
            return

        with file_lock:
            print(f"Rotating log file (size: {file_size / 1024 / 1024:.2f}MB)")

            # Delete oldest log file if we're at the limit
            oldest_file = LOG_DIR / f'syslog.jsonl.{MAX_LOG_FILES}.gz'
            if oldest_file.exists():
                oldest_file.unlink()
                print(f"Deleted oldest log file: {oldest_file.name}")

            # Rotate existing files
            for i in range(MAX_LOG_FILES - 1, 0, -1):
                old_file = LOG_DIR / f'syslog.jsonl.{i}.gz'
                new_file = LOG_DIR / f'syslog.jsonl.{i + 1}.gz'
                if old_file.exists():
                    old_file.rename(new_file)

            # Compress and rotate current log file
            rotated_file = LOG_DIR / 'syslog.jsonl.1'
            compressed_file = LOG_DIR / 'syslog.jsonl.1.gz'

            # Move current file to .1
            shutil.move(str(LOG_FILE), str(rotated_file))

            # Compress the rotated file
            with open(rotated_file, 'rb') as f_in:
                with gzip.open(compressed_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

            # Remove uncompressed rotated file
            rotated_file.unlink()

            print(f"Log rotation complete. Created {compressed_file.name}")

    except Exception as e:
        print(f"Error during log rotation: {e}")


def rotation_monitor():
    """Background thread to monitor and rotate logs"""
    while True:
        try:
            time.sleep(ROTATION_CHECK_INTERVAL)
            rotate_logs()
        except Exception as e:
            print(f"Error in rotation monitor: {e}")


def save_log_to_file(log_entry):
    """Append log entry to file in JSON Lines format"""
    try:
        with file_lock:
            with open(LOG_FILE, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
    except Exception as e:
        print(f"Error writing to log file: {e}")

def load_logs_from_file():
    """Load existing logs from file on startup"""
    if not LOG_FILE.exists():
        return

    try:
        with open(LOG_FILE, 'r') as f:
            for line in f:
                try:
                    log_entry = json.loads(line.strip())
                    log_buffer.append(log_entry)
                except json.JSONDecodeError:
                    continue
        print(f"Loaded {len(log_buffer)} log entries from file")
    except Exception as e:
        print(f"Error loading logs from file: {e}")

class SyslogUDPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = bytes.decode(self.request[0].strip(), errors='ignore')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        client_ip = self.client_address[0]

        log_entry = {
            'timestamp': timestamp,
            'source': client_ip,
            'message': data
        }
        log_buffer.append(log_entry)
        save_log_to_file(log_entry)
        print(f"[{timestamp}] {client_ip}: {data}")

class SyslogTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = self.request.recv(4096).strip()
        data = bytes.decode(data, errors='ignore')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        client_ip = self.client_address[0]

        log_entry = {
            'timestamp': timestamp,
            'source': client_ip,
            'message': data
        }
        log_buffer.append(log_entry)
        save_log_to_file(log_entry)
        print(f"[{timestamp}] {client_ip}: {data}")

# Flask web interface
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/logs')
def get_logs():
    return jsonify(list(log_buffer))

def start_syslog_servers(udp_port=514, tcp_port=514, host='0.0.0.0'):
    # Start log rotation monitor
    rotation_thread = threading.Thread(target=rotation_monitor)
    rotation_thread.daemon = True
    rotation_thread.start()
    print(f"Log rotation monitor started (max size: {MAX_LOG_SIZE / 1024 / 1024}MB, max files: {MAX_LOG_FILES})")

    # Start UDP server
    udp_server = socketserver.UDPServer((host, udp_port), SyslogUDPHandler)
    udp_thread = threading.Thread(target=udp_server.serve_forever)
    udp_thread.daemon = True
    udp_thread.start()
    print(f"Syslog UDP server listening on {host}:{udp_port}")

    # Start TCP server
    tcp_server = socketserver.TCPServer((host, tcp_port), SyslogTCPHandler)
    tcp_thread = threading.Thread(target=tcp_server.serve_forever)
    tcp_thread.daemon = True
    tcp_thread.start()
    print(f"Syslog TCP server listening on {host}:{tcp_port}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Simple Syslog Receiver with Web Interface and Log Rotation')
    parser.add_argument('--syslog-port', type=int, default=514, help='Syslog port (UDP and TCP, default: 514)')
    parser.add_argument('--web-port', type=int, default=8080, help='Web interface port (default: 8080)')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--max-size', type=int, default=100, help='Max log file size in MB before rotation (default: 100)')
    parser.add_argument('--max-files', type=int, default=10, help='Max number of rotated log files to keep (default: 10)')
    args = parser.parse_args()

    # Update rotation settings from arguments
    MAX_LOG_SIZE = args.max_size * 1024 * 1024
    MAX_LOG_FILES = args.max_files

    # Disable Flask's default request logging and warnings
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    # Suppress Flask development server warning
    from flask import cli as flask_cli
    flask_cli.show_server_banner = lambda *args: None

    # Ensure log directory exists
    ensure_log_directory()

    # Load existing logs from file
    load_logs_from_file()

    print("=" * 60)
    print("Syslog Receiver with Web Interface")
    print("=" * 60)
    print(f"Log rotation: {args.max_size}MB per file, keep {args.max_files} files")

    # Start syslog servers
    start_syslog_servers(udp_port=args.syslog_port, tcp_port=args.syslog_port, host=args.host)

    # Start web interface
    print(f"Web interface starting on http://{args.host}:{args.web_port}")
    app.run(host=args.host, port=args.web_port, debug=False)
