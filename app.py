import requests
import streamlit as st
from agent.sentiment import analyze_movie

# Ensure this is the very first Streamlit command
st.set_page_config(page_title="CineVault — Intelligence Terminal", layout="wide", initial_sidebar_state="collapsed")

API_KEY = st.secrets.get("OMDB_API_KEY", "your_fallback_key")

# ---------------- FETCH MOVIE DATA ----------------
def fetch_movie_data(title: str):
    if not API_KEY:
        return None
    url = "http://www.omdbapi.com/"
    params = {"t": title, "apikey": API_KEY, "plot": "full", "r": "json"}
    try:
        res = requests.get(url, params=params, timeout=10)
        data = res.json()
        if not data or data.get("Response") == "False":
            return None
        
        imdb_rating = data.get("imdbRating")
        return {
            "title": data.get("Title"),
            "year": data.get("Year"),
            "plot": data.get("Plot"),
            "actors": data.get("Actors"),
            "genre": data.get("Genre"),
            "director": data.get("Director"),
            "imdb_rating": imdb_rating if imdb_rating != "N/A" else "—",
            "poster": data.get("Poster"),
            "runtime": data.get("Runtime"),
        }
    except:
        return None

# ---- DARK/LIGHT MODE STATE ----
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

# ---- THEME PALETTE ----
DM = st.session_state.dark_mode
if DM:
    BG, SURF, S2 = "#060912", "#0d1024", "#141729"
    P, SEC, ACC = "#ff5e62", "#4facfe", "#f9c846"
    TXT, SUB = "#eef0f8", "#7a839e"
    BRD, GP, GS = "rgba(255,255,255,0.07)", "rgba(255,94,98,0.25)", "rgba(79,172,254,0.25)"
else:
    BG, SURF, S2 = "#faf8f4", "#ffffff", "#f2ede4"
    P, SEC, ACC = "#c0392b", "#2980b9", "#d68910"
    TXT, SUB = "#1c1c2e", "#6c7a89"
    BRD, GP, GS = "rgba(0,0,0,0.09)", "rgba(192,57,43,0.12)", "rgba(41,128,185,0.12)"

# ====================================================================
# GLOBAL CSS (Fixed for Vibrancy)
# ====================================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700;900&family=DM+Sans:wght@400;500;700&family=JetBrains+Mono:wght@400;700&display=swap');

/* Hide Streamlit elements for a cleaner terminal look */
#MainMenu, footer, header {{visibility: hidden;}}
.stDeployButton {{display:none;}}

.stApp {{ 
    background-color: {BG} !important; 
    color: {TXT}; 
    transition: all 0.5s ease;
}}

