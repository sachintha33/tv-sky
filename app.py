from flask import Flask, send_from_directory, jsonify
import requests
import urllib.parse
import re
from cachetools import cached, TTLCache

app = Flask(__name__, static_folder='.', static_url_path='')

# Cache the playlist for 1 hour to reduce requests to the source
cache = TTLCache(maxsize=1, ttl=3600)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/channels')
@cached(cache)
def get_channels():
    urls = [
        'https://iptv-org.github.io/iptv/index.m3u',
        'https://raw.githubusercontent.com/iptv-org/iptv/master/index.m3u'
    ]
    for url in urls:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            lines = response.text.split('\n')
            channels = []
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                if line.startswith('#EXTINF'):
                    current = {
                        "name": 'Unknown',
                        "group": '',
                        "country": '',
                        "logo": '',
                        "url": ''
                    }
                    
                    # Extract group, logo, country, name using regex
                    group_match = re.search(r'group-title="([^"]*)"', line, re.IGNORECASE)
                    logo_match = re.search(r'tvg-logo="([^"]*)"', line, re.IGNORECASE)
                    country_match = re.search(r'tvg-country="([^"]*)"', line, re.IGNORECASE)
                    name_match = re.search(r',(.+)$', line)
                    
                    if group_match:
                        current["group"] = group_match.group(1).strip()
                    if logo_match:
                        current["logo"] = logo_match.group(1).strip()
                    if country_match:
                        current["country"] = country_match.group(1).strip().upper()
                    if name_match:
                        current["name"] = name_match.group(1).strip()
                    else:
                        # Fallback for name
                        if ',' in line:
                            current["name"] = line.split(',', 1)[1].strip().strip('"')
                    
                    i += 1
                    if i < len(lines):
                        url_line = lines[i].strip()
                        if url_line.startswith('http'):
                            current["url"] = url_line
                            channels.append(current)
                i += 1
            
            if channels:
                return jsonify(channels)
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch channels from {url}: {e}")
    
    return jsonify({"error": "Failed to fetch channels from all sources"}), 500


if __name__ == '__main__':
    app.run(debug=True)
