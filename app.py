import requests
import streamlit as st
from agent.sentiment import analyze_movie

API_KEY = st.secrets["OMDB_API_KEY"]

# ---------------- FETCH MOVIE DATA (UNCHANGED) ----------------
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

# ---- PAGE CONFIG ----
st.set_page_config(page_title="CineVault — Intelligence Terminal", layout="wide", initial_sidebar_state="collapsed")

# ---- DARK/LIGHT MODE STATE ----
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

# ---- TOP TOGGLE BAR ----
_gap1, _gap2, toggle_col = st.columns([5, 1, 1])
with toggle_col:
    light_on = st.toggle("☀️  Light", value=not st.session_state.dark_mode, key="theme_toggle")
    st.session_state.dark_mode = not light_on

DM = st.session_state.dark_mode

# ---- THEME PALETTE ----
if DM:
    BG    = "#060912"
    SURF  = "#0d1024"
    S2    = "#141729"
    P     = "#ff5e62"    # coral-red primary
    SEC   = "#4facfe"    # electric blue secondary
    ACC   = "#f9c846"    # warm gold accent
    TXT   = "#eef0f8"
    SUB   = "#7a839e"
    BRD   = "rgba(255,255,255,0.07)"
    GP    = "rgba(255,94,98,0.25)"
    GS    = "rgba(79,172,254,0.25)"
    LOADER_BG = "#060912"
else:
    BG    = "#faf8f4"
    SURF  = "#ffffff"
    S2    = "#f2ede4"
    P     = "#c0392b"
    SEC   = "#2980b9"
    ACC   = "#d68910"
    TXT   = "#1c1c2e"
    SUB   = "#6c7a89"
    BRD   = "rgba(0,0,0,0.09)"
    GP    = "rgba(192,57,43,0.12)"
    GS    = "rgba(41,128,185,0.12)"
    LOADER_BG = "#faf8f4"

# ====================================================================
# GLOBAL CSS
# ====================================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700;900&family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;1,400&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ---- BASE ---- */
.stApp {{ background-color: {BG} !important; color: {TXT}; transition: background 0.4s ease, color 0.4s ease; }}
.block-container {{ max-width: 1200px; padding-top: 0.5rem !important; }}
*, *::before, *::after {{ box-sizing: border-box; }}

/* ---- LOADING SCREEN ---- */
#cv-loader {{
    position: fixed; inset: 0;
    background: {LOADER_BG};
    z-index: 9999;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    gap: 28px;
    animation: loaderFadeOut 0.5s ease 2.2s forwards;
    pointer-events: none;
}}
.cv-loader-logo {{
    font-family: 'Cinzel', serif;
    font-size: 36px; font-weight: 900;
    background: linear-gradient(135deg, {P} 0%, {ACC} 50%, {SEC} 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
    animation: logoPulse 1.8s ease-in-out infinite;
}}
.cv-loader-track {{
    width: 260px; height: 3px;
    background: {BRD};
    border-radius: 2px;
    overflow: hidden;
}}
.cv-loader-bar {{
    height: 100%;
    background: linear-gradient(90deg, {P}, {ACC}, {SEC});
    border-radius: 2px;
    animation: loadBarFill 2s ease forwards;
}}
.cv-loader-text {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px; letter-spacing: 5px;
    color: {SUB}; text-transform: uppercase;
    animation: textBlink 1.2s ease-in-out infinite;
}}
.cv-loader-orb {{
    position: absolute;
    width: 300px; height: 300px;
    border-radius: 50%;
    background: radial-gradient(circle, {GP} 0%, transparent 70%);
    animation: orbFloat 3s ease-in-out infinite;
    pointer-events: none;
}}
@keyframes loadBarFill {{
    0%   {{ width: 0%; }}
    40%  {{ width: 55%; }}
    70%  {{ width: 78%; }}
    100% {{ width: 100%; }}
}}
@keyframes logoPulse {{ 0%,100% {{ opacity:.7; }} 50% {{ opacity:1; }} }}
@keyframes textBlink {{ 0%,100% {{ opacity:.3; }} 50% {{ opacity:.9; }} }}
@keyframes loaderFadeOut {{ to {{ opacity:0; visibility:hidden; }} }}
@keyframes orbFloat {{
    0%,100% {{ transform: translateY(0) scale(1); }}
    50%      {{ transform: translateY(-20px) scale(1.1); }}
}}

