import requests
import streamlit as st
from agent.sentiment import analyze_movie

# Replace with your actual secrets setup
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

    # Safe IMDb fallback if OMDB returns "N/A"
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
st.set_page_config(page_title="Movie Review Agent", layout="wide")

# ---------------- GLOBAL CSS ----------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Inter:wght@400;600&family=Playfair+Display:wght@700;900&display=swap');

.stApp { background-color: #05070a !important; color: #e8e8f0; }
.block-container { max-width: 1200px; padding-top: 2rem; }

/* IMPROVED SEARCH INPUT */
div[data-testid="stChatInput"] {
    border: 1px solid rgba(0, 255, 231, 0.2);
    border-radius: 15px;
    background: rgba(255, 255, 255, 0.02);
    padding: 5px;
}

/* HEADER TYPOGRAPHY */
.eyebrow {
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    letter-spacing: 5px;
    color: #00ffe7;
    text-align: center;
    opacity: 0.8;
}

.title {
    font-family: 'Playfair Display', serif;
    font-size: clamp(30px, 6vw, 50px);
    font-weight: 900;
    text-align: center;
    background: linear-gradient(135deg, #fff 30%, #444 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 40px;
}

/* HORIZONTAL CRITIC CARDS */
.critic-container { 
    display: flex; 
    gap: 20px; 
    flex-wrap: wrap; 
    margin-top: 20px;
}

.critic-card {
    flex: 1; 
    min-width: 300px;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px; 
    padding: 24px;
    transition: transform 0.3s ease;
}

.critic-card:hover {
    border-color: rgba(0, 255, 231, 0.3);
}

.critic-label {
    font-family: 'Space Mono', monospace; 
    font-size: 11px;
    text-transform: uppercase; 
    letter-spacing: 2px;
    margin-bottom: 12px;
}

.critic-text { 
    font-family: 'Inter', sans-serif; 
    font-size: 14px; 
    line-height: 1.6;
    color: #cbd5e1; 
}

/* COLOR ACCENTS */
.label-expert { color: #00ffe7; border-bottom: 1px solid rgba(0, 255, 231, 0.2); padding-bottom: 4px; }
.label-devils { color: #ff4b2b; border-bottom: 1px solid rgba(255, 75, 43, 0.2); padding-bottom: 4px; }
.label-audience { color: #ffcc00; border-bottom: 1px solid rgba(255, 204, 0, 0.2); padding-bottom: 4px; }

/* VERDICT STYLING */
.verdict-box {
    background: linear-gradient(to right, rgba(0, 255, 231, 0.05), transparent);
    border-left: 4px solid #00ffe7;
    padding: 20px;
    border-radius: 0 12px 12px 0;
    font-family: 'Inter', sans-serif;
}
</style>
""", unsafe_allow_html=True)

# ---------------- HERO HEADER ----------------
st.markdown("<div class='eyebrow'>QUANTUM ANALYSIS UNIT</div>", unsafe_allow_html=True)
st.markdown("<div class='title'>MOVIE REVIEW AGENT</div>", unsafe_allow_html=True)

# ---------------- CENTERED SEARCH ----------------
c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    user_input = st.chat_input("Search movie records...")
st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)

# ---------------- MAIN LOGIC ----------------
if user_input:
    movie = fetch_movie_data(user_input)

    if not movie:
        st.error("Protocol Error: Subject not found in database.")
        st.stop()

    # Display Movie Info
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image(movie["poster"], use_column_width=True)

    with col2:
        st.markdown(f"<h1 style='margin-bottom:0;'>{movie['title']}</h1>", unsafe_allow_html=True)
        st.markdown(
            f"<p style='color:grey; font-family:Space Mono; font-size:14px;'>"
            f"{movie['year']} // DIR: {movie['director']} // {movie['runtime']} // ⭐ IMDb {movie['imdb_rating']}"
            f"</p>",
            unsafe_allow_html=True
        )
        st.write(movie["plot"])
        st.markdown(f"**Cast:** {movie['actors']}")

    # Agent Processing
    raw_reviews = {
        "title": movie["title"],
        "critic_reviews": movie["plot"],
        "audience_reactions": movie["actors"],
        "discussion_points": movie["genre"]
    }

    with st.spinner("Synchronizing AI Personas..."):
        result = analyze_movie(raw_reviews)

    st.write("---")
    st.markdown("### 🎬 MULTI-AGENT PERSPECTIVES")

    # Horizontal Critics Panel
    st.markdown(f"""
    <div class="critic-container">
        <div class="critic-card">
            <div class="critic-label label-expert">Veteran Critic</div>
            <div class="critic-text">{result["critic_expert"]}</div>
        </div>
        <div class="critic-card">
            <div class="critic-label label-devils">Devil's Advocate</div>
            <div class="critic-text">{result["devils_advocate"]}</div>
        </div>
        <div class="critic-card">
            <div class="critic-label label-audience">Audience Sentiment</div>
            <div class="critic-text">{result["audience_sentiment"]}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.write("<br>", unsafe_allow_html=True)
    st.write("---")

    # Themes and Score Section
    t1, t2 = st.columns([2, 1])
    with t1:
        st.markdown("### 🎯 Core Themes")
        themes_html = " ".join([f"<span style='background:rgba(255,255,255,0.05); padding:6px 14px; border-radius:20px; border:1px solid rgba(255,255,255,0.1); margin-right:5px;'># {t}</span>" for t in result["themes"]])
        st.markdown(themes_html, unsafe_allow_html=True)

    with t2:
        st.markdown(f"<div style='text-align:right;'><p style='font-family:Space Mono; margin-bottom:0;'>AI SCORE</p><h1 style='color:#00ffe7; margin-top:0;'>{result['final_verdict']['score']}</h1></div>", unsafe_allow_html=True)

    # Final Verdict Section
    v = result["final_verdict"]
    st.markdown("### 🧠 Intelligence Verdict")
    st.markdown(f"<div class='verdict-box'>{v['overview']}</div>", unsafe_allow_html=True)

    st.write("<br>", unsafe_allow_html=True)
    w1, w2 = st.columns(2)
    with w1:
        st.write("### ✅ Strengths")
        for w in v["what_works"]:
            st.write(f"⁃ {w}")
    with w2:
        st.write("### ❌ Deficiencies")
        for f in v["what_fails"]:
            st.write(f"⁃ {f}")