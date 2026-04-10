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

# ---------------- GLOBAL CSS & UI TWEAKS ----------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&family=Space+Mono:wght@400;700&family=Playfair+Display:wght@900&display=swap');

/* Main Background */
.stApp {
    background-color: #05070a;
    color: #e0e0e0;
}

.block-container {
    max-width: 1200px;
    padding-top: 2rem;
}

/* Header UI */
.eyebrow {
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    letter-spacing: 5px;
    color: #00ffe7;
    text-align: center;
    margin-bottom: 0px;
}

.title {
    font-family: 'Playfair Display', serif;
    font-size: clamp(30px, 6vw, 60px);
    text-align: center;
    background: linear-gradient(135deg, #fff 30%, #555 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0;
}

/* Critics Panel Cards */
.critic-card {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    padding: 20px;
    height: 100%;
    transition: transform 0.3s ease;
}

.critic-card:hover {
    border-color: rgba(255, 255, 255, 0.2);
    background: rgba(255, 255, 255, 0.05);
}

.label-expert { border-left: 4px solid #00ffe7; color: #00ffe7; }
.label-devils { border-left: 4px solid #ff4b2b; color: #ff4b2b; }
.label-audience { border-left: 4px solid #00ff87; color: #00ff87; }

.critic-header {
    font-family: 'Space Mono', monospace;
    font-weight: bold;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 15px;
    padding-left: 10px;
}

.critic-body {
    font-family: 'Inter', sans-serif;
    font-size: 14px;
    line-height: 1.6;
    color: #bcbcbc;
    max-width: 350px; /* Prevents text stretching */
}

/* Score Badge */
.score-box {
    background: linear-gradient(90deg, #00ffe7, #7a7cff);
    color: black;
    padding: 10px 20px;
    border-radius: 50px;
    font-weight: bold;
    display: inline-block;
    font-family: 'Space Mono', monospace;
}

</style>
""", unsafe_allow_html=True)

# ---------------- HERO HEADER ----------------
st.markdown("<div class='eyebrow'>ANALYSIS UNIT 01</div>", unsafe_allow_html=True)
st.markdown("<div class='title'>TERMINAL EVX</div>", unsafe_allow_html=True)

st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)
c1,c2,c3 = st.columns([1,3,1])
with c2:
    user_input = st.chat_input("Input Title (e.g. Inception, Dune)...")

# ---------------- MAIN APP ----------------
if user_input:
    movie = fetch_movie_data(user_input)

    if not movie:
        st.error("Access Denied: Movie not found in database.")
        st.stop()

    # Movie Poster & Metadata
    m1, m2 = st.columns([1, 2])
    with m1:
        st.image(movie["poster"], use_column_width=True)
    with m2:
        st.markdown(f"<h1 style='margin:0;'>{movie['title']}</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:grey; font-family:Space Mono;'>{movie['year']} | {movie['runtime']} | {movie['genre']}</p>", unsafe_allow_html=True)
        st.write(movie["plot"])
        st.markdown(f"**Director:** {movie['director']}")
        st.markdown(f"**Cast:** {movie['actors']}")

    raw_reviews = {
        "title": movie["title"],
        "critic_reviews": movie["plot"],
        "audience_reactions": movie["actors"],
        "discussion_points": movie["genre"]
    }

    with st.spinner("AI Agents Cross-Referencing..."):
        result = analyze_movie(raw_reviews)

    st.write("---")
    
    # 🎬 CRITICS PANEL (The Horizontal Redesign)
    st.markdown("### 🎬 MULTI-AGENT ANALYSIS")
    
    cp1, cp2, cp3 = st.columns(3)
    
    with cp1:
        st.markdown(f"""<div class='critic-card'>
            <div class='critic-header label-expert'>The Veteran Critic</div>
            <div class='critic-body'>{result["critic_expert"]}</div>
        </div>""", unsafe_allow_html=True)

    with cp2:
        st.markdown(f"""<div class='critic-card'>
            <div class='critic-header label-devils'>Devil's Advocate</div>
            <div class='critic-body'>{result["devils_advocate"]}</div>
        </div>""", unsafe_allow_html=True)

    with cp3:
        st.markdown(f"""<div class='critic-card'>
            <div class='critic-header label-audience'>Audience Logic</div>
            <div class='critic-body'>{result["audience_sentiment"]}</div>
        </div>""", unsafe_allow_html=True)

    st.write("---")
    
    # Bottom Sections
    v = result["final_verdict"]
    
    f1, f2 = st.columns(2)
    with f1:
        st.markdown("### 🧠 THE VERDICT")
        st.write(v['overview'])
        st.markdown(f"<div class='score-box'>SCORE: {v['score']}</div>", unsafe_allow_html=True)
    
    with f2:
        st.markdown("### 🎯 KEY THEMES")
        for t in result["themes"]:
            st.markdown(f"<code style='color:#00ffe7;'># {t}</code>", unsafe_allow_html=True)

    st.write("---")
    w1, w2 = st.columns(2)
    with w1:
        st.write("### ✅ What Works")
        for w in v["what_works"]:
            st.write("✔", w)
    with w2:
        st.write("### ❌ What Fails")
        for f in v["what_fails"]:
            st.write("✖", f)