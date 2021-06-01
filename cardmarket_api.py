import requests
print(requests.get("https://api.cardmarket.com/ws/v2.0/expansions/1469/singles").content)