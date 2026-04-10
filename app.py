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
        "poster": data.get("Poster"),
        "runtime": data.get("Runtime"),
    }

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Movie Intelligence Terminal", layout="wide")

# ---------------- GLOBAL CSS ----------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Playfair+Display:wght@700;900&display=swap');

html, body, [class*="css"] {
    background-color: #080b14 !important;
    color: #e8e8f0;
    font-family: 'Space Mono', monospace;
}

::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(120,100,255,0.4); border-radius: 4px; }

/* SCANLINES OVERLAY */
body::before {
    content: '';
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    pointer-events: none;
    background: repeating-linear-gradient(
        0deg, transparent, transparent 2px,
        rgba(0,0,0,0.03) 2px, rgba(0,0,0,0.03) 4px
    );
    z-index: 9999;
}

/* HEADER */
.eyebrow {
    font-size: 11px;
    letter-spacing: 6px;
    color: #7a7cff;
    text-transform: uppercase;
    text-align: center;
    animation: pulse 2.5s ease-in-out infinite;
    margin-bottom: 8px;
}
@keyframes pulse { 0%,100%{opacity:0.6} 50%{opacity:1} }

.title {
    font-family: 'Playfair Display', serif;
    font-size: clamp(28px, 5vw, 56px);
    font-weight: 900;
    text-align: center;
    line-height: 1.1;
    letter-spacing: -1px;
    background: linear-gradient(90deg, #00ffe7 0%, #7a7cff 45%, #ff00c8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 6px;
}

.subhead {
    font-size: 11px;
    color: rgba(255,255,255,0.25);
    letter-spacing: 3px;
    text-transform: uppercase;
    text-align: center;
    margin-bottom: 8px;
}

/* GLASS CARD */
.glass {
    background: rgba(255,255,255,0.04);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    padding: 24px;
    border-radius: 20px;
    border: 1px solid rgba(255,255,255,0.08);
    transition: transform 0.3s ease, border-color 0.3s;
    margin-bottom: 4px;
}
.glass:hover { transform: translateY(-5px); border-color: rgba(255,255,255,0.14); }

/* PERSONA ACCENT BORDERS */
.critic   { border-left: 4px solid #f5c518 !important; }
.devil    { border-left: 4px solid #c400ff !important; }
.audience { border-left: 4px solid #00ffa6 !important; }

/* PERSONA LABEL COLORS */
.critic-text   { color: #f5c518; font-size: 11px; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 10px; }
.devil-text    { color: #c400ff; font-size: 11px; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 10px; }
.audience-text { color: #00ffa6; font-size: 11px; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 10px; }

/* SCORE BADGES */
.score-pill-imdb {
    padding: 18px 16px;
    border-radius: 16px;
    text-align: center;
    background: rgba(245,197,24,0.1);
    border: 1px solid rgba(245,197,24,0.3);
}
.score-pill-ai {
    padding: 18px 16px;
    border-radius: 16px;
    text-align: center;
    background: rgba(122,124,255,0.1);
    border: 1px solid rgba(122,124,255,0.3);
}
.score-label { font-size: 10px; letter-spacing: 2px; text-transform: uppercase; color: rgba(255,255,255,0.4); margin-bottom: 6px; }
.score-value-imdb { font-size: 30px; font-weight: 700; color: #f5c518; font-family: 'Playfair Display', serif; }
.score-value-ai   { font-size: 30px; font-weight: 700; color: #7a7cff; font-family: 'Playfair Display', serif; }

/* MOVIE TITLE */
.movie-title {
    font-family: 'Playfair Display', serif;
    font-size: clamp(22px, 3vw, 36px);
    font-weight: 900;
    color: #fff;
    line-height: 1.15;
    margin-bottom: 4px;
}
.movie-year { font-size: 13px; color: #7a7cff; letter-spacing: 2px; margin-bottom: 18px; }

/* META LABELS */
.meta-label { font-size: 10px; color: rgba(255,255,255,0.35); letter-spacing: 2px; text-transform: uppercase; margin-bottom: 2px; }
.meta-value { font-size: 13px; color: rgba(255,255,255,0.85); margin-bottom: 14px; }

/* SECTION LABEL */
.section-label {
    font-size: 10px;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: rgba(255,255,255,0.35);
    margin-bottom: 16px;
}

/* CONFLICT CARD */
.conflict-wrap {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,100,100,0.15);
    border-radius: 20px;
    padding: 24px;
    margin-bottom: 8px;
    transition: transform 0.3s ease;
}
.conflict-wrap:hover { transform: translateY(-5px); }

.conflict-critic {
    padding: 16px;
    border-radius: 12px;
    background: rgba(245,197,24,0.07);
    border: 1px solid rgba(245,197,24,0.2);
    font-size: 13px;
    line-height: 1.6;
    color: rgba(255,255,255,0.8);
}
.conflict-devil {
    padding: 16px;
    border-radius: 12px;
    background: rgba(196,0,255,0.07);
    border: 1px solid rgba(196,0,255,0.2);
    font-size: 13px;
    line-height: 1.6;
    color: rgba(255,255,255,0.8);
}
.conflict-side-label { font-size: 10px; letter-spacing: 2px; text-transform: uppercase; opacity: 0.6; margin-bottom: 8px; }
.vs-text {
    font-family: 'Playfair Display', serif;
    font-weight: 900;
    font-size: 26px;
    color: rgba(255,255,255,0.12);
    text-align: center;
    padding: 8px 0;
}

/* THEME PILLS */
.theme-pill {
    display: inline-block;
    padding: 8px 18px;
    border-radius: 50px;
    font-size: 11px;
    letter-spacing: 1px;
    text-transform: uppercase;
    background: rgba(122,124,255,0.1);
    border: 1px solid rgba(122,124,255,0.3);
    color: #7a7cff;
    margin: 4px;
}

/* WORKS / FAILS */
.wf-title-works { font-size: 11px; letter-spacing: 2px; text-transform: uppercase; color: #00ffa6; margin-bottom: 12px; }
.wf-title-fails { font-size: 11px; letter-spacing: 2px; text-transform: uppercase; color: #ff5c7a; margin-bottom: 12px; }
.wf-item {
    font-size: 13px;
    color: rgba(255,255,255,0.75);
    padding: 8px 0;
    border-bottom: 1px solid rgba(255,255,255,0.05);
    line-height: 1.5;
}
.wf-item:last-child { border-bottom: none; }

/* VERDICT */
.verdict-label { font-size: 11px; letter-spacing: 2px; text-transform: uppercase; color: rgba(255,255,255,0.4); margin-bottom: 10px; }
.verdict-text  { font-size: 14px; color: rgba(255,255,255,0.8); line-height: 1.7; }

/* FINAL SCORE */
.final-score-wrap { text-align: center; padding: 36px 24px; }
.final-score-label { font-size: 11px; letter-spacing: 4px; text-transform: uppercase; color: rgba(255,255,255,0.3); margin-bottom: 10px; }
.final-score-value {
    font-family: 'Playfair Display', serif;
    font-size: 80px;
    font-weight: 900;
    background: linear-gradient(90deg, #00ffe7, #7a7cff, #ff00c8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1;
}

.center { text-align: center; }

/* Streamlit element overrides */
div[data-testid="stHorizontalBlock"] { gap: 16px; }
div[data-testid="column"] > div { height: 100%; }
</style>
""", unsafe_allow_html=True)

# ---------------- HERO HEADER ----------------
st.markdown("<div class='eyebrow'>[ SYSTEM ONLINE ]</div>", unsafe_allow_html=True)
st.markdown("<div class='title'>MOVIE INTELLIGENCE TERMINAL</div>", unsafe_allow_html=True)
st.markdown("<div class='subhead'>AI-Powered Cinematic Analysis</div>", unsafe_allow_html=True)
st.write("")

user_input = st.chat_input("Search movie or TV show...")

# ---------------- MAIN APP ----------------
if user_input:

    movie = fetch_movie_data(user_input)

    if not movie:
        st.error("Movie not found")
        st.stop()

    st.write("")

    # ---------- HERO POSTER + INFO ----------
    col1, col2 = st.columns([1, 2])

    with col1:
        st.image(movie["poster"], use_column_width=True)

    with col2:
        st.markdown(f"<div class='movie-title'>{movie['title']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='movie-year'>{movie['year']}</div>", unsafe_allow_html=True)

        st.markdown(f"<div class='meta-label'>Director</div><div class='meta-value'>{movie['director']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='meta-label'>Genre</div><div class='meta-value'>{movie['genre']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='meta-label'>Runtime</div><div class='meta-value'>{movie['runtime']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='meta-label'>Cast</div><div class='meta-value'>{movie['actors']}</div>", unsafe_allow_html=True)

    st.write("")

    raw_reviews = {
        "title": movie["title"],
        "critic_reviews": movie["plot"],
        "audience_reactions": f"Actors: {movie['actors']}",
        "discussion_points": movie["genre"]
    }

    with st.spinner("AI Critics debating…"):
        result = analyze_movie(raw_reviews)

    # ---------- SCORE BAR ----------
    colA, colB = st.columns(2)
    with colA:
        st.markdown(f"""
        <div class='score-pill-imdb'>
            <div class='score-label'>IMDB Rating</div>
            <div class='score-value-imdb'>⭐ {movie['imdb_rating']}</div>
        </div>""", unsafe_allow_html=True)
    with colB:
        st.markdown(f"""
        <div class='score-pill-ai'>
            <div class='score-label'>AI Consensus Score</div>
            <div class='score-value-ai'>🎯 {result['final_verdict']['score']}</div>
        </div>""", unsafe_allow_html=True)

    st.write("")
    st.write("")

    # ---------- PERSONA GRID ----------
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("<div class='glass critic'>", unsafe_allow_html=True)
        st.markdown("<div class='critic-text'>⚙ Veteran Critic</div>", unsafe_allow_html=True)
        st.write(result["critic_expert"])
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='glass devil'>", unsafe_allow_html=True)
        st.markdown("<div class='devil-text'>☿ Devil's Advocate</div>", unsafe_allow_html=True)
        st.write(result["devils_advocate"])
        st.markdown("</div>", unsafe_allow_html=True)

    with col3:
        st.markdown("<div class='glass audience'>", unsafe_allow_html=True)
        st.markdown("<div class='audience-text'>◎ Audience Voice</div>", unsafe_allow_html=True)
        st.write(result["audience_sentiment"])
        st.markdown("</div>", unsafe_allow_html=True)

    st.write("")

    # ---------- THE CONFLICT ----------
    st.markdown("""
    <div class='conflict-wrap'>
        <div class='section-label'>⚔ The Conflict</div>
    </div>
    """, unsafe_allow_html=True)

    conf_col1, conf_col2, conf_col3 = st.columns([5, 1, 5])

    with conf_col1:
        critic_text = result["critic_expert"]
        teaser = critic_text[:180] + "..." if len(critic_text) > 180 else critic_text
        st.markdown(f"""
        <div class='conflict-critic'>
            <div class='conflict-side-label' style='color:#f5c518'>Veteran Critic says</div>
            {teaser}
        </div>""", unsafe_allow_html=True)

    with conf_col2:
        st.markdown("<div class='vs-text'>VS</div>", unsafe_allow_html=True)

    with conf_col3:
        devil_text = result["devils_advocate"]
        teaser2 = devil_text[:180] + "..." if len(devil_text) > 180 else devil_text
        st.markdown(f"""
        <div class='conflict-devil'>
            <div class='conflict-side-label' style='color:#c400ff'>Devil's Advocate says</div>
            {teaser2}
        </div>""", unsafe_allow_html=True)

    st.write("")
    st.write("")

    # ---------- THEMES ----------
    st.markdown("<div class='section-label'>🎯 Core Themes</div>", unsafe_allow_html=True)
    theme_html = "".join([f"<span class='theme-pill'>{t}</span>" for t in result["themes"]])
    st.markdown(f"<div class='glass' style='padding:20px 24px'>{theme_html}</div>", unsafe_allow_html=True)

    st.write("")

    # ---------- FINAL VERDICT ----------
    v = result["final_verdict"]

    st.markdown("<div class='section-label'>🧠 Final Verdict</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"""
        <div class='glass'>
            <div class='verdict-label'>Overview</div>
            <div class='verdict-text'>{v['overview']}</div>
        </div>""", unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class='glass'>
            <div class='verdict-label'>Conclusion</div>
            <div class='verdict-text'>{v['conclusion']}</div>
        </div>""", unsafe_allow_html=True)

    st.write("")

    col1, col2 = st.columns(2)

    with col1:
        works_items = "".join([f"<div class='wf-item'>✔ {w}</div>" for w in v["what_works"]])
        st.markdown(f"""
        <div class='glass'>
            <div class='wf-title-works'>✅ What Works</div>
            {works_items}
        </div>""", unsafe_allow_html=True)

    with col2:
        fails_items = "".join([f"<div class='wf-item'>✖ {f}</div>" for f in v["what_fails"]])
        st.markdown(f"""
        <div class='glass'>
            <div class='wf-title-fails'>❌ What Fails</div>
            {fails_items}
        </div>""", unsafe_allow_html=True)

    st.write("")

    # ---------- FINAL SCORE ----------
    st.markdown(f"""
    <div class='glass final-score-wrap'>
        <div class='final-score-label'>AI Consensus Score</div>
        <div class='final-score-value'>{v['score']}</div>
    </div>""", unsafe_allow_html=True)