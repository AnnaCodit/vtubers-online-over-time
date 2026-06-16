with open("fragments_response.html", "r", encoding="utf-8") as f:
    html = f.read()

# Let's print out lines containing "viewer", "online", or the target numbers
lines = html.splitlines()
print(f"Total lines: {len(lines)}")

print("\n--- Lines with 'viewer' ---")
for i, line in enumerate(lines):
    if "viewer" in line.lower() or "83" in line or "71" in line or "105" in line:
        print(f"Line {i+1}: {line.strip()[:150]}")
