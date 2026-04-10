import requests
import streamlit as st

API_KEY = st.secrets["OMDB_API_KEY"]


def fetch_movie_data(title: str):

    if not API_KEY:
        raise ValueError("Missing OMDB_API_KEY.")

    # 🔥 STEP 1: better query (adds full plot + better matching)
    url = "http://www.omdbapi.com/"
    params = {
        "t": title,
        "apikey": API_KEY,
        "plot": "full",
        "r": "json"
    }

    try:
        res = requests.get(url, params=params, timeout=10)
        data = res.json()
    except Exception as e:
        print("OMDB REQUEST FAILED:", e)
        return None

    if not data or data.get("Response") == "False":
        return None

    # 🔥 STEP 2: safely extract ratings (OMDb structure is messy)
    ratings = {}
    for r in data.get("Ratings", []):
        ratings[r.get("Source")] = r.get("Value")

    return {
        "title": data.get("Title"),
        "year": data.get("Year"),
        "plot": data.get("Plot"),
        "actors": data.get("Actors"),
        "genre": data.get("Genre"),
        "director": data.get("Director"),
        "writer": data.get("Writer"),

        "imdb_rating": data.get("imdbRating"),
        "metascore": data.get("Metascore"),
        "ratings": ratings,

        "poster": data.get("Poster"),
        "runtime": data.get("Runtime"),
        "language": data.get("Language"),
        "country": data.get("Country")
    }