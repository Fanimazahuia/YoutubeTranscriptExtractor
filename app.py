import os
import logging
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
        
        app.logger.debug(f"Fetching transcript for video ID: {video_id}")
        
        # Fetch transcript using youtube-transcript-api
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        
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
        app.logger.error(f"Unexpected error fetching transcript for video ID {video_id}: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred while fetching the transcript'
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
        
        app.logger.debug(f"Fetching formatted transcript for video ID: {video_id}")
        
        # Fetch transcript using youtube-transcript-api
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        
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
        app.logger.error(f"Unexpected error fetching formatted transcript for video ID {video_id}: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred while fetching the transcript'
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
        'endpoints': {
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
        }
    }), 200

if __name__ == '__main__':
    # Run the Flask app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
