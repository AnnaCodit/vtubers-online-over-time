import os
import re
import csv
import time
import random
import base64
import json
import requests
import sys

# Ensure UTF-8 output to avoid Windows console encoding issues
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

CSV_FILENAME = os.path.join("data", "vtubers_avg_online.csv")
VTUBERS_FILENAME = "vtubers.txt"
# Ensure the data directory exists
os.makedirs("data", exist_ok=True)

def decode_twitchtracker_meta(content):
    """
    Decodes the obfuscated TwitchTracker metadata payload.
    Splits by '!', replaces '#' with 'W', and base64-decodes the parts.
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
            decoded_data[key] = decoded_val.strip('"')
            
    return decoded_data

def get_streamer_stats(streamer_name):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    main_url = f"https://twitchtracker.com/{streamer_name}"
    
    # Fetch main page
    response = requests.get(main_url, headers=headers, timeout=15)
    if response.status_code != 200:
        print(f"[{streamer_name}] Failed to fetch main page (Status: {response.status_code})")
        return None
        
    html = response.text
    
    # Extract channel ID
    channel_id_match = re.search(r'window\.channel\s*=\s*\{\s*id\s*:\s*(\d+)', html)
    if not channel_id_match:
        channel_id_match = re.search(r'"id":(\d+),"limit"', html)
        
    if not channel_id_match:
        print(f"[{streamer_name}] Could not find channel ID in HTML")
        return None
        
    channel_id = int(channel_id_match.group(1))
    
    # Extract & Decode main page ecs metadata
    ecs_match = re.search(r'<meta id="ecs" content="([^"]+)"', html)
    if not ecs_match:
        print(f"[{streamer_name}] Could not find <meta id='ecs'> tag in main page")
        return None
        
    decoded_main = decode_twitchtracker_meta(ecs_match.group(1))
    fragments_url = decoded_main.get('fragments')
    if not fragments_url:
        print(f"[{streamer_name}] Could not find fragments URL in decoded metadata")
        return None
        
    fragments_url = fragments_url.replace(r'\/', '/')
    
    # Sleep briefly before the fragments POST request to mimic natural behavior
    time.sleep(0.5)
    
    # POST to fragments URL
    post_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': main_url,
        'X-Requested-With': 'XMLHttpRequest'
    }
    post_data = {
        'id': channel_id
    }
    
    fragments_resp = requests.post(fragments_url, data=post_data, headers=post_headers, timeout=15)
    if fragments_resp.status_code != 200:
        print(f"[{streamer_name}] Failed to fetch fragments (Status: {fragments_resp.status_code})")
        return None
        
    fragments_html = fragments_resp.text
    
    # Extract & Decode fragments ecs metadata
    fragments_ecs_match = re.search(r'<meta id="ecs" content="([^"]+)"', fragments_html)
    if not fragments_ecs_match:
        print(f"[{streamer_name}] Could not find <meta id='ecs'> tag in fragments HTML")
        return None
        
    decoded_fragments = decode_twitchtracker_meta(fragments_ecs_match.group(1))
    
    charts_data = decoded_fragments.get('charts')
    if not charts_data or 'statistics' not in charts_data:
        print(f"[{streamer_name}] Could not find charts statistics in decoded fragments")
        return None
        
    return charts_data['statistics']

def load_processed_vtubers():
    """
    Reads the output CSV to see which vtubers have already been processed
    """
    processed = set()
    if os.path.exists(CSV_FILENAME):
        try:
            with open(CSV_FILENAME, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None) # Skip header
                if header:
                    for row in reader:
                        if len(row) >= 2:
                            processed.add(row[1].strip().lower())
        except Exception as e:
            print(f"Warning reading existing CSV file: {e}")
    return processed

def main():
    if not os.path.exists(VTUBERS_FILENAME):
        print(f"Error: {VTUBERS_FILENAME} not found.")
        sys.exit(1)
        
    # Read vtubers list
    with open(VTUBERS_FILENAME, "r", encoding="utf-8") as f:
        vtubers = [line.strip() for line in f if line.strip()]
        
    print(f"Loaded {len(vtubers)} vtubers from {VTUBERS_FILENAME}")
    
    # Load processed vtubers
    processed = load_processed_vtubers()
    print(f"Already processed: {len(processed)} vtubers")
    
    # Filter to process list
    to_process = [v for v in vtubers if v.lower() not in processed]
    print(f"Remaining to process: {len(to_process)} vtubers")
    
    if not to_process:
        print("All vtubers have been processed!")
        return
        
    # Open CSV file for appending
    file_exists = os.path.exists(CSV_FILENAME)
    
    with open(CSV_FILENAME, "a", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        
        # Write header if new file
        if not file_exists:
            writer.writerow(["month", "vtuber", "avg_viewers"])
            csv_file.flush()
            
        for i, vtuber in enumerate(to_process):
            print(f"\n[{i+1}/{len(to_process)}] Processing: {vtuber}")
            try:
                stats = get_streamer_stats(vtuber)
                if stats:
                    added_rows = 0
                    for row in stats:
                        # row: [Date, Avg Viewers, Max Viewers, Minutes Streamed, Followers Gain, Game Weights]
                        date = row[0]
                        avg_viewers = row[1]
                        writer.writerow([date, vtuber, avg_viewers])
                        added_rows += 1
                        
                    csv_file.flush() # Ensure it's saved immediately
                    print(f"[{vtuber}] Success! Saved {added_rows} monthly records.")
                else:
                    print(f"[{vtuber}] Skipped or failed.")
            except Exception as e:
                print(f"[{vtuber}] Unexpected error occurred: {e}")
                
            # Random sleep 1-3 seconds between different vtubers
            sleep_time = random.uniform(1.0, 3.0)
            print(f"Sleeping for {sleep_time:.2f} seconds...")
            time.sleep(sleep_time)

    print("\nProcessing completed!")

if __name__ == "__main__":
    main()
