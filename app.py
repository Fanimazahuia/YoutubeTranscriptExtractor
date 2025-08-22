import os
import logging
import random
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable

# Configure logging for debugging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Enable CORS for cross-origin requests
CORS(app)

# List of user agents to rotate through for better compatibility
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0'
]

def get_transcript_with_retry(video_id, max_retries=3):
    """
    Fetch transcript with retry logic using Tor proxy and fallback strategies.
    
    Args:
        video_id (str): YouTube video ID
        max_retries (int): Maximum number of retry attempts
        
    Returns:
        list: Transcript data
        
    Raises:
        Exception: If all retry attempts fail
    """
    last_error = None
    
    for attempt in range(max_retries):
        try:
            app.logger.debug(f"Attempt {attempt + 1}: Fetching transcript for video ID: {video_id}")
            
            # Strategy 1: Try with Tor proxy first (should work in Docker)
            if attempt == 0:
                try:
                    proxies = {
                        'http': 'socks5h://127.0.0.1:9050',
                        'https': 'socks5h://127.0.0.1:9050'
                    }
                    app.logger.debug("Attempting to use Tor SOCKS5 proxy: 127.0.0.1:9050")
                    transcript_list = YouTubeTranscriptApi.get_transcript(video_id, proxies=proxies)
                    app.logger.debug(f"Successfully retrieved transcript via Tor proxy on attempt {attempt + 1}")
                    return transcript_list
                except Exception as proxy_error:
                    app.logger.warning(f"Tor proxy failed on attempt {attempt + 1}: {str(proxy_error)}")
                    last_error = proxy_error
            
            # Strategy 2: Direct connection with language variations
            language_combinations = [
                ['en'],
                ['en-US'],
                ['en-GB'], 
                ['en', 'en-US'],
                ['en', 'en-GB', 'en-US']
            ]
            
            languages = language_combinations[attempt % len(language_combinations)]
            app.logger.debug(f"Trying direct connection with languages: {languages}")
            
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
            app.logger.debug(f"Successfully retrieved transcript via direct connection on attempt {attempt + 1}")
            return transcript_list
            
        except Exception as e:
            last_error = e
            app.logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
            
            # Add delay between retries to avoid rate limiting
            if attempt < max_retries - 1:
                delay = random.uniform(2, 5)  # Random delay between 2-5 seconds
                app.logger.debug(f"Waiting {delay:.1f} seconds before retry...")
                time.sleep(delay)
    
    # All attempts failed, raise the last error
    if last_error:
        raise last_error
    else:
        raise Exception("Failed to retrieve transcript after all retry attempts")

@app.route('/transcript', methods=['GET'])
def get_transcript():
    """
    Fetch YouTube video transcript by video ID.

    Query Parameters:
        videoId (str): YouTube video ID (required)

    Returns:
        JSON: Array of transcript objects with start, duration, and text fields

    Error Responses:
        400: Missing or invalid videoId parameter
        404: Transcript not found or video unavailable
        500: Internal server error
    """
    try:
        # Get videoId from query parameters
        video_id = request.args.get('videoId')

        if not video_id:
            return jsonify({
                'error': 'Missing required parameter: videoId',
                'message': 'Please provide a YouTube video ID in the videoId query parameter'
            }), 400

        # Validate videoId format (basic check)
        if not video_id.strip():
            return jsonify({
                'error': 'Invalid videoId parameter',
                'message': 'videoId cannot be empty'
            }), 400

        # Use the new retry function with multiple strategies
        transcript_list = get_transcript_with_retry(video_id)

        # Format transcript data to match expected output
        formatted_transcript = []
        for entry in transcript_list:
            formatted_transcript.append({
                'start': entry.get('start', 0),
                'duration': entry.get('duration', 0),
                'text': entry.get('text', '')
            })

        app.logger.debug(f"Successfully retrieved transcript with {len(formatted_transcript)} entries")

        return jsonify(formatted_transcript), 200

    except TranscriptsDisabled:
        app.logger.warning(f"Transcripts disabled for video ID: {video_id}")
        return jsonify({
            'error': 'Transcripts disabled',
            'message': 'Transcripts are disabled for this video'
        }), 404

    except NoTranscriptFound:
        app.logger.warning(f"No transcript found for video ID: {video_id}")
        return jsonify({
            'error': 'No transcript found',
            'message': 'No transcript is available for this video'
        }), 404

    except VideoUnavailable:
        app.logger.warning(f"Video unavailable for video ID: {video_id}")
        return jsonify({
            'error': 'Video unavailable',
            'message': 'The requested video is unavailable or does not exist'
        }), 404

    except Exception as e:
        error_message = str(e)
        app.logger.error(f"Unexpected error fetching transcript for video ID {video_id}: {error_message}")
        
        # Check if it's an IP blocking issue and provide helpful guidance
        if "cloud provider" in error_message.lower() or "ip" in error_message.lower():
            return jsonify({
                'error': 'IP blocked by YouTube',
                'message': 'YouTube has blocked requests from this server IP. This is common with cloud hosting platforms. The service may work intermittently.',
                'suggestion': 'Try again later or use a different video ID for testing.',
                'technical_details': error_message
            }), 503
        else:
            return jsonify({
                'error': 'Internal server error',
                'message': 'An unexpected error occurred while fetching the transcript',
                'details': error_message
            }), 500

