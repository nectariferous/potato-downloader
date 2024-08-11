from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
from pytube import YouTube, Search
import os
import logging
from datetime import datetime
import json
from io import BytesIO

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Setup logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

# Global variable to store start time
start_time = datetime.now()

def get_video_info(video_url):
    try:
        yt = YouTube(video_url)
        streams = yt.streams.filter(progressive=True)
        
        available_resolutions = [
            {
                "itag": stream.itag,
                "resolution": stream.resolution,
                "filesize": stream.filesize,
                "fps": stream.fps
            } for stream in streams
        ]
        
        highest_res_stream = yt.streams.get_highest_resolution()
        
        video_info = {
            "title": yt.title,
            "description": yt.description,
            "views": yt.views,
            "rating": yt.rating,
            "length": yt.length,
            "author": yt.author,
            "publish_date": str(yt.publish_date),
            "thumbnail_url": yt.thumbnail_url,
            "available_resolutions": available_resolutions,
            "highest_resolution": {
                "itag": highest_res_stream.itag,
                "resolution": highest_res_stream.resolution,
                "filesize": highest_res_stream.filesize
            }
        }
        return video_info
    except Exception as e:
        logging.error(f"Error in get_video_info: {str(e)}")
        return {"error": str(e)}

@app.route('/api/video_info', methods=['GET'])
def video_info():
    video_url = request.args.get('url')
    if not video_url:
        return jsonify({"error": "No URL provided"}), 400
    
    info = get_video_info(video_url)
    return jsonify(info)

@app.route('/api/download', methods=['GET'])
def download_video():
    video_url = request.args.get('url')
    itag = request.args.get('itag')
    if not video_url:
        return jsonify({"error": "No URL provided"}), 400
    
    try:
        yt = YouTube(video_url)
        if itag:
            stream = yt.streams.get_by_itag(int(itag))
        else:
            stream = yt.streams.get_highest_resolution()
        
        buffer = BytesIO()
        stream.stream_to_buffer(buffer)
        buffer.seek(0)
        
        return Response(
            buffer,
            mimetype='video/mp4',
            headers={"Content-Disposition": f"attachment;filename={yt.title}.mp4"}
        )
    except Exception as e:
        logging.error(f"Error in download_video: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/search', methods=['GET'])
def search_videos():
    query = request.args.get('q')
    limit = request.args.get('limit', default=10, type=int)
    if not query:
        return jsonify({"error": "No search query provided"}), 400
    
    try:
        search_results = Search(query).results
        videos = []
        for video in search_results[:limit]:
            videos.append({
                "title": video.title,
                "url": video.watch_url,
                "thumbnail": video.thumbnail_url,
                "duration": video.length,
                "views": video.views,
                "author": video.author
            })
        return jsonify(videos)
    except Exception as e:
        logging.error(f"Error in search_videos: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    return jsonify({
        "uptime": str(datetime.now() - start_time)
    })

@app.route('/')
def home():
    return jsonify({
        "message": "Welcome to the YouTube Video API",
        "endpoints": [
            "/api/video_info",
            "/api/download",
            "/api/search",
            "/api/stats"
        ]
    })

if __name__ == '__main__':
    app.run(debug=True)