/* ---- HERO HEADER ---- */
.hero-wrap {{ text-align: center; padding: 40px 0 20px; }}
.hero-eyebrow {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px; letter-spacing: 8px;
    color: {SEC}; text-transform: uppercase; margin-bottom: 10px;
    animation: fadeInDown 0.8s ease;
}}
.hero-title {{
    font-family: 'Cinzel', serif;
    font-size: clamp(40px, 8vw, 80px);
    font-weight: 900; line-height: 1;
    background: linear-gradient(120deg, {P} 10%, {ACC} 50%, {SEC} 90%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin-bottom: 15px;
    filter: drop-shadow(0 0 20px {GP});
}}

/* ---- INTERACTIVE CARDS ---- */
details.cv-card {{
    background: {SURF};
    border: 1px solid {BRD};
    border-radius: 20px;
    margin-bottom: 15px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}}
details.cv-card:hover {{
    transform: translateY(-5px) scale(1.01);
    box-shadow: 0 20px 40px rgba(0,0,0,0.4);
    border-color: {P};
}}

/* ---- VIBRANT POSTER ---- */
.poster-frame {{
    border-radius: 20px;
    overflow: hidden;
    box-shadow: 0 0 50px {GP};
    border: 2px solid {BRD};
    transition: all 0.5s ease;
}}
.poster-frame:hover {{
    transform: rotateY(10deg);
    box-shadow: 0 0 70px {P};
}}

/* Animations */
@keyframes fadeInDown {{
    from {{ opacity: 0; transform: translateY(-30px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}

/* Styling the Search Input to look like a Terminal */
div[data-baseweb="input"] {{
    background-color: {SURF} !important;
    border-radius: 50px !important;
    border: 2px solid {BRD} !important;
    padding: 5px 20px !important;
}}
div[data-baseweb="input"]:focus-within {{
    border-color: {SEC} !important;
    box-shadow: 0 0 25px {GS} !important;
}}
</style>
""", unsafe_allow_html=True)

# ---- TOP TOGGLE BAR ----
t1, t2 = st.columns([6, 1])
with t2:
    light_on = st.toggle("🌙 Mode", value=not st.session_state.dark_mode)
    if light_on != (not st.session_state.dark_mode):
        st.session_state.dark_mode = not light_on
        st.rerun()

# ====================================================================
# HERO SECTION
# ====================================================================
st.markdown(f"""
<div class="hero-wrap">
    <div class="hero-eyebrow">QUANTUM CINEMATIC ANALYSIS UNIT</div>
    <div class="hero-title">CINEVAULT</div>
    <div class="hero-sub" style="color:{SUB}; letter-spacing:4px;">// AI-POWERED MOVIE INTELLIGENCE //</div>
</div>
""", unsafe_allow_html=True)

# Search Bar centered
_, s_col, _ = st.columns([1, 2, 1])
with s_col:
    # Changed from chat_input to text_input for better UI placement
    user_input = st.text_input("", placeholder="Enter movie title and press Enter...", key="main_search")

# ====================================================================
# MAIN ANALYSIS LOGIC
# ====================================================================
if user_input:
    movie = fetch_movie_data(user_input)

    if not movie:
        st.error("⚠️ Protocol Error: Subject not found in database.")
    else:
        # Layout Results
        col1, col2 = st.columns([1, 1.8], gap="large")

        with col1:
            st.markdown(f'<div class="poster-frame"><img src="{movie["poster"]}" style="width:100%"></div>', unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <h1 style="font-family:'Cinzel'; font-size:45px; margin-bottom:0;">{movie["title"]}</h1>
            <div style="margin-bottom:20px;">
                <span style="color:{ACC}; font-family:'JetBrains Mono';">[{movie["year"]}]</span>
                <span style="color:{SEC}; margin-left:15px;">★ {movie["imdb_rating"]}</span>
            </div>
            <p style="font-size:18px; line-height:1.6; color:{SUB};">{movie["plot"]}</p>
            <div style="background:{S2}; padding:15px; border-radius:10px; border-left:4px solid {P};">
                <small style="color:{SEC}; font-family:'JetBrains Mono';">DIRECTED BY</small><br>
                <b>{movie["director"]}</b>
            </div>
            """, unsafe_allow_html=True)

        # AI Agent Section
        st.markdown(f'<div style="margin-top:40px; border-bottom:1px solid {BRD}; padding-bottom:10px; font-family:\'JetBrains Mono\'; letter-spacing:3px; color:{SEC};">AGENT NEURAL ANALYSIS</div>', unsafe_allow_html=True)
        
        with st.spinner("Synchronizing AI Personas..."):
            # Dummy result for structure - ensure analyze_movie returns this dict
            result = analyze_movie({"title": movie["title"], "plot": movie["plot"]})

        # Display Cards
        for label, content, color in [
            ("VETERAN CRITIC", result.get("critic_expert", ""), SEC),
            ("DEVIL'S ADVOCATE", result.get("devils_advocate", ""), P),
            ("AUDIENCE PULSE", result.get("audience_sentiment", ""), ACC)
        ]:
            st.markdown(f"""
            <details class="cv-card">
                <summary style="padding:20px; cursor:pointer; list-style:none; display:flex; justify-content:space-between; align-items:center;">
                    <span style="color:{color}; font-weight:bold; letter-spacing:2px;">{label}</span>
                    <span style="opacity:0.5; font-size:12px;">CLICK TO DECRYPT ▼</span>
                </summary>
                <div style="padding:0 20px 20px 20px; line-height:1.7; color:{SUB}; border-top:1px solid {BRD}; pt:10px;">
                    {content}
                </div>
            </details>
            """, unsafe_allow_html=True)

st.markdown(f"<div style='text-align:center; margin-top:100px; color:{SUB}; font-family:\"JetBrains Mono\"; font-size:10px;'>CINEVAULT v3.2 // ENCRYPTED TERMINAL</div>", unsafe_allow_html=True)