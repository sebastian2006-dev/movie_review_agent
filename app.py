import requests
import streamlit as st
import time
from agent.sentiment import analyze_movie

# ---------------- APP CONFIG ----------------
st.set_page_config(page_title="Movie Intelligence Terminal", layout="wide")

# ---------------- API KEY ----------------
OMDB_API_KEY = st.secrets["OMDB_API_KEY"]

# ---------------- RATE LIMIT PROTECTION ----------------
# Limits how often the AI can be called (protects Groq quota)
COOLDOWN_SECONDS = 20

def check_rate_limit():
    now = time.time()
    last_call = st.session_state.get("last_api_call", 0)

    if now - last_call < COOLDOWN_SECONDS:
        wait = int(COOLDOWN_SECONDS - (now - last_call))
        st.warning(f"⚠️ AI is cooling down to protect API limits. Try again in {wait}s.")
        st.stop()

    st.session_state["last_api_call"] = now


# ---------------- FETCH MOVIE DATA ----------------
def fetch_movie_data(title: str):
    if not OMDB_API_KEY:
        st.error("Missing OMDB_API_KEY in Streamlit secrets.")
        st.stop()

    url = "http://www.omdbapi.com/"
    params = {"t": title, "apikey": OMDB_API_KEY, "plot": "full", "r": "json"}

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


# ---------------- GLOBAL CSS ----------------
st.markdown("""
<style>
.stApp { background-color: #05070a !important; color: #e8e8f0; }
.block-container { max-width: 1200px; padding-top: 2rem; }

.critic-container {
    display:flex; gap:20px; flex-wrap:wrap; margin-top:20px;
}
.critic-card {
    flex:1; min-width:300px; padding:24px;
    background:rgba(255,255,255,0.03);
    border:1px solid rgba(255,255,255,0.08);
    border-radius:16px;
}
.verdict-box {
    background:rgba(0,255,231,0.05);
    border-left:4px solid #00ffe7;
    padding:20px;
    border-radius:0 12px 12px 0;
}
</style>
""", unsafe_allow_html=True)


# ---------------- HEADER ----------------
st.markdown("<h1 style='text-align:center;'>🎬 Cinematic Intelligence Terminal</h1>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# Centered search bar
c1, c2, c3 = st.columns([1,2,1])
with c2:
    user_input = st.chat_input("Search any movie or TV show...")

# ---------------- MAIN APP ----------------
if user_input:

    # 🔐 Rate limiter to prevent quota burn
    check_rate_limit()

    # Fetch OMDB data
    movie = fetch_movie_data(user_input)

    if not movie:
        st.error("Movie not found in OMDB database.")
        st.stop()

    # Poster + metadata
    col1, col2 = st.columns([1,2])
    with col1:
        st.image(movie["poster"], use_column_width=True)

    with col2:
        st.markdown(f"## {movie['title']} ({movie['year']})")
        st.write(f"**Director:** {movie['director']}")
        st.write(f"**Runtime:** {movie['runtime']}")
        st.write(f"**Cast:** {movie['actors']}")
        st.write(movie["plot"])

    # Prepare AI input
    raw_reviews = {
        "title": movie["title"],
        "critic_reviews": movie["plot"],
        "audience_reactions": movie["actors"],
        "discussion_points": movie["genre"]
    }

    # Call AI safely
    try:
        with st.spinner("🧠 AI Critics are analysing..."):
            result = analyze_movie(raw_reviews)
    except Exception as e:
        st.error("AI service temporarily busy. Please try again in a few seconds.")
        st.stop()

    # ---------------- AI PANELS ----------------
    st.write("---")
    st.markdown("## 🎬 Multi-Agent Perspectives")

    st.markdown(f"""
    <div class="critic-container">
        <div class="critic-card">
            <h4>Veteran Critic</h4>
            <p>{result["critic_expert"]}</p>
        </div>
        <div class="critic-card">
            <h4>Devil's Advocate</h4>
            <p>{result["devils_advocate"]}</p>
        </div>
        <div class="critic-card">
            <h4>Audience Voice</h4>
            <p>{result["audience_sentiment"]}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ---------------- THEMES + SCORE ----------------
    st.write("---")
    col1, col2 = st.columns([2,1])

    with col1:
        st.markdown("### 🎯 Themes")
        for t in result["themes"]:
            st.write("•", t)

    with col2:
        st.markdown("### ⭐ AI Rating")
        st.markdown(f"# {result['final_verdict']['score']}")

    # ---------------- FINAL VERDICT ----------------
    v = result["final_verdict"]

    st.write("---")
    st.markdown("## 🧠 Final Verdict")
    st.markdown(f"<div class='verdict-box'>{v['overview']}</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### ✅ What Works")
        for w in v["what_works"]:
            st.write("•", w)

    with col2:
        st.markdown("### ❌ What Fails")
        for f in v["what_fails"]:
            st.write("•", f)