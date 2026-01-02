FROM python:3.11-slim

# Environment variables
ENV PIP_BREAK_SYSTEM_PACKAGES=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_NO_WARN_SCRIPT_LOCATION=1 \
    PIP_PROGRESS_BAR=off \
    PIP_ROOT_USER_ACTION=ignore

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application files
COPY syslog_viewer.py .
COPY templates/ templates/

# Expose ports
# 514 for syslog (UDP and TCP)
# 8080 for web interface
EXPOSE 514/udp 514/tcp 8080

# Run as non-root user for security
RUN useradd -m -u 1000 syslog && chown -R syslog:syslog /app
USER syslog

# Start the application
CMD ["python", "syslog_viewer.py"]