/* ---- HERO HEADER ---- */
.hero-wrap {{ text-align: center; padding: 20px 0 10px; }}
.hero-eyebrow {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; letter-spacing: 8px;
    color: {SEC}; text-transform: uppercase; margin-bottom: 10px;
    animation: heroIn 0.7s ease both;
}}
.hero-title {{
    font-family: 'Cinzel', serif;
    font-size: clamp(30px, 5vw, 58px);
    font-weight: 900; line-height: 1;
    background: linear-gradient(120deg, {P} 10%, {ACC} 50%, {SEC} 90%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 8px;
    animation: heroIn 0.7s ease 0.1s both;
}}
.hero-sub {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px; letter-spacing: 3px;
    color: {SUB};
    animation: heroIn 0.7s ease 0.2s both;
}}
@keyframes heroIn {{
    from {{ opacity:0; transform: translateY(-16px); }}
    to   {{ opacity:1; transform: translateY(0); }}
}}

/* ---- SEARCH BAR ---- */
div[data-testid="stChatInput"] > div {{
    background: {SURF} !important;
    border: none !important;
    border-radius: 60px !important;
    box-shadow:
        0 0 0 2px {P},
        0 0 28px {GP},
        0 0 60px {GS},
        0 8px 32px rgba(0,0,0,0.3) !important;
    transition: box-shadow 0.35s ease, transform 0.35s ease !important;
    padding: 6px 16px !important;
}}
div[data-testid="stChatInput"] > div:focus-within {{
    box-shadow:
        0 0 0 2.5px {SEC},
        0 0 40px {GS},
        0 0 80px {GP},
        0 12px 40px rgba(0,0,0,0.4) !important;
    transform: translateY(-2px) scale(1.01) !important;
}}
div[data-testid="stChatInput"] textarea,
div[data-testid="stChatInput"] input {{
    color: {TXT} !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 15px !important;
    background: transparent !important;
}}
div[data-testid="stChatInput"] textarea::placeholder,
div[data-testid="stChatInput"] input::placeholder {{
    color: {SUB} !important;
    font-style: italic;
}}

/* ---- MOVIE POSTER ---- */
.poster-frame {{
    border-radius: 18px; overflow: hidden;
    box-shadow: 0 24px 64px rgba(0,0,0,0.55), 0 0 0 1px {BRD};
    transition: transform 0.35s ease, box-shadow 0.35s ease;
}}
.poster-frame:hover {{
    transform: scale(1.03) rotate(-0.8deg);
    box-shadow: 0 32px 80px rgba(0,0,0,0.65), 0 0 0 2px {P}55;
}}

/* ---- MOVIE META ---- */
.movie-title-text {{
    font-family: 'Cinzel', serif;
    font-size: clamp(22px, 3.5vw, 40px);
    font-weight: 900; color: {TXT};
    margin: 0 0 10px; line-height: 1.1;
}}
.meta-row {{
    display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 18px;
}}
.chip {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px; padding: 5px 14px;
    border-radius: 30px; border: 1px solid {BRD};
    background: {S2}; color: {SUB};
    letter-spacing: 0.5px;
}}
.chip-imdb {{
    background: linear-gradient(135deg, {P}, {ACC});
    color: #fff; border: none;
    font-weight: 600; font-size: 12px;
    box-shadow: 0 4px 14px {GP};
}}
.plot-text {{
    font-family: 'DM Sans', sans-serif;
    font-size: 14px; line-height: 1.85;
    color: {SUB}; margin-bottom: 14px;
}}
.cast-text {{
    font-family: 'DM Sans', sans-serif;
    font-size: 13px; color: {SUB};
}}
.cast-text strong {{ color: {TXT}; }}

/* ---- SECTION HEADERS ---- */
.sec-header {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; letter-spacing: 5px; text-transform: uppercase;
    color: {SEC}; margin: 36px 0 16px;
    display: flex; align-items: center; gap: 14px;
}}
.sec-header::after {{
    content: ''; flex: 1; height: 1px;
    background: linear-gradient(to right, {SEC}44, transparent);
}}

