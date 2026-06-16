import requests

url = "https://twitchtracker.com/fra3a/fragments?expires=1781391209&signature=4c2df1fe73ed184d99d1598faf6b120aa56b9991dbb95782cc258e5f1d461173"
data = {
    'id': 1239759441
}
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://twitchtracker.com/fra3a',
    'X-Requested-With': 'XMLHttpRequest'
}

response = requests.post(url, data=data, headers=headers)
print("Status Code:", response.status_code)
print("Content length:", len(response.text))
with open("fragments_response.html", "w", encoding="utf-8") as f:
    f.write(response.text)

print("Saved to fragments_response.html")
