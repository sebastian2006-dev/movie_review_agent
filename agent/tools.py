import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OMDB_API_KEY")

def fetch_movie_data(title: str):

    if not API_KEY:
        raise ValueError("Missing OMDB_API_KEY. Add it to your .env file.")

    url = f"http://www.omdbapi.com/?t={title}&apikey={API_KEY}"

    try:
        res = requests.get(url)
        data = res.json()
    except:
        return None

    if data.get("Response") == "False":
        return None

    return {
        "title": data.get("Title"),
        "year": data.get("Year"),
        "plot": data.get("Plot"),
        "actors": data.get("Actors"),
        "genre": data.get("Genre"),
        "imdb_rating": data.get("imdbRating"),
        "poster": data.get("Poster")
    }