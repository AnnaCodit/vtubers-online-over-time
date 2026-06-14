import requests

url = "https://api.ivr.fi/v2/twitch/user?login=fra3a"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

response = requests.get(url, headers=headers)
print("Status Code:", response.status_code)
if response.status_code == 200:
    data = response.json()
    print("Response JSON keys:", data[0].keys() if isinstance(data, list) else data.keys())
    print("Sample response (first level keys):")
    # Print the structure of the response to see how to extract the avatar/logo URL
    import pprint
    pprint.pprint(data)
else:
    print(response.text)
