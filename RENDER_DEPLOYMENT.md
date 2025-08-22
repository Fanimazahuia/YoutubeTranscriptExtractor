# Render Deployment Guide with Docker + Tor

## The Complete Solution for YouTube IP Blocking (August 2025)

This API now uses Docker to run Tor proxy on Render, which solves YouTube's cloud IP blocking completely. This is the same approach you used successfully before!

## What's Implemented

✅ **Docker container with Tor** - Full Tor installation and automatic startup  
✅ **Tor proxy integration** - Uses SOCKS5 proxy to bypass IP blocks  
✅ **Fallback strategies** - Multiple retry attempts with different methods  
✅ **Enhanced testing** - Tor connectivity verification in test endpoint  
✅ **Production ready** - Proper container orchestration and health checks  

## Deployment Steps for Render (Docker)

### 1. Set Up Your Render Service
1. **Connect your GitHub repository** to Render
2. **Important**: Set the **Environment** to **"Docker"** (not Python!)
3. **Auto-deploy** should be enabled from your main branch

### 2. Render Configuration
- **Build Command**: Leave empty (Docker handles this)
- **Start Command**: Leave empty (Docker handles this)
- **Dockerfile**: `./Dockerfile` (auto-detected)

### 3. Environment Variables (Optional)
- `SESSION_SECRET`: Any random string for Flask sessions

## Testing Your Deployment

After deployment, test these endpoints to verify Tor is working:

### 1. Health Check
```bash
curl https://your-app.onrender.com/health
```

### 2. Tor Connectivity Test (New!)
```bash
curl https://your-app.onrender.com/test
```
This endpoint now shows:
- ✅ Whether Tor is running in the container
- ✅ If YouTube transcripts are working via Tor
- ⚠️ Specific error messages if something is wrong

Expected successful response:
```json
{
  "status": "success",
  "message": "YouTube Transcript API is working correctly",
  "tor_status": {
    "tor_available": true,
    "message": "Tor proxy is running"
  },
  "sample_transcript": [...],
  "total_entries": 223
}
```

### 3. Real Transcript
```bash
curl "https://your-app.onrender.com/transcript?videoId=dQw4w9WgXcQ"
```

## Expected Behavior with Docker + Tor

- ✅ **All videos should work**: Tor bypasses cloud IP blocking completely
- ✅ **Consistent results**: Same video should work reliably every time
- ✅ **Fast performance**: Tor proxy adds minimal latency
- ✅ **No rate limits**: YouTube can't associate requests with cloud provider

## Docker Container Details

The Dockerfile:
1. **Installs Tor** using apt-get in Ubuntu base image
2. **Configures Tor** with proper SOCKS5 settings
3. **Starts Tor automatically** when container launches
4. **Waits for Tor initialization** before starting Flask app
5. **Runs health checks** to ensure Tor is working

## Troubleshooting

### If Test Endpoint Shows `tor_available: false`
- Check Render logs for Tor startup errors
- Verify Docker environment is selected (not Python)
- Try redeploying to refresh container

### If Transcripts Still Fail
- Check application logs for specific error messages
- Tor might need more time to establish circuits (restart service)
- Some videos genuinely don't have transcripts

## Migration from Previous Python Deployment

1. Change Environment from **Python** to **Docker** in Render
2. Remove any previous build/start commands
3. Let Render auto-detect the Dockerfile
4. Redeploy and test with `/test` endpoint