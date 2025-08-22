#!/bin/bash

# Local Docker test script
# This helps verify the Docker container works correctly before deploying to Render

echo "Building Docker image..."
docker build -t youtube-transcript-api .

if [ $? -eq 0 ]; then
    echo "✅ Docker build successful"
    
    echo "Starting container on port 8080..."
    docker run -p 8080:10000 --rm --name youtube-api-test youtube-transcript-api &
    
    # Wait for container to start
    echo "Waiting for container to initialize (30 seconds)..."
    sleep 30
    
    echo "Testing health endpoint..."
    curl -s http://localhost:8080/health | python3 -m json.tool
    
    echo -e "\nTesting Tor connectivity and transcript functionality..."
    curl -s http://localhost:8080/test | python3 -m json.tool
    
    echo -e "\nStopping container..."
    docker stop youtube-api-test
    
    echo "✅ Docker test completed. If you see Tor working above, deploy to Render!"
else
    echo "❌ Docker build failed"
    exit 1
fi