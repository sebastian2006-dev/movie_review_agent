import requests
import streamlit as st
from agent.sentiment import analyze_movie

# ---------------- CACHE LOGIC ----------------
@st.cache_data(ttl=3600)
def fetch_movie_data(title: str):
    API_KEY = st.secrets["OMDB_API_KEY"]
    if not API_KEY: raise ValueError("Missing OMDB_API_KEY.")
    url = "http://www.omdbapi.com/"
    params = {"t": title, "apikey": API_KEY, "plot": "full", "r": "json"}
    try:
        res = requests.get(url, params=params, timeout=10)
        data = res.json()
        if not data or data.get("Response") == "False": return None
        return {
            "title": data.get("Title"), "year": data.get("Year"), "plot": data.get("Plot"),
            "actors": data.get("Actors"), "genre": data.get("Genre"), "director": data.get("Director"),
            "imdb_rating": data.get("imdbRating") if data.get("imdbRating") != "N/A" else "—",
            "poster": data.get("Poster"), "runtime": data.get("Runtime"),
        }
    except: return None

@st.cache_data(show_spinner=False)
def get_ai_analysis(raw_reviews):
    return analyze_movie(raw_reviews)

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Movie Review Agent", layout="wide")

# ---------------- GLOBAL CSS (Dark Theme Only) ----------------
st.markdown("""
<style>
.stApp { background-color: #060b18 !important; color: #e8eaf6; font-family: 'DM Sans', sans-serif; }
.glass-card { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 20px; padding: 22px 24px; backdrop-filter: blur(16px); }
.hero-title { font-family: 'Syne', sans-serif; font-size: 50px; font-weight: 800; text-align: center; background: linear-gradient(135deg, #e8eaf6 0%, #a78bfa 50%, #06b6d4 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
div[data-testid="stChatInput"] textarea { background: rgba(255,255,255,0.03) !important; border: 1px solid rgba(124,58,237,0.4) !important; border-radius: 16px !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# ---------------- UI ----------------
st.markdown("<div class='hero-title'>Movie Review Agent</div>", unsafe_allow_html=True)

c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    user_input = st.chat_input("Search a movie title...")

if user_input:
    with st.spinner("Fetching database records..."):
        movie = fetch_movie_data(user_input)
    
    if not movie:
        st.error("Protocol Error: Subject not found.")
    else:
        # Display Movie Info
        col_p, col_i = st.columns([1, 2])
        with col_p: st.image(movie["poster"], use_column_width=True)
        with col_i:
            st.subheader(movie['title'])
            st.write(f"**Year:** {movie['year']} | **Director:** {movie['director']}")
            st.write(movie["plot"])

        # AI Analysis
        with st.spinner("Synchronizing AI Personas..."):
            result = get_ai_analysis({
                "title": movie["title"], "critic_reviews": movie["plot"],
                "audience_reactions": movie["actors"], "discussion_points": movie["genre"]
            })

        # Display Results
        st.markdown("### 🎬 Multi-Agent Perspectives")
        col1, col2, col3 = st.columns(3)
        cards = [("Veteran Critic", "🎓", result["critic_expert"]), 
                 ("Devil's Advocate", "😈", result["devils_advocate"]), 
                 ("Audience Sentiment", "🍿", result["audience_sentiment"])]
        
        for col, (title, icon, text) in zip([col1, col2, col3], cards):
            with col:
                st.markdown(f"<div class='glass-card'><b>{icon} {title}</b><br><br>{text[:150]}...</div>", unsafe_allow_html=True)
                with st.expander("Read Full Analysis"): st.write(text)