/* ---- EXPANDABLE CRITIC CARDS ---- */
details.cv-card {{
    background: {SURF};
    border: 1px solid {BRD};
    border-radius: 20px;
    overflow: hidden;
    margin-bottom: 12px;
    transition: border-color 0.3s ease, box-shadow 0.3s ease, transform 0.3s ease;
    box-shadow: 0 4px 24px rgba(0,0,0,0.18);
}}
details.cv-card:hover {{
    border-color: {P}55;
    box-shadow: 0 8px 36px {GP};
    transform: translateY(-3px);
}}
details.cv-card[open] {{
    border-color: {SEC}66;
    box-shadow: 0 12px 48px {GS};
}}
summary.cv-card-head {{
    list-style: none; cursor: pointer;
    padding: 20px 24px;
    display: flex; align-items: center; justify-content: space-between;
    user-select: none;
    -webkit-user-select: none;
}}
summary.cv-card-head::-webkit-details-marker {{ display: none; }}
.cv-card-title {{
    display: flex; align-items: center; gap: 12px;
    font-family: 'DM Sans', sans-serif;
    font-weight: 600; font-size: 14px; color: {TXT};
}}
.cv-dot {{
    width: 10px; height: 10px; border-radius: 50%;
    flex-shrink: 0;
    box-shadow: 0 0 10px currentColor;
}}
.cv-badge {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px; letter-spacing: 3px;
    text-transform: uppercase; padding: 3px 10px;
    border-radius: 20px; border: 1px solid currentColor;
    opacity: 0.8;
}}
.cv-chevron {{
    font-size: 16px; color: {SUB};
    transition: transform 0.3s ease, color 0.3s ease;
    line-height: 1;
}}
details.cv-card[open] .cv-chevron {{
    transform: rotate(180deg);
    color: {SEC};
}}
.cv-card-body {{
    padding: 0 24px 24px;
    border-top: 1px solid {BRD};
    padding-top: 18px;
    font-family: 'DM Sans', sans-serif;
    font-size: 14px; line-height: 1.85; color: {SUB};
    animation: bodyReveal 0.3s ease both;
}}
.cv-unlock-hint {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; color: {SUB};
    opacity: 0.55; letter-spacing: 2px;
}}
details.cv-card[open] .cv-unlock-hint {{ display: none; }}
@keyframes bodyReveal {{
    from {{ opacity:0; transform: translateY(-8px); }}
    to   {{ opacity:1; transform: translateY(0); }}
}}

/* ---- VERDICT / SCORE ---- */
.verdict-wrap {{
    background: {SURF};
    border: 1px solid {BRD};
    border-radius: 24px;
    overflow: hidden;
    box-shadow: 0 12px 48px rgba(0,0,0,0.25);
    position: relative;
}}
.verdict-topbar {{
    height: 4px;
    background: linear-gradient(90deg, {P} 0%, {ACC} 50%, {SEC} 100%);
}}
.verdict-inner {{ padding: 28px 32px; }}
.score-num {{
    font-family: 'Cinzel', serif;
    font-size: 78px; font-weight: 900; line-height: 1;
    background: linear-gradient(135deg, {P}, {ACC});
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
}}
.verdict-overview {{
    font-family: 'DM Sans', sans-serif;
    font-size: 14px; line-height: 1.85;
    color: {SUB}; margin-top: 14px;
}}

/* ---- THEMES ---- */
.theme-pill {{
    display: inline-block;
    background: {S2};
    border: 1px solid {BRD};
    color: {TXT};
    padding: 8px 20px; border-radius: 40px;
    margin: 5px; font-size: 13px;
    font-family: 'DM Sans', sans-serif;
    cursor: default;
    transition: all 0.25s ease;
}}
.theme-pill:hover {{
    background: linear-gradient(135deg, {P}20, {SEC}20);
    border-color: {P}88;
    color: {P};
    transform: scale(1.07) translateY(-2px);
    box-shadow: 0 6px 20px {GP};
}}

