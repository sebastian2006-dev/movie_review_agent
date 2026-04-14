import requests
import streamlit as st
from agent.sentiment import analyze_movie

API_KEY = st.secrets["OMDB_API_KEY"]

# ---------------- FETCH MOVIE DATA ----------------
def fetch_movie_data(title: str):
    if not API_KEY:
        raise ValueError("Missing OMDB_API_KEY.")

    url = "http://www.omdbapi.com/"
    params = {"t": title, "apikey": API_KEY, "plot": "full", "r": "json"}

    try:
        res = requests.get(url, params=params, timeout=10)
        data = res.json()
    except:
        return None

    if not data or data.get("Response") == "False":
        return None

    imdb_rating = data.get("imdbRating")
    if not imdb_rating or imdb_rating == "N/A":
        imdb_rating = "—"

    return {
        "title": data.get("Title"),
        "year": data.get("Year"),
        "plot": data.get("Plot"),
        "actors": data.get("Actors"),
        "genre": data.get("Genre"),
        "director": data.get("Director"),
        "imdb_rating": imdb_rating,
        "poster": data.get("Poster"),
        "runtime": data.get("Runtime"),
    }

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Movie Review Agent", layout="wide", initial_sidebar_state="collapsed")

# ---------------- SESSION STATE ----------------
if "cached_query"  not in st.session_state: st.session_state.cached_query  = None
if "cached_movie"  not in st.session_state: st.session_state.cached_movie  = None
if "cached_result" not in st.session_state: st.session_state.cached_result = None

# ---------------- HERO HEADER ----------------
st.markdown("### 🎬 Movie Debate AI")
user_input = st.chat_input("Search a movie title...")

# ---------------- MAIN LOGIC ----------------
if user_input:
    query_key = user_input.strip().lower()
    if query_key != st.session_state.cached_query:
        st.session_state.cached_query  = query_key
        st.session_state.cached_movie  = fetch_movie_data(user_input)
        st.session_state.cached_result = None

        if st.session_state.cached_movie:
            raw_reviews = {
                "title": st.session_state.cached_movie["title"],
                "critic_reviews": st.session_state.cached_movie["plot"],
                "audience_reactions": st.session_state.cached_movie["actors"],
                "discussion_points": st.session_state.cached_movie["genre"],
            }
            with st.spinner("Running AI debate..."):
                st.session_state.cached_result = analyze_movie(raw_reviews)

movie  = st.session_state.cached_movie
result = st.session_state.cached_result

if movie is None and st.session_state.cached_query is not None:
    st.error("No movie found.")

elif movie and result:

    # Movie header
    col_poster, col_info = st.columns([1,2])
    with col_poster:
        if movie["poster"] != "N/A":
            st.image(movie["poster"])

    with col_info:
        st.title(movie["title"])
        st.caption(f"{movie['year']} • {movie['director']} • ⭐ IMDb {movie['imdb_rating']}")
        st.write(movie["plot"])
        st.caption(f"Cast: {movie['actors']}")

    st.divider()

    # ---------------- DEBATE TRANSCRIPT (TOP) ----------------
    st.header("⚔️ AI Debate Transcript")

    debate = result.get("debate_transcript", [])
    for turn in debate:
        role = turn["role"]
        with st.chat_message("assistant"):
            st.markdown(f"**{role}**")
            st.write(turn["text"])

    st.divider()

    # ---------------- AI SUMMARY + SCORE ----------------
    col_sum, col_score = st.columns([3,1])

    with col_score:
        st.subheader("🤖 AI Score")
        st.metric("Final Score", result["final_score"])

    with col_sum:
        st.subheader("🧠 Debate Summary")
        st.info(result["debate_summary"])

    # pros cons
    w1, w2 = st.columns(2)

    with w1:
        st.subheader("✅ What Works")
        for item in result["what_works"]:
            st.write("•", item)

    with w2:
        st.subheader("❌ What Fails")
        for item in result["what_fails"]:
            st.write("•", item)

    st.divider()

    # ---------------- THEMES ----------------
    st.subheader("🏷 Themes")
    st.write(", ".join(result["themes"]))