# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-01-02

### Added
- **Automatic log rotation** with configurable size limits
  - Default: 100MB per file
  - Default retention: 10 rotated files
  - Automatic gzip compression of rotated files
  - Thread-safe file operations
  - Background rotation monitor (checks every 60 seconds)
- **Production-ready WSGI server** (Waitress)
  - Replaced Flask development server with Waitress
  - Multi-threaded request handling (4 threads)
  - Better performance and reliability for production use
- New command-line arguments:
  - `--max-size`: Configure rotation file size in MB
  - `--max-files`: Configure number of rotated files to keep

### Changed
- Web server now uses Waitress instead of Flask's built-in development server
- Enhanced startup logging to show rotation settings
- Updated requirements.txt to include Waitress

### Technical Details

**Log Rotation Process:**
1. Checks file size every 60 seconds
2. When file exceeds max size (default 100MB):
   - Rotates existing files (`.1.gz` → `.2.gz`, etc.)
   - Moves current file to `.1`
   - Compresses to `.1.gz` using gzip
   - Deletes oldest file if retention limit reached
   - Creates new empty log file
3. All operations are thread-safe using file locks

**Production Server (Waitress):**
- Pure Python WSGI server
- Multi-threaded (4 worker threads)
- Production-ready and stable
- Cross-platform compatible
- No development server warnings

### Migration Notes

Existing deployments will continue to work without changes. The new features use sensible defaults:
- Log rotation: 100MB files, keep 10 rotations
- Web server: Waitress with 4 threads

To customize log rotation, add command arguments:
```bash
python syslog_viewer.py --max-size 50 --max-files 5
```

Or in docker-compose.yml:
```yaml
command: ["python", "syslog_viewer.py", "--max-size", "50", "--max-files", "5"]
```
