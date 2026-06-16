import csv
import os
import sys
import json
import time
import requests

# Ensure UTF-8 output to avoid Windows console encoding issues
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

INPUT_CSV = os.path.join("data", "vtubers_avg_online.csv")
OUTPUT_CSV = os.path.join("data", "vtubers_wide_stats.csv")
CACHE_FILE = os.path.join("data", "vtuber_images_cache.json")
# Ensure the data directory exists
os.makedirs("data", exist_ok=True)

DEFAULT_AVATAR = "https://static-cdn.jtvnw.net/jtv_user_pictures/bc0af20e-b4db-4205-a2ba-f6aaf2903c1d-profile_image-600x600.png"

def load_image_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning reading image cache: {e}")
    return {}

def save_image_cache(cache):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Warning saving image cache: {e}")

def fetch_twitch_logo(username):
    url = f"https://api.ivr.fi/v2/twitch/user?login={username}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # The API returns a list of users, or a single user depending on query
            if isinstance(data, list) and len(data) > 0:
                logo_url = data[0].get('logo')
                if logo_url:
                    return logo_url
            elif isinstance(data, dict):
                logo_url = data.get('logo')
                if logo_url:
                    return logo_url
        else:
            print(f"  [API] Failed for {username}: Status {response.status_code}")
    except Exception as e:
        print(f"  [API] Error for {username}: {e}")
    return None

def main():
    if not os.path.exists(INPUT_CSV):
        print(f"Error: input file {INPUT_CSV} not found.")
        sys.exit(1)

    # 1. Read input CSV
    print(f"Reading {INPUT_CSV}...")
    unique_months = set()
    unique_vtubers = set()
    stats = {} # Nested dict: stats[vtuber][month] = avg_viewers

    with open(INPUT_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            month = row['month'].strip()
            vtuber = row['vtuber'].strip()
            avg_viewers = row['avg_viewers'].strip()
            
            # Treat empty/invalid/null avg_viewers as 0
            try:
                avg_viewers_val = int(float(avg_viewers))
            except ValueError:
                avg_viewers_val = 0
                
            unique_months.add(month)
            unique_vtubers.add(vtuber)
            
            if vtuber not in stats:
                stats[vtuber] = {}
            stats[vtuber][month] = avg_viewers_val

    # 2. Sort months chronologically
    sorted_months = sorted(list(unique_months))
    print(f"Found {len(unique_vtubers)} vtubers and {len(sorted_months)} months of data.")
    print(f"Data range: {sorted_months[0]} to {sorted_months[-1]}")

    # 3. Load image cache
    image_cache = load_image_cache()
    print(f"Loaded {len(image_cache)} profile images from cache.")

    # 4. Fetch missing image URLs
    # Filter only vtubers that are in the parsed statistics
    sorted_vtubers = sorted(list(unique_vtubers))
    
    needed_fetch = [v for v in sorted_vtubers if v.lower() not in image_cache]
    print(f"Fetching logos for {len(needed_fetch)} new vtubers...")

    for idx, vtuber in enumerate(sorted_vtubers):
        v_lower = vtuber.lower()
        if v_lower not in image_cache:
            print(f"[{idx+1}/{len(sorted_vtubers)}] Fetching logo for: {vtuber}")
            logo_url = fetch_twitch_logo(vtuber)
            if logo_url:
                image_cache[v_lower] = logo_url
                print(f"  Success: {logo_url[:60]}...")
            else:
                image_cache[v_lower] = DEFAULT_AVATAR
                print(f"  Failed. Set fallback: {DEFAULT_AVATAR}")
            
            # Save cache incrementally to prevent data loss
            save_image_cache(image_cache)
            
            # Delay 0.5 seconds as requested
            time.sleep(0.5)

    # 5. Write the wide CSV file
    print(f"Writing wide statistics to {OUTPUT_CSV}...")
    headers = ["Label", "Image URL"] + sorted_months

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        
        for vtuber in sorted_vtubers:
            v_lower = vtuber.lower()
            logo_url = image_cache.get(v_lower, DEFAULT_AVATAR)
            
            row = [vtuber, logo_url]
            for month in sorted_months:
                # Fill with 0 if data for month doesn't exist
                val = stats[vtuber].get(month, 0)
                row.append(val)
                
            writer.writerow(row)

    print(f"Finished! Successfully generated {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
