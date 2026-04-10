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

    # ⭐ FIX: safe IMDb fallback if OMDB returns "N/A"
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
st.set_page_config(page_title="Movie Intelligence Terminal", layout="wide")

# ---------------- GLOBAL CSS ----------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Inter:wght@400;600&family=Playfair+Display:wght@700;900&display=swap');

.stApp { background-color: #05070a !important; color: #e8e8f0; }
.block-container { max-width: 1200px; padding-top: 2rem; }

div[data-testid="stChatInput"] {
    border: 1px solid rgba(0, 255, 231, 0.2);
    border-radius: 15px;
    background: rgba(255, 255, 255, 0.02);
    padding: 5px;
}

.eyebrow {
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    letter-spacing: 5px;
    color: #00ffe7;
    text-align: center;
}

.title {
    font-family: 'Playfair Display', serif;
    font-size: clamp(30px, 6vw, 50px);
    font-weight: 900;
    text-align: center;
    background: linear-gradient(135deg, #fff 30%, #444 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.critic-container { display:flex; gap:20px; flex-wrap:wrap; }
.critic-card {
    flex:1; min-width:300px;
    background: rgba(255,255,255,0.03);
    border:1px solid rgba(255,255,255,0.08);
    border-radius:16px; padding:24px;
}
.critic-label {
    font-family:'Space Mono'; font-size:11px;
    text-transform:uppercase; letter-spacing:2px;
    margin-bottom:12px;
}
.critic-text { font-family:'Inter'; font-size:14px; color:#cbd5e1; }

.label-expert{color:#00ffe7}
.label-devils{color:#ff4b2b}
.label-audience{color:#ffcc00}

.verdict-box {
    background: linear-gradient(to right, rgba(0,255,231,0.05), transparent);
    border-left: 4px solid #00ffe7;
    padding: 20px;
    border-radius: 0 12px 12px 0;
}
</style>
""", unsafe_allow_html=True)

# ---------------- HERO HEADER ----------------
st.markdown("<div class='eyebrow'>QUANTUM ANALYSIS UNIT</div>", unsafe_allow_html=True)
st.markdown("<div class='title'>CINEMATIC TERMINAL</div>", unsafe_allow_html=True)

# ⭐ CENTER SEARCH
st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)
c1,c2,c3 = st.columns([1,2,1])
with c2:
    user_input = st.chat_input("Access movie records...")
st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)

# ---------------- MAIN APP ----------------
if user_input:
    movie = fetch_movie_data(user_input)

    if not movie:
        st.error("Protocol Error: Subject not found in database.")
        st.stop()

    # ⭐ HEADER WITH IMDB RATING (NEW)
    col1, col2 = st.columns([1,2])
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

    st.write("---")
    t1, t2 = st.columns([2,1])

    with t1:
        st.markdown("### 🎯 Core Themes")
        themes_html = " ".join([f"<span style='background:rgba(255,255,255,0.05); padding:5px 12px; border-radius:20px;'># {t}</span>" for t in result["themes"]])
        st.markdown(themes_html, unsafe_allow_html=True)

    with t2:
        st.markdown(f"<h1 style='color:#00ffe7'>{result['final_verdict']['score']}</h1>", unsafe_allow_html=True)

    v = result["final_verdict"]
    st.markdown("### 🧠 Intelligence Verdict")
    st.markdown(f"<div class='verdict-box'>{v['overview']}</div>", unsafe_allow_html=True)

    w1, w2 = st.columns(2)
    with w1:
        st.write("### ✅ Strengths")
        for w in v["what_works"]:
            st.write(f"• {w}")
    with w2:
        st.write("### ❌ Deficiencies")
        for f in v["what_fails"]:
            st.write(f"• {f}")