/* ---- STRENGTHS / DEFICIENCIES EXPANDABLE ---- */
details.sw-item {{
    background: {SURF}; border: 1px solid {BRD};
    border-radius: 14px; overflow: hidden;
    margin-bottom: 8px;
    transition: all 0.25s ease;
}}
details.sw-item:hover {{ border-color: {ACC}55; transform: translateX(5px); }}
details.sw-item[open] {{ border-color: {ACC}88; }}
summary.sw-head {{
    list-style: none; cursor: pointer;
    padding: 13px 18px;
    display: flex; align-items: center; gap: 10px;
    font-family: 'DM Sans', sans-serif;
    font-weight: 500; font-size: 13px; color: {TXT};
    user-select: none; -webkit-user-select: none;
}}
summary.sw-head::-webkit-details-marker {{ display: none; }}
.sw-icon {{ font-size: 15px; flex-shrink: 0; }}
.sw-body {{
    padding: 0 18px 14px;
    border-top: 1px solid {BRD}; padding-top: 12px;
    font-family: 'DM Sans', sans-serif;
    font-size: 13px; line-height: 1.7; color: {SUB};
    animation: bodyReveal 0.25s ease both;
}}

/* ---- FLOATING SIDEBAR TABS ---- */
.cv-float-tabs {{
    position: fixed; top: 50%; right: 22px;
    transform: translateY(-50%);
    z-index: 1000;
    display: flex; flex-direction: column; gap: 10px;
}}
.cv-ftab {{
    width: 44px; height: 44px;
    background: {SURF};
    border: 1px solid {BRD};
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 19px; cursor: pointer;
    transition: all 0.2s ease;
    box-shadow: 0 4px 18px rgba(0,0,0,0.28);
    text-decoration: none !important;
    color: inherit !important;
    position: relative;
}}
.cv-ftab::before {{
    content: attr(data-tip);
    position: absolute;
    right: 54px;
    background: {SURF};
    border: 1px solid {BRD};
    padding: 5px 12px;
    border-radius: 8px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; letter-spacing: 1px;
    color: {TXT};
    white-space: nowrap;
    opacity: 0; pointer-events: none;
    transition: opacity 0.2s ease;
    box-shadow: 0 4px 16px rgba(0,0,0,0.2);
}}
.cv-ftab:hover::before {{ opacity: 1; }}
.cv-ftab:hover {{
    background: linear-gradient(135deg, {P}20, {SEC}20);
    border-color: {P}88;
    transform: scale(1.15) translateX(-5px);
    box-shadow: 0 6px 24px {GP};
}}

/* ---- TOGGLE STYLING ---- */
div[data-testid="stToggle"] > label {{
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 11px !important;
    letter-spacing: 1px !important;
    color: {SUB} !important;
}}

/* ---- STREAMLIT MISC ---- */
hr {{ border-color: {BRD} !important; margin: 28px 0 !important; }}
.stSpinner > div {{ color: {P} !important; }}
[data-testid="stSpinner"] div {{
    border-top-color: {P} !important;
}}
.stAlert {{ border-radius: 14px !important; font-family: 'DM Sans', sans-serif !important; }}

/* ---- CUSTOM SCROLLBAR ---- */
::-webkit-scrollbar {{ width: 5px; height: 5px; }}
::-webkit-scrollbar-track {{ background: {BG}; }}
::-webkit-scrollbar-thumb {{
    background: linear-gradient(180deg, {P}, {SEC});
    border-radius: 3px;
}}
::-webkit-scrollbar-thumb:hover {{ background: {ACC}; }}
</style>

<!-- LOADING SCREEN -->
<div id="cv-loader">
    <div class="cv-loader-orb"></div>
    <div class="cv-loader-logo">CINEVAULT</div>
    <div class="cv-loader-track"><div class="cv-loader-bar"></div></div>
    <div class="cv-loader-text">Booting Intelligence Matrix...</div>
</div>

<!-- FLOATING SIDEBAR TABS (rendered before content) -->
<div class="cv-float-tabs" id="cv-float-tabs" style="display:none;">
    <a class="cv-ftab" href="#movie-header" data-tip="OVERVIEW">🎬</a>
    <a class="cv-ftab" href="#ai-perspectives" data-tip="AI CRITICS">🤖</a>
    <a class="cv-ftab" href="#themes-section" data-tip="THEMES">🎯</a>
    <a class="cv-ftab" href="#verdict-section" data-tip="VERDICT">⚡</a>
    <a class="cv-ftab" href="#analysis-section" data-tip="ANALYSIS">📊</a>
