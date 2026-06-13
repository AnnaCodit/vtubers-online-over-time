import re
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

with open("streams_section.html", "r", encoding="utf-8") as f:
    html = f.read()

# Let's find all instances of:
# <a class="entity entity-line" href="/fra3a/streams/..." title="..." ...>
# <div data-dt="...">...</div>
# <div><div class="to-number-lg">MAX_VIEWERS</div></div>

# Regex to find each stream link block
stream_blocks = re.findall(r'<a class="entity entity-line"[^>]*>.*?</a>', html, re.DOTALL)
print(f"Found {len(stream_blocks)} stream blocks:")

for idx, block in enumerate(stream_blocks):
    dt_match = re.search(r'data-dt="([^"]+)"', block)
    title_match = re.search(r'title="([^"]+)"', block)
    
    # Inside the block there are three divs with classes to-number-lg/to-time-lg.
    # The first one is Max Viewers
    # The second one is Followers Gained
    # The third one is Duration
    nums = re.findall(r'class="to-number-lg">(\d+)</div>', block)
    duration_match = re.search(r'class="to-time-lg">(\d+)</div>', block)
    
    dt = dt_match.group(1) if dt_match else "N/A"
    title = title_match.group(1) if title_match else "N/A"
    max_viewers = nums[0] if len(nums) > 0 else "N/A"
    followers = nums[1] if len(nums) > 1 else "N/A"
    duration = duration_match.group(1) if duration_match else "N/A"
    
    # print
    print(f"Stream {idx+1}: Date={dt} | Max Viewers={max_viewers} | Followers={followers} | Duration={duration} mins | Title={title[:40]}...")
