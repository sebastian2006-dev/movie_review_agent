import requests
import json

API_KEY = "8bb4fda5"

def test_omdb(title):
    url = "http://www.omdbapi.com/"
    params = {"t": title, "apikey": API_KEY, "plot": "full", "r": "json"}
    res = requests.get(url, params=params)
    print(f"--- {title} ---")
    data = res.json()
    if data.get("Response") == "True":
        print(f"Ratings: {data.get('Ratings')}")
    else:
        print(f"Error: {data.get('Error')}")

test_omdb("Breaking Bad")
test_omdb("Inception")
test_omdb("Interstellar")
