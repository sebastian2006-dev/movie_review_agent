import requests
import streamlit as st
from agent.sentiment import analyze_movie

# 1. SETUP PAGE
st.set_page_config(page_title="Movie Review Agent", layout="wide")

# 2. CACHING (Prevents re-running API calls/AI analysis on every UI refresh)
@st.cache_data(show_spinner=False)
def fetch_movie_data(title: str):
    API_KEY = st.secrets.get("OMDB_API_KEY")
    if not API_KEY: return None
    url = "http://www.omdbapi.com/"
    params = {"t": title, "apikey": API_KEY, "plot": "full", "r": "json"}
    try:
        res = requests.get(url, params=params, timeout=10)
        data = res.json()
        if not data or data.get("Response") == "False": return None
        return data
    except: return None

@st.cache_data(show_spinner=False)
def get_ai_analysis(title, plot, actors, genre):
    # Pass data as a dictionary to your agent
    return analyze_movie({
        "title": title,
        "critic_reviews": plot,
        "audience_reactions": actors,
        "discussion_points": genre
    })

# 3. CSS (Kept exactly as you designed)
st.markdown("""
<style>
.stApp { background-color: #060b18 !important; color: #e8eaf6; font-family: 'DM Sans', sans-serif; }
.hero-title { font-family: 'Syne', sans-serif; font-size: 50px; font-weight: 800; text-align: center; background: linear-gradient(135deg, #e8eaf6 0%, #a78bfa 50%, #06b6d4 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.glass-card { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 20px; padding: 22px 24px; }
</style>
""", unsafe_allow_html=True)

# 4. INTERFACE
st.markdown("<div class='hero-title'>Movie Review Agent</div>", unsafe_allow_html=True)

# USE A FORM: This stops the app from re-running until you click "Analyze"
with st.form("search_form"):
    user_input = st.text_input("Enter a movie title:", placeholder="e.g., Inception")
    submitted = st.form_submit_button("Analyze Movie")

# 5. EXECUTION
if submitted and user_input:
    with st.spinner("Fetching database records..."):
        movie = fetch_movie_data(user_input)
    
    if not movie:
        st.error("Protocol Error: Subject not found in database.")
    else:
        # Display Info
        col_p, col_i = st.columns([1, 2])
        with col_p: st.image(movie.get("Poster"), use_column_width=True)
        with col_i:
            st.subheader(movie.get('Title'))
            st.write(f"**Year:** {movie.get('Year')} | **Director:** {movie.get('Director')}")
            st.write(movie.get("Plot"))

        # Trigger AI Analysis
        with st.spinner("Synchronizing AI Personas..."):
            result = get_ai_analysis(movie.get('Title'), movie.get('Plot'), movie.get('Actors'), movie.get('Genre'))

        # Render Results
        st.markdown("### 🎬 Multi-Agent Perspectives")
        c1, c2, c3 = st.columns(3)
        
        # Display cards
        for col, (header, icon, content) in zip([c1, c2, c3], [
            ("Veteran Critic", "🎓", result["critic_expert"]),
            ("Devil's Advocate", "😈", result["devils_advocate"]),
            ("Audience Sentiment", "🍿", result["audience_sentiment"])
        ]):
            with col:
                st.markdown(f"<div class='glass-card'><b>{icon} {header}</b><br><br>{content[:150]}...</div>", unsafe_allow_html=True)
                with st.expander("Read Full Analysis"): st.write(content)