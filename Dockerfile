# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Install system dependencies including Tor
RUN apt-get update && apt-get install -y \
    tor \
    curl \
    && rm -rf /var/lib/apt/lists/*

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
RUN echo "SocksPort 0.0.0.0:9050" > /etc/tor/torrc && \
    echo "ControlPort 0.0.0.0:9051" >> /etc/tor/torrc && \
    echo "DataDirectory /var/lib/tor" >> /etc/tor/torrc && \
    echo "Log notice stdout" >> /etc/tor/torrc && \
    echo "ExitPolicy reject *:*" >> /etc/tor/torrc && \
    echo "StrictNodes 1" >> /etc/tor/torrc

# Create startup script
RUN echo '#!/bin/bash\n\
# Debug Python and API versions\n\
echo "=== Environment Debug ==="\n\
python3 --version\n\
python3 -c "import youtube_transcript_api; print(f\"YouTube Transcript API version: {youtube_transcript_api.__version__}\")" || echo "Could not get version"\n\
python3 -c "from youtube_transcript_api import YouTubeTranscriptApi; print(\"Available methods:\", [m for m in dir(YouTubeTranscriptApi) if not m.startswith(\"_\")])"\n\
echo "========================"\n\
\n\
# Start Tor in background\n\
echo "Starting Tor proxy..."\n\
tor &\n\
\n\
# Wait for Tor to start\n\
echo "Waiting for Tor to start..."\n\
sleep 15\n\
\n\
# Check if Tor is running\n\
echo "Testing Tor connectivity..."\n\
if timeout 10 curl --socks5-hostname 127.0.0.1:9050 http://check.torproject.org/ 2>/dev/null | grep -q "Congratulations"; then\n\
    echo "✅ Tor is running successfully"\n\
else\n\
    echo "⚠️  Tor startup verification failed, but continuing..."\n\
    # Check if Tor process is at least running\n\
    if pgrep tor > /dev/null; then\n\
        echo "Tor process is running on PID: $(pgrep tor)"\n\
    else\n\
        echo "Tor process not found"\n\
    fi\n\
fi\n\
\n\
# Test YouTube API functionality\n\
echo "Testing YouTube Transcript API..."\n\
python3 -c "from youtube_transcript_api import YouTubeTranscriptApi; t = YouTubeTranscriptApi.list_transcripts(\"iCQ4SgVHENg\").find_transcript([\"en\"]).fetch(); print(f\"✅ API test successful, got {len(t)} entries\")" || echo "⚠️  API test failed"\n\
\n\
echo "Starting Flask application..."\n\
# Start the Flask application\n\
exec gunicorn --bind 0.0.0.0:${PORT:-10000} --workers 1 --timeout 120 --log-level debug main:app\n\
' > /app/start.sh && chmod +x /app/start.sh

# Expose the port
EXPOSE ${PORT:-10000}

# Use the startup script
CMD ["/app/start.sh"]