</div>

<script>
// Show floating tabs once content loads
setTimeout(function() {{
    var tabs = document.getElementById('cv-float-tabs');
    if(tabs) tabs.style.display = 'flex';
}}, 2500);
</script>
""", unsafe_allow_html=True)

# ====================================================================
# HERO HEADER
# ====================================================================
st.markdown(f"""
<div class="hero-wrap" id="top">
    <div class="hero-eyebrow">QUANTUM CINEMATIC ANALYSIS UNIT</div>
    <div class="hero-title">CINEVAULT</div>
    <div class="hero-sub">// AI-POWERED MOVIE INTELLIGENCE //</div>
</div>
""", unsafe_allow_html=True)

# ====================================================================
# SEARCH BAR — CENTERED (position unchanged)
# ====================================================================
st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
_s1, _s2, _s3 = st.columns([1, 2, 1])
with _s2:
    user_input = st.chat_input("Search any movie title...")
st.markdown("<div style='height:36px'></div>", unsafe_allow_html=True)

# ====================================================================
# MAIN APP — unchanged logic, new UI
# ====================================================================
if user_input:

    movie = fetch_movie_data(user_input)

    if not movie:
        st.error("⚠️  Protocol Error: Subject not found in database.")
        st.stop()

    # ---- MOVIE HEADER ----
    st.markdown('<div id="movie-header"></div>', unsafe_allow_html=True)
    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown('<div class="poster-frame">', unsafe_allow_html=True)
        st.image(movie["poster"], use_column_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <h1 class="movie-title-text">{movie["title"]}</h1>
        <div class="meta-row">
            <span class="chip">{movie["year"]}</span>
            <span class="chip">🎬 {movie["director"]}</span>
            <span class="chip">⏱ {movie["runtime"]}</span>
            <span class="chip">🎭 {movie["genre"]}</span>
            <span class="chip chip-imdb">⭐ IMDb {movie["imdb_rating"]}</span>
        </div>
        <p class="plot-text">{movie["plot"]}</p>
        <p class="cast-text"><strong>Cast:</strong> {movie["actors"]}</p>
        """, unsafe_allow_html=True)

    # ---- PREPARE AI INPUT (unchanged) ----
    raw_reviews = {
        "title": movie["title"],
        "critic_reviews": movie["plot"],
        "audience_reactions": movie["actors"],
        "discussion_points": movie["genre"]
    }

    with st.spinner("⚡  Synchronizing AI Personas..."):
        result = analyze_movie(raw_reviews)

    # ---- AI PERSPECTIVES ----
    st.markdown(f"""
    <div class="sec-header" id="ai-perspectives">AI MULTI-AGENT PERSPECTIVES</div>
    <p style="font-family:'JetBrains Mono',monospace; font-size:11px; color:{SUB}; letter-spacing:2px; margin-bottom:18px;">
        CLICK EACH CARD TO UNLOCK THE FULL ANALYSIS
    </p>

    <details class="cv-card">
        <summary class="cv-card-head">
            <div class="cv-card-title">
                <span class="cv-dot" style="background:{SEC}; color:{SEC};"></span>
                <span style="color:{SEC};">VETERAN CRITIC</span>
                <span class="cv-badge" style="color:{SEC};">EXPERT LENS</span>
            </div>
            <div style="display:flex; align-items:center; gap:10px;">
                <span class="cv-unlock-hint">CLICK TO UNLOCK</span>
                <span class="cv-chevron">▾</span>
            </div>
        </summary>
        <div class="cv-card-body">{result["critic_expert"]}</div>
    </details>

    <details class="cv-card">
        <summary class="cv-card-head">
            <div class="cv-card-title">
                <span class="cv-dot" style="background:{P}; color:{P};"></span>
                <span style="color:{P};">DEVIL'S ADVOCATE</span>
                <span class="cv-badge" style="color:{P};">CONTRARIAN VIEW</span>
            </div>
            <div style="display:flex; align-items:center; gap:10px;">
                <span class="cv-unlock-hint">CLICK TO UNLOCK</span>
                <span class="cv-chevron">▾</span>
            </div>
        </summary>
        <div class="cv-card-body">{result["devils_advocate"]}</div>
    </details>

    <details class="cv-card">
        <summary class="cv-card-head">
            <div class="cv-card-title">
                <span class="cv-dot" style="background:{ACC}; color:{ACC};"></span>
                <span style="color:{ACC};">AUDIENCE PULSE</span>
                <span class="cv-badge" style="color:{ACC};">CROWD REACTION</span>
            </div>
            <div style="display:flex; align-items:center; gap:10px;">
                <span class="cv-unlock-hint">CLICK TO UNLOCK</span>
                <span class="cv-chevron">▾</span>
            </div>
        </summary>
        <div class="cv-card-body">{result["audience_sentiment"]}</div>
    </details>
    """, unsafe_allow_html=True)

    # ---- THEMES ----
    st.markdown(f'<div class="sec-header" id="themes-section">CORE THEMATIC ARCHITECTURE</div>', unsafe_allow_html=True)
    themes_html = " ".join([
        f'<span class="theme-pill">◈ {t}</span>'
        for t in result["themes"]
    ])
    st.markdown(themes_html, unsafe_allow_html=True)

    st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

    # ---- VERDICT ----
    v = result["final_verdict"]
    st.markdown(f'<div class="sec-header" id="verdict-section">INTELLIGENCE VERDICT</div>', unsafe_allow_html=True)

    vcol1, vcol2 = st.columns([1, 2])
    with vcol1:
        st.markdown(f"""
        <div class="verdict-wrap">
            <div class="verdict-topbar"></div>
            <div class="verdict-inner">
                <div style="font-family:'JetBrains Mono',monospace; font-size:10px; letter-spacing:4px; color:{SUB}; margin-bottom:6px;">FINAL SCORE</div>
                <div class="score-num">{v["score"]}</div>
                <div style="font-family:'DM Sans',sans-serif; font-size:12px; color:{SUB}; margin-top:8px; line-height:1.6;">{movie["title"]} · {movie["year"]}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with vcol2:
        st.markdown(f"""
        <div class="verdict-wrap">
            <div class="verdict-topbar"></div>
            <div class="verdict-inner">
                <div style="font-family:'JetBrains Mono',monospace; font-size:10px; letter-spacing:4px; color:{SUB}; margin-bottom:10px;">SYNOPSIS VERDICT</div>
                <div class="verdict-overview">{v["overview"]}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ---- STRENGTHS & DEFICIENCIES ----
    st.markdown(f'<div class="sec-header" id="analysis-section">DEEP ANALYSIS — CLICK TO EXPAND</div>', unsafe_allow_html=True)

    acol1, acol2 = st.columns(2)

    with acol1:
        st.markdown(f"""
        <div style="font-family:'JetBrains Mono',monospace; font-size:10px; letter-spacing:4px; color:{SEC}; margin-bottom:12px;">✅ STRENGTHS</div>
        """ + "".join([
            f"""<details class="sw-item">
                <summary class="sw-head">
                    <span class="sw-icon" style="color:{SEC};">◈</span>
                    <span>Strength {i+1}</span>
                </summary>
                <div class="sw-body">{w}</div>
            </details>"""
            for i, w in enumerate(v["what_works"])
        ]), unsafe_allow_html=True)

    with acol2:
        st.markdown(f"""
        <div style="font-family:'JetBrains Mono',monospace; font-size:10px; letter-spacing:4px; color:{P}; margin-bottom:12px;">❌ DEFICIENCIES</div>
        """ + "".join([
            f"""<details class="sw-item">
                <summary class="sw-head">
                    <span class="sw-icon" style="color:{P};">◈</span>
                    <span>Deficiency {i+1}</span>
                </summary>
                <div class="sw-body">{f}</div>
            </details>"""
            for i, f in enumerate(v["what_fails"])
        ]), unsafe_allow_html=True)

    st.markdown("<div style='height:60px'></div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="text-align:center; font-family:'JetBrains Mono',monospace; font-size:10px;
                letter-spacing:3px; color:{SUB}; padding: 20px 0;">
        CINEVAULT // POWERED BY AI MULTI-AGENT ANALYSIS
    </div>
    """, unsafe_allow_html=True)