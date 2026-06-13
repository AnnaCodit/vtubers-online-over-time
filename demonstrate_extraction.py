import re
import base64
import json
import requests
import sys

# Ensure UTF-8 output to avoid Windows console encoding issues
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def decode_twitchtracker_meta(content):
    """
    Decodes the obfuscated TwitchTracker metadata payload.
    It splits by '!', replaces '#' with 'W', and base64-decodes the parts.
    """
    parts = content.split('!')
    
    def db(s):
        return s.replace('#', 'W')

    def safe_b64decode(s):
        s = db(s)
        missing_padding = len(s) % 4
        if missing_padding:
            s += '=' * (4 - missing_padding)
        return base64.b64decode(s).decode('utf-8')

    keys = json.loads(safe_b64decode(parts[-1]))
    decoded_data = {}
    for idx, part in enumerate(parts[:-1]):
        key = keys[idx] if idx < len(keys) else f"part_{idx}"
        decoded_val = safe_b64decode(part)
        try:
            decoded_data[key] = json.loads(decoded_val)
        except Exception:
            # If not JSON (like the fragments URL itself), save raw stripped string
            decoded_data[key] = decoded_val.strip('"')
            
    return decoded_data

def get_streamer_stats(streamer_name):
    print(f"=== Fetching data for: {streamer_name} ===")
    
    # Step 1: Get main page HTML
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    main_url = f"https://twitchtracker.com/{streamer_name}"
    
    response = requests.get(main_url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch main page (Status: {response.status_code})")
        return None
        
    html = response.text
    
    # Step 2: Extract channel ID
    channel_id_match = re.search(r'window\.channel\s*=\s*\{\s*id\s*:\s*(\d+)', html)
    if not channel_id_match:
        # Try finding in data-clips if not in window.channel
        channel_id_match = re.search(r'"id":(\d+),"limit"', html)
        
    if not channel_id_match:
        print("Could not find channel ID in HTML")
        return None
        
    channel_id = int(channel_id_match.group(1))
    print(f"Found Channel ID: {channel_id}")
    
    # Step 3: Extract & Decode main page ecs metadata
    ecs_match = re.search(r'<meta id="ecs" content="([^"]+)"', html)
    if not ecs_match:
        print("Could not find <meta id='ecs'> tag in main page HTML")
        return None
        
    decoded_main = decode_twitchtracker_meta(ecs_match.group(1))
    fragments_url = decoded_main.get('fragments')
    if not fragments_url:
        print("Could not find fragments URL in decoded metadata")
        return None
        
    # Clean escaped slashes in the URL
    fragments_url = fragments_url.replace(r'\/', '/')
    print(f"Decoded Fragments URL: {fragments_url}")
    
    # Step 4: Perform POST to fragments URL
    post_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': main_url,
        'X-Requested-With': 'XMLHttpRequest'
    }
    post_data = {
        'id': channel_id
    }
    
    print("Requesting fragments data...")
    fragments_resp = requests.post(fragments_url, data=post_data, headers=post_headers)
    if fragments_resp.status_code != 200:
        print(f"Failed to fetch fragments page (Status: {fragments_resp.status_code})")
        return None
        
    fragments_html = fragments_resp.text
    
    # Step 5: Extract & Decode fragments ecs metadata
    fragments_ecs_match = re.search(r'<meta id="ecs" content="([^"]+)"', fragments_html)
    if not fragments_ecs_match:
        print("Could not find <meta id='ecs'> tag in fragments HTML")
        return None
        
    decoded_fragments = decode_twitchtracker_meta(fragments_ecs_match.group(1))
    
    # Step 6: Print out chart data
    charts_data = decoded_fragments.get('charts')
    if not charts_data or 'statistics' not in charts_data:
        print("Could not find charts statistics in decoded fragments metadata")
        return None
        
    print("\n--- Successful Extraction! ---")
    print(f"Monthly statistics for {streamer_name}:")
    print(f"{'Month':<12} | {'Avg Viewers':<12} | {'Peak Viewers':<12} | {'Hours Streamed':<14} | {'Followers Gain':<14}")
    print("-" * 75)
    for row in charts_data['statistics']:
        # row: [Date, Avg Viewers, Max Viewers, Minutes Streamed, Followers Gain, Game Weights]
        date = row[0]
        avg_viewers = row[1]
        max_viewers = row[2]
        hours_streamed = round(row[3] / 60, 1)
        followers_gain = row[4]
        print(f"{date:<12} | {avg_viewers:<12} | {max_viewers:<12} | {hours_streamed:<14} | {followers_gain:<14}")
        
    return decoded_fragments

if __name__ == "__main__":
    get_streamer_stats("fra3a")
