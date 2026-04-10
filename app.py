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

    return {
        "title": data.get("Title"),
        "year": data.get("Year"),
        "plot": data.get("Plot"),
        "actors": data.get("Actors"),
        "genre": data.get("Genre"),
        "director": data.get("Director"),
        "imdb_rating": data.get("imdbRating"),
        "poster": data.get("Poster"),
        "runtime": data.get("Runtime"),
    }

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Movie Intelligence Terminal", layout="wide")

# ⭐ MAX WIDTH CONTAINER (fix stretched layout)
st.markdown("""
<style>
.block-container {
    max-width: 1100px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}
</style>
""", unsafe_allow_html=True)

# ---------------- GLOBAL CSS ----------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Playfair+Display:wght@700;900&display=swap');

html, body {
    background-color: #080b14 !important;
    color: #e8e8f0;
    font-family: 'Space Mono', monospace;
}

/* HEADER */
.eyebrow {
    font-size: 11px;
    letter-spacing: 6px;
    color: #7a7cff;
    text-transform: uppercase;
    text-align: center;
    margin-bottom: 8px;
}

.title {
    font-family: 'Playfair Display', serif;
    font-size: clamp(28px, 5vw, 56px);
    font-weight: 900;
    text-align: center;
    background: linear-gradient(90deg, #00ffe7 0%, #7a7cff 45%, #ff00c8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.subhead {
    font-size: 11px;
    color: rgba(255,255,255,0.3);
    letter-spacing: 3px;
    text-transform: uppercase;
    text-align: center;
}

/* GLASS CARD (improved readability) */
.glass {
    background: rgba(255,255,255,0.04);
    backdrop-filter: blur(16px);
    padding: 28px;
    border-radius: 20px;
    border: 1px solid rgba(255,255,255,0.08);
    font-size: 15px;
    line-height: 1.75;
    margin-bottom: 10px;
}

/* META */
.meta-label { font-size: 11px; opacity: 0.5; text-transform: uppercase; }
.meta-value { font-size: 15px; margin-bottom: 16px; }

/* VERDICT */
.verdict-text { font-size: 16px; line-height: 1.85; }

/* SECTION */
.section-label { font-size: 12px; letter-spacing: 3px; text-transform: uppercase; opacity: 0.5; }

</style>
""", unsafe_allow_html=True)

# ---------------- HERO HEADER ----------------
st.markdown("<div class='eyebrow'>[ SYSTEM ONLINE ]</div>", unsafe_allow_html=True)
st.markdown("<div class='title'>MOVIE INTELLIGENCE TERMINAL</div>", unsafe_allow_html=True)
st.markdown("<div class='subhead'>AI-Powered Cinematic Analysis</div>", unsafe_allow_html=True)

# ⭐ CENTERED SEARCH (Claude style landing)
st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)
c1,c2,c3 = st.columns([1,2,1])
with c2:
    user_input = st.chat_input("Search movie or TV show...")
st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)

# ---------------- MAIN APP ----------------
if user_input:

    movie = fetch_movie_data(user_input)

    if not movie:
        st.error("Movie not found")
        st.stop()

    col1, col2 = st.columns([1,2])
    with col1:
        st.image(movie["poster"], use_column_width=True)
    with col2:
        st.markdown(f"## {movie['title']} ({movie['year']})")
        st.markdown(f"<div class='meta-label'>Director</div><div class='meta-value'>{movie['director']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='meta-label'>Genre</div><div class='meta-value'>{movie['genre']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='meta-label'>Runtime</div><div class='meta-value'>{movie['runtime']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='meta-label'>Cast</div><div class='meta-value'>{movie['actors']}</div>", unsafe_allow_html=True)

    raw_reviews = {
        "title": movie["title"],
        "critic_reviews": movie["plot"],
        "audience_reactions": movie["actors"],
        "discussion_points": movie["genre"]
    }

    with st.spinner("AI Critics debating…"):
        result = analyze_movie(raw_reviews)

    st.write("---")
    st.markdown("### 🎬 Critics Panel")
    col1,col2,col3 = st.columns(3)

    col1.markdown(result["critic_expert"])
    col2.markdown(result["devils_advocate"])
    col3.markdown(result["audience_sentiment"])

    st.write("---")
    st.markdown("### 🎯 Themes")
    for t in result["themes"]:
        st.write("•", t)

    v = result["final_verdict"]

    st.write("---")
    st.markdown("### 🧠 Final Verdict")
    st.markdown(f"<div class='verdict-text'>{v['overview']}</div>", unsafe_allow_html=True)

    st.write("### ✅ What Works")
    for w in v["what_works"]:
        st.write("✔", w)

    st.write("### ❌ What Fails")
    for f in v["what_fails"]:
        st.write("✖", f)

    st.write("## 🎯 AI Score:", v["score"])