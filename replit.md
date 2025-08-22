# YouTube Transcript Extractor API

## Overview

This is a Flask-based REST API service that extracts transcripts from YouTube videos using the YouTube Transcript API. The service provides a simple endpoint to fetch video transcripts by providing a YouTube video ID. The application is designed to handle common YouTube API limitations, including IP blocking from cloud providers, and implements proxy fallback mechanisms for improved reliability.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Framework
- **Flask**: Lightweight Python web framework chosen for its simplicity and ease of deployment
- **WSGI Server**: Uses Gunicorn for production deployment, providing better performance and stability than Flask's development server
- **CORS Support**: Enabled cross-origin requests to allow frontend applications from different domains to consume the API

### API Design
- **Primary Endpoints**: 
  - `/transcript` - JSON format transcript data
  - `/transcript/formatted` - Human-readable text with timestamps
  - `/test` - Built-in testing endpoint for cloud deployment verification
  - `/health` - Service health check
- **Error Handling**: Comprehensive error responses for missing parameters, invalid video IDs, transcript unavailability, and IP blocking scenarios
- **Response Format**: JSON responses with structured data containing transcript timing and text information
- **Cloud Deployment Testing**: Dedicated `/test` endpoint provides immediate verification of service functionality

### Network Resilience (Docker + Tor Solution - August 2025)
- **Docker Container with Tor**: Complete Tor proxy setup within Docker container for cloud deployment
- **SOCKS5 Proxy Integration**: Primary strategy uses Tor SOCKS5 proxy (127.0.0.1:9050) to bypass YouTube IP blocking
- **Multi-Layer Fallback**: Attempts Tor proxy first, then falls back to direct connection with language variations
- **Tor Connectivity Verification**: Built-in health checks to verify Tor proxy availability and functionality
- **Cloud Platform Ready**: Specifically designed for Render Docker deployments to solve cloud IP blocking completely
- **Progressive Retry Logic**: Random delays (2-5 seconds) between attempts with multiple language code fallbacks

### Logging and Monitoring
- **Debug Logging**: Comprehensive logging system for tracking API requests, proxy attempts, and error conditions
- **Error Tracking**: Detailed error messages for debugging YouTube API limitations and network issues

### Security
- **Environment Variables**: Session secret key configurable via environment variables with fallback to development key
- **Input Validation**: Basic validation of video ID parameters to prevent empty or malformed requests

### Deployment Architecture
- **Docker Container**: Containerized deployment with Ubuntu base image for full system control
- **Tor Integration**: Automatic Tor installation and configuration within container
- **Cloud Deployment**: Optimized for Render Docker environment with proper orchestration
- **Port Configuration**: Flexible port binding (default 10000) with environment variable support
- **Process Management**: Container startup script manages Tor initialization followed by Gunicorn server
- **Health Monitoring**: Built-in Tor connectivity checks and service health verification

## External Dependencies

### Core Libraries
- **Flask**: Web framework for API endpoints and request handling
- **Flask-CORS**: Cross-origin resource sharing support for frontend integration
- **youtube-transcript-api**: Primary library for fetching YouTube video transcripts
- **Gunicorn**: WSGI HTTP Server for production deployment

### Network Dependencies
- **YouTube API**: Relies on YouTube's internal transcript API for data retrieval
- **Tor Network** (Optional): SOCKS5 proxy support for IP masking when available
- **HTTPS Connections**: All YouTube API requests made over secure connections

### Cloud Platform Integration
- **Render**: Current deployment platform with automatic builds and deployments
- **Environment Configuration**: Supports environment-based configuration for different deployment stages

### Known Limitations
- **IP Blocking**: YouTube blocks requests from cloud provider IPs, requiring proxy solutions
- **Rate Limiting**: Subject to YouTube's rate limiting policies
- **Transcript Availability**: Not all videos have transcripts available, handled gracefully with appropriate error responses