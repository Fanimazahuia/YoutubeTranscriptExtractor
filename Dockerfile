# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Install system dependencies including Tor
RUN apt-get update && apt-get install -y \
    tor \
    curl \
    sudo \
    net-tools \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /var/run/tor \
    && chown -R debian-tor:debian-tor /var/run/tor

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

# Verify installation and debug
RUN python3 -c "from youtube_transcript_api import YouTubeTranscriptApi; print('YouTube API imported successfully')" && \
    python3 -c "print('Available methods:', [m for m in dir(__import__('youtube_transcript_api').YouTubeTranscriptApi) if not m.startswith('_')])"

# Copy application code
COPY . .

# Create Tor configuration
RUN echo "SocksPort 9050" > /etc/tor/torrc && \
    echo "ControlPort 9051" >> /etc/tor/torrc && \
    echo "DataDirectory /var/lib/tor" >> /etc/tor/torrc && \
    echo "Log notice stderr" >> /etc/tor/torrc && \
    echo "ExitPolicy reject *:*" >> /etc/tor/torrc && \
    echo "StrictNodes 0" >> /etc/tor/torrc && \
    echo "DisableNetwork 0" >> /etc/tor/torrc && \
    chown -R debian-tor:debian-tor /var/lib/tor

# Create startup script
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Debug Python and API versions\n\
echo "=== Environment Debug ==="\n\
python3 --version\n\
python3 -c "import youtube_transcript_api; print(f\"YouTube Transcript API version: {youtube_transcript_api.__version__}\")" || echo "Could not get version"\n\
echo "========================"\n\
\n\
# Ensure Tor directories have correct permissions\n\
chown -R debian-tor:debian-tor /var/lib/tor\n\
chmod 700 /var/lib/tor\n\
\n\
# Start Tor as daemon\n\
echo "Starting Tor proxy as debian-tor user..."\n\
sudo -u debian-tor tor --RunAsDaemon 1 --pidfile /var/run/tor/tor.pid\n\
\n\
# Wait for Tor to start and create SOCKS port\n\
echo "Waiting for Tor to initialize..."\n\
for i in {1..30}; do\n\
    if netstat -ln | grep -q ":9050"; then\n\
        echo "✅ Tor SOCKS proxy is listening on port 9050"\n\
        break\n\
    fi\n\
    echo "Waiting for Tor to bind to port 9050... ($i/30)"\n\
    sleep 2\n\
done\n\
\n\
# Final verification\n\
if netstat -ln | grep -q ":9050"; then\n\
    echo "✅ Tor startup successful - proxy available on 127.0.0.1:9050"\n\
else\n\
    echo "⚠️  Tor may not be ready, but continuing..."\n\
fi\n\
\n\
echo "Starting Flask application..."\n\
# Start the Flask application\n\
exec gunicorn --bind 0.0.0.0:${PORT:-10000} --workers 1 --timeout 120 --log-level debug main:app\n\
' > /app/start.sh && chmod +x /app/start.sh

# Expose the port
EXPOSE ${PORT:-10000}

# Use the startup script
CMD ["/app/start.sh"]