@app.route('/transcript/formatted', methods=['GET'])
def get_formatted_transcript():
    """
    Fetch YouTube video transcript by video ID and return as formatted text.

    Query Parameters:
        videoId (str): YouTube video ID (required)

    Returns:
        Text: Formatted transcript with timestamps in MM:SS format

    Error Responses:
        400: Missing or invalid videoId parameter
        404: Transcript not found or video unavailable
        500: Internal server error
    """
    try:
        # Get videoId from query parameters
        video_id = request.args.get('videoId')

        if not video_id:
            return jsonify({
                'error': 'Missing required parameter: videoId',
                'message': 'Please provide a YouTube video ID in the videoId query parameter'
            }), 400

        # Validate videoId format (basic check)
        if not video_id.strip():
            return jsonify({
                'error': 'Invalid videoId parameter',
                'message': 'videoId cannot be empty'
            }), 400

        # Use the new retry function with multiple strategies
        transcript_list = get_transcript_with_retry(video_id)

        # Format transcript as text with timestamps
        formatted_text = ""
        for entry in transcript_list:
            start_time = entry.get('start', 0)
            text = entry.get('text', '')

            # Convert seconds to MM:SS format
            minutes = int(start_time // 60)
            seconds = int(start_time % 60)
            timestamp = f"{minutes}:{seconds:02d}"

            formatted_text += f"{timestamp}\n{text}\n"

        app.logger.debug(f"Successfully formatted transcript with {len(transcript_list)} entries")

        # Return as plain text
        return formatted_text, 200, {'Content-Type': 'text/plain; charset=utf-8'}

    except TranscriptsDisabled:
        app.logger.warning(f"Transcripts disabled for video ID: {video_id}")
        return jsonify({
            'error': 'Transcripts disabled',
            'message': 'Transcripts are disabled for this video'
        }), 404

    except NoTranscriptFound:
        app.logger.warning(f"No transcript found for video ID: {video_id}")
        return jsonify({
            'error': 'No transcript found',
            'message': 'No transcript is available for this video'
        }), 404

    except VideoUnavailable:
        app.logger.warning(f"Video unavailable for video ID: {video_id}")
        return jsonify({
            'error': 'Video unavailable',
            'message': 'The requested video is unavailable or does not exist'
        }), 404

    except Exception as e:
        error_message = str(e)
        app.logger.error(f"Unexpected error fetching formatted transcript for video ID {video_id}: {error_message}")
        
        # Check if it's an IP blocking issue and provide helpful guidance
        if "cloud provider" in error_message.lower() or "ip" in error_message.lower():
            return jsonify({
                'error': 'IP blocked by YouTube',
                'message': 'YouTube has blocked requests from this server IP. This is common with cloud hosting platforms. The service may work intermittently.',
                'suggestion': 'Try again later or use a different video ID for testing.',
                'technical_details': error_message
            }), 503
        else:
            return jsonify({
                'error': 'Internal server error',
                'message': 'An unexpected error occurred while fetching the transcript',
                'details': error_message
            }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """
    Simple health check endpoint to verify the API is running.

    Returns:
        JSON: Status message
    """
    return jsonify({
        'status': 'healthy',
        'message': 'YouTube Transcript API is running'
    }), 200

def check_tor_connectivity():
    """
    Check if Tor is running and accessible.
    
    Returns:
        dict: Tor connectivity status
    """
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('127.0.0.1', 9050))
        sock.close()
        return {
            'tor_available': result == 0,
            'message': 'Tor proxy is running' if result == 0 else 'Tor proxy not available'
        }
    except Exception as e:
        return {
            'tor_available': False,
            'message': f'Error checking Tor: {str(e)}'
        }

@app.route('/test', methods=['GET'])
def test_endpoint():
    """
    Test endpoint with a known working video for cloud deployment testing.
    
    Returns:
        JSON: Test transcript result
    """
    # Using a popular video that usually has transcripts available
    test_video_id = "iCQ4SgVHENg"  # A short, popular video with reliable transcripts
    
    # Check Tor connectivity first
    tor_status = check_tor_connectivity()
    
    try:
        transcript_list = get_transcript_with_retry(test_video_id, max_retries=2)
        
        # Return just the first few entries for testing
        sample_transcript = transcript_list[:3] if len(transcript_list) > 3 else transcript_list
        
        return jsonify({
            'status': 'success',
            'message': 'YouTube Transcript API is working correctly',
            'test_video_id': test_video_id,
            'sample_transcript': sample_transcript,
            'total_entries': len(transcript_list),
            'tor_status': tor_status
        }), 200
        
    except Exception as e:
        error_message = str(e)
        
        if "cloud provider" in error_message.lower() or "ip" in error_message.lower():
            return jsonify({
                'status': 'ip_blocked',
                'message': 'YouTube is blocking requests from this cloud server IP',
                'error': error_message,
                'tor_status': tor_status,
                'suggestions': [
                    'This is common with cloud hosting platforms like Render, Heroku, etc.',
                    'Docker deployment with Tor should resolve this issue',
                    'Make sure to set Render to use Docker language/environment',
                    'Try deploying to a different region or hosting provider'
                ]
            }), 503
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to fetch test transcript',
                'error': error_message,
                'tor_status': tor_status
            }), 500

@app.route('/', methods=['GET'])
def root():
    """
    Root endpoint providing API documentation.

    Returns:
        JSON: API documentation and usage instructions
    """
    return jsonify({
        'name': 'YouTube Transcript API',
        'version': '1.0.0',
        'description': 'Fetch YouTube video transcripts using video ID',
        'status': 'Cloud deployment optimized with retry logic',
        'endpoints': {
            '/test': {
                'method': 'GET',
                'description': 'Test endpoint to verify API functionality with a sample video',
                'note': 'Use this to check if the service is working on your deployment'
            },
            '/transcript': {
                'method': 'GET',
                'description': 'Fetch transcript for a YouTube video (JSON format)',
                'parameters': {
                    'videoId': 'YouTube video ID (required)'
                },
                'example': '/transcript?videoId=dQw4w9WgXcQ'
            },
            '/transcript/formatted': {
                'method': 'GET',
                'description': 'Fetch transcript for a YouTube video (formatted text with timestamps)',
                'parameters': {
                    'videoId': 'YouTube video ID (required)'
                },
                'example': '/transcript/formatted?videoId=dQw4w9WgXcQ'
            },
            '/health': {
                'method': 'GET',
                'description': 'Health check endpoint'
            }
        },
        'cloud_deployment_notes': {
            'issue': 'YouTube blocks IPs from cloud providers',
            'solution': 'This API includes retry logic and error handling',
            'testing': 'Use /test endpoint to verify functionality',
            'status_codes': {
                '503': 'IP blocked by YouTube (common on cloud platforms)',
                '404': 'Video not found or transcript unavailable',
                '500': 'Other server errors'
            }
        }
    }), 200

if __name__ == '__main__':
    # Run the Flask app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)