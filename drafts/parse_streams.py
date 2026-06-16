import re
import sys

# Ensure UTF-8 output to avoid Windows console encoding issues
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

with open("fragments_response.html", "r", encoding="utf-8") as f:
    html = f.read()

# Let's find the section for recent streams:
match = re.search(r'id="channel-streams-wrapper".*?</section>', html, re.DOTALL | re.IGNORECASE)
if match:
    print("Found channel-streams-wrapper section!")
    section_html = match.group(0)
    
    # Save the section html to a separate file so we can view it cleanly
    with open("streams_section.html", "w", encoding="utf-8") as f_out:
        f_out.write(section_html)
    print("Saved streams section to streams_section.html")
    
    # Let's print out all numbers inside elements
    print("\n--- All numbers in this section ---")
    numbers = re.findall(r'>\s*(\d+)\s*<', section_html)
    print(numbers)
    
    # Let's also look for avg/max/peak/hours/viewers values
    # e.g. `<div class="to-number">105</div>` or similar structures
    print("\n--- Matching patterns with viewer counts ---")
    # Let's find matches of class="..." and inside them numbers
    for m in re.finditer(r'<div class="([^"]*)"[^>]*>\s*(\d+)\s*</div>', section_html):
        print(f"Class: {m.group(1)} -> Value: {m.group(2)}")
    
    for m in re.finditer(r'<span class="([^"]*)"[^>]*>\s*(\d+)\s*</span>', section_html):
        print(f"Class: {m.group(1)} -> Value: {m.group(2)}")
        
    for m in re.finditer(r'<td class="([^"]*)"[^>]*>\s*(\d+)\s*</td>', section_html):
        print(f"Class: {m.group(1)} -> Value: {m.group(2)}")
else:
    print("Could not find channel-streams-wrapper.")
