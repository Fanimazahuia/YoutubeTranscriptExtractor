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
RUN pip install --no-cache-dir uv && \
    uv pip install --system -r pyproject.toml

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
# Start Tor in background\n\
tor &\n\
\n\
# Wait for Tor to start\n\
echo "Waiting for Tor to start..."\n\
sleep 10\n\
\n\
# Check if Tor is running\n\
if curl --socks5-hostname 127.0.0.1:9050 http://check.torproject.org/ | grep -q "Congratulations"; then\n\
    echo "Tor is running successfully"\n\
else\n\
    echo "Tor startup verification failed, but continuing..."\n\
fi\n\
\n\
# Start the Flask application\n\
exec gunicorn --bind 0.0.0.0:${PORT:-10000} --workers 1 --timeout 120 main:app\n\
' > /app/start.sh && chmod +x /app/start.sh

# Expose the port
EXPOSE ${PORT:-10000}

# Use the startup script
CMD ["/app/start.sh"]