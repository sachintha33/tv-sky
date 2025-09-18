from flask import Flask, send_from_directory, jsonify
import requests
from cachetools import cached, TTLCache

app = Flask(__name__, static_folder='.', static_url_path='')

# Cache the playlist for 1 hour to reduce requests to the source
cache = TTLCache(maxsize=1, ttl=3600)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/playlist')
@cached(cache)
def get_playlist():
    urls = [
        'https://iptv-org.github.io/iptv/index.m3u',
        'https://raw.githubusercontent.com/iptv-org/iptv/master/index.m3u'
    ]
    for url in urls:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.text, 200, {'Content-Type': 'application/vnd.apple.mpegurl'}
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch playlist from {url}: {e}")
    
    return jsonify({"error": "Failed to fetch playlist from all sources"}), 500

if __name__ == '__main__':
    app.run(debug=True)
