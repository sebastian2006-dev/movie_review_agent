import requests
import json

# Keys from the user's latest .env
OMDB_API_KEY = "8bb4fda5"

def test_omdb_key(key):
    url = "http://www.omdbapi.com/"
    params = {"s": "Inception", "apikey": key}
    res = requests.get(url, params=params)
    print(f"OMDb Key {key}: {res.json()}")

test_omdb_key(OMDB_API_KEY)
