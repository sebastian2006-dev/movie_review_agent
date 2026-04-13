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

# ---------------- SESSION STATE INIT ----------------
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True
if "show_critic" not in st.session_state:
    st.session_state.show_critic = False
if "show_devil" not in st.session_state:
    st.session_state.show_devil = False
if "show_audience" not in st.session_state:
    st.session_state.show_audience = False

# ---------------- SIDEBAR THEME TOGGLE ----------------
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    theme_label = "🌙 Dark Mode" if st.session_state.dark_mode else "☀️ Light Mode"
    if st.toggle(theme_label, value=st.session_state.dark_mode):
        st.session_state.dark_mode = True
    else:
        st.session_state.dark_mode = False
    st.markdown("---")
    st.markdown(
        "<small style='color:grey;'>Movie Review Agent uses multi-agent AI to deliver expert, contrarian, and audience perspectives on any film.</small>",
        unsafe_allow_html=True
    )

is_dark = st.session_state.dark_mode

# ---------------- THEME VARIABLES ----------------
if is_dark:
    bg_base       = "#060b18"
    bg_card       = "rgba(255,255,255,0.04)"
    bg_card_hover = "rgba(255,255,255,0.08)"
    border_color  = "rgba(255,255,255,0.08)"
    text_primary  = "#e8eaf6"
    text_secondary= "#8892b0"
    text_muted    = "#4a5568"
    accent1       = "#7c3aed"   # vivid purple
    accent2       = "#06b6d4"   # electric teal
    accent3       = "#a855f7"   # violet
    glow1         = "rgba(124,58,237,0.35)"
    glow2         = "rgba(6,182,212,0.25)"
    verdict_bg    = "rgba(124,58,237,0.08)"
    verdict_border= "#7c3aed"
    error_bg      = "rgba(239,68,68,0.1)"
    error_border  = "#ef4444"
    tag_bg        = "rgba(124,58,237,0.15)"
    tag_border    = "rgba(124,58,237,0.4)"
    score_color   = "#06b6d4"
    header_gradient = "linear-gradient(135deg, #e8eaf6 0%, #a78bfa 50%, #06b6d4 100%)"
    eyebrow_color = "#06b6d4"
    input_bg      = "rgba(255,255,255,0.03)"
    input_border  = "rgba(124,58,237,0.4)"
    input_glow    = "rgba(124,58,237,0.3)"
    meta_color    = "#64748b"
    sidebar_bg    = "#0a1020"
else:
    bg_base       = "#f0f4ff"
    bg_card       = "rgba(255,255,255,0.75)"
    bg_card_hover = "rgba(255,255,255,0.95)"
    border_color  = "rgba(124,58,237,0.15)"
    text_primary  = "#1a1a2e"
    text_secondary= "#374151"
    text_muted    = "#9ca3af"
    accent1       = "#7c3aed"
    accent2       = "#0891b2"
    accent3       = "#9333ea"
    glow1         = "rgba(124,58,237,0.15)"
    glow2         = "rgba(8,145,178,0.15)"
    verdict_bg    = "rgba(124,58,237,0.05)"
    verdict_border= "#7c3aed"
    error_bg      = "rgba(239,68,68,0.08)"
    error_border  = "#ef4444"
    tag_bg        = "rgba(124,58,237,0.1)"
    tag_border    = "rgba(124,58,237,0.3)"
    score_color   = "#0891b2"
    header_gradient = "linear-gradient(135deg, #1a1a2e 0%, #7c3aed 60%, #0891b2 100%)"
    eyebrow_color = "#7c3aed"
    input_bg      = "rgba(255,255,255,0.8)"
    input_border  = "rgba(124,58,237,0.5)"
    input_glow    = "rgba(124,58,237,0.2)"
    meta_color    = "#6b7280"
    sidebar_bg    = "#e8eaf6"

# ---------------- GLOBAL CSS ----------------
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&family=JetBrains+Mono:wght@400;700&display=swap');

/* ── Base ── */
.stApp {{
    background-color: {bg_base} !important;
    color: {text_primary};
    font-family: 'DM Sans', sans-serif;
}}
.block-container {{
    max-width: 1180px;
    padding-top: 2.5rem;
    padding-bottom: 4rem;
}}

/* ── Sidebar ── */
[data-testid="stSidebar"] {{
    background: {sidebar_bg} !important;
    border-right: 1px solid {border_color};
}}

/* ── Animated Mesh Background ── */
.stApp::before {{
    content: '';
    position: fixed;
    inset: 0;
    z-index: -1;
    background:
        radial-gradient(ellipse 80% 60% at 20% 10%, {glow1} 0%, transparent 60%),
        radial-gradient(ellipse 60% 50% at 80% 80%, {glow2} 0%, transparent 55%),
        radial-gradient(ellipse 40% 40% at 50% 50%, rgba(168,85,247,0.06) 0%, transparent 70%);
    pointer-events: none;
}}

/* ── Typography ── */
h1, h2, h3, .syne {{ font-family: 'Syne', sans-serif !important; }}
code, .mono {{ font-family: 'JetBrains Mono', monospace !important; }}

/* ── Hero ── */
.hero-eyebrow {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    letter-spacing: 6px;
    color: {eyebrow_color};
    text-align: center;
    text-transform: uppercase;
    margin-bottom: 12px;
    opacity: 0.85;
}}
.hero-title {{
    font-family: 'Syne', sans-serif;
    font-size: clamp(34px, 6vw, 64px);
    font-weight: 800;
    text-align: center;
    background: {header_gradient};
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.1;
    margin-bottom: 6px;
}}
.hero-sub {{
    font-family: 'DM Sans', sans-serif;
    font-size: 15px;
    color: {text_muted};
    text-align: center;
    letter-spacing: 0.3px;
    margin-bottom: 36px;
}}

/* ── Chat Input ── */
div[data-testid="stChatInput"] textarea {{
    background: {input_bg} !important;
    border: 1px solid {input_border} !important;
    border-radius: 16px !important;
    color: {text_primary} !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 15px !important;
    padding: 16px 20px !important;
    backdrop-filter: blur(12px);
    box-shadow: 0 0 0 0 transparent;
    transition: box-shadow 0.3s ease, border-color 0.3s ease !important;
}}
div[data-testid="stChatInput"] textarea:focus {{
    box-shadow: 0 0 24px {input_glow}, 0 0 0 1px {input_border} !important;
    border-color: {accent1} !important;
    outline: none !important;
}}
div[data-testid="stChatInput"] {{
    border-radius: 18px !important;
    overflow: visible !important;
}}

/* ── Movie Meta Header ── */
.movie-meta {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    color: {meta_color};
    letter-spacing: 1.5px;
    margin-bottom: 12px;
}}
.movie-title-display {{
    font-family: 'Syne', sans-serif;
    font-size: clamp(24px, 4vw, 40px);
    font-weight: 800;
    color: {text_primary};
    margin-bottom: 6px;
}}

/* ── Glassmorphism Cards ── */
.glass-card {{
    background: {bg_card};
    border: 1px solid {border_color};
    border-radius: 20px;
    padding: 24px 26px;
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    transition: transform 0.25s ease, box-shadow 0.25s ease, background 0.25s ease;
    height: 100%;
    box-sizing: border-box;
}}
.glass-card:hover {{
    transform: translateY(-4px) scale(1.01);
    background: {bg_card_hover};
    box-shadow: 0 16px 48px {glow1};
}}

.card-label {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 8px;
}}
.card-label::after {{
    content: '';
    flex: 1;
    height: 1px;
    background: {border_color};
}}
.label-expert   {{ color: {accent2}; }}
.label-devils   {{ color: #f97316; }}
.label-audience {{ color: #facc15; }}

.card-preview {{
    font-family: 'DM Sans', sans-serif;
    font-size: 14px;
    color: {text_secondary};
    line-height: 1.65;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
}}
.card-full {{
    font-family: 'DM Sans', sans-serif;
    font-size: 14px;
    color: {text_secondary};
    line-height: 1.65;
}}

/* ── Verdict Box ── */
.verdict-box {{
    background: {verdict_bg};
    border-left: 3px solid {verdict_border};
    border-radius: 0 16px 16px 0;
    padding: 22px 26px;
    font-family: 'DM Sans', sans-serif;
    font-size: 15px;
    color: {text_secondary};
    line-height: 1.7;
    backdrop-filter: blur(10px);
}}

/* ── Score Display ── */
.score-ring {{
    font-family: 'Syne', sans-serif;
    font-size: 64px;
    font-weight: 800;
    color: {score_color};
    text-shadow: 0 0 30px {glow2};
    line-height: 1;
}}

/* ── Theme Tags ── */
.theme-tag {{
    display: inline-block;
    background: {tag_bg};
    border: 1px solid {tag_border};
    color: {accent3};
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    padding: 5px 14px;
    border-radius: 100px;
    margin: 4px 3px;
    letter-spacing: 0.5px;
    transition: background 0.2s;
}}
.theme-tag:hover {{
    background: rgba(124,58,237,0.25);
}}

/* ── Section Heading ── */
.section-heading {{
    font-family: 'Syne', sans-serif;
    font-size: 18px;
    font-weight: 700;
    color: {text_primary};
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 10px;
}}

/* ── Strength / Fail items ── */
.point-item {{
    display: flex;
    align-items: flex-start;
    gap: 10px;
    font-family: 'DM Sans', sans-serif;
    font-size: 14px;
    color: {text_secondary};
    padding: 8px 0;
    border-bottom: 1px solid {border_color};
    line-height: 1.55;
}}
.dot-green {{ color: #34d399; font-size: 18px; line-height: 1.2; }}
.dot-red   {{ color: #f87171; font-size: 18px; line-height: 1.2; }}

/* ── Error ── */
.err-box {{
    background: {error_bg};
    border: 1px solid {error_border};
    border-radius: 12px;
    padding: 18px 22px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    color: #f87171;
    text-align: center;
}}

/* ── Divider ── */
.fancy-divider {{
    height: 1px;
    background: linear-gradient(to right, transparent, {border_color}, transparent);
    margin: 36px 0;
}}

/* ── Poster ── */
.poster-wrap img {{
    border-radius: 16px !important;
    box-shadow: 0 20px 60px rgba(0,0,0,0.5), 0 0 0 1px {border_color} !important;
}}

/* ── Expander override ── */
[data-testid="stExpander"] {{
    background: transparent !important;
    border: none !important;
}}

/* ── Streamlit button style override ── */
.stButton > button {{
    background: transparent !important;
    border: 1px solid {input_border} !important;
    color: {accent1} !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 11px !important;
    letter-spacing: 1.5px !important;
    border-radius: 100px !important;
    padding: 4px 16px !important;
    transition: background 0.2s, box-shadow 0.2s !important;
}}
.stButton > button:hover {{
    background: rgba(124,58,237,0.12) !important;
    box-shadow: 0 0 14px {input_glow} !important;
}}
</style>
""", unsafe_allow_html=True)

# ---------------- HERO HEADER ----------------
st.markdown("<div class='hero-eyebrow'>⬡ Multi-Agent Intelligence · Powered by AI</div>", unsafe_allow_html=True)
st.markdown("<div class='hero-title'>Movie Review Agent</div>", unsafe_allow_html=True)
st.markdown("<div class='hero-sub'>Ask about any film — get expert, contrarian, and audience perspectives in seconds.</div>", unsafe_allow_html=True)

# ── Centered Chat Input ──
c1, c2, c3 = st.columns([1, 2.5, 1])
with c2:
    user_input = st.chat_input("Search a movie title...")

st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

# ---------------- MAIN APP ----------------
if user_input:
    # Reset expand states on new search
    st.session_state.show_critic   = False
    st.session_state.show_devil    = False
    st.session_state.show_audience = False

    movie = fetch_movie_data(user_input)

    if not movie:
        st.markdown(
            "<div class='err-box'>⚠ &nbsp; No results found for that title. Try a different spelling or year.</div>",
            unsafe_allow_html=True
        )
        st.stop()

    # ── Movie Header ──
    col_poster, col_info = st.columns([1, 2.6], gap="large")

    with col_poster:
        if movie["poster"] and movie["poster"] != "N/A":
            st.markdown("<div class='poster-wrap'>", unsafe_allow_html=True)
            st.image(movie["poster"], use_column_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

    with col_info:
        st.markdown(f"<div class='movie-title-display'>{movie['title']}</div>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='movie-meta'>"
            f"{movie['year']} &nbsp;·&nbsp; DIR: {movie['director']} &nbsp;·&nbsp; {movie['runtime']} &nbsp;·&nbsp; ⭐ IMDb {movie['imdb_rating']}"
            f"</div>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<p style='font-size:14px; color:{text_secondary}; line-height:1.7; margin-top:12px;'>{movie['plot']}</p>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<p style='font-size:13px; color:{text_muted}; font-family:JetBrains Mono,monospace; margin-top:8px;'>"
            f"CAST: {movie['actors']}</p>",
            unsafe_allow_html=True
        )

    # ── Prepare raw_reviews for analyze_movie (UNCHANGED) ──
    raw_reviews = {
        "title": movie["title"],
        "critic_reviews": movie["plot"],
        "audience_reactions": movie["actors"],
        "discussion_points": movie["genre"]
    }

    with st.spinner("Synchronizing AI personas..."):
        result = analyze_movie(raw_reviews)

    st.markdown("<div class='fancy-divider'></div>", unsafe_allow_html=True)

    # ── Section: Multi-Agent Perspectives ──
    st.markdown("<div class='section-heading'>🎬 &nbsp; Multi-Agent Perspectives</div>", unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns(3, gap="medium")

    def render_critic_card(col, label_class, label_icon, label_text, key, full_text):
        with col:
            preview = full_text[:220] + "..." if len(full_text) > 220 else full_text
            st.markdown(f"""
            <div class="glass-card">
                <div class="card-label {label_class}">{label_icon} {label_text}</div>
                <div class="card-preview">{preview}</div>
            </div>
            """, unsafe_allow_html=True)
            btn_label = "▾ Collapse" if st.session_state[key] else "▸ Read Analysis"
            if st.button(btn_label, key=f"btn_{key}"):
                st.session_state[key] = not st.session_state[key]
            if st.session_state[key]:
                with st.expander("Full Analysis", expanded=True):
                    st.markdown(
                        f"<div class='card-full'>{full_text}</div>",
                        unsafe_allow_html=True
                    )

    render_critic_card(
        col_a, "label-expert", "🎓", "Veteran Critic",
        "show_critic", result["critic_expert"]
    )
    render_critic_card(
        col_b, "label-devils", "😈", "Devil's Advocate",
        "show_devil", result["devils_advocate"]
    )
    render_critic_card(
        col_c, "label-audience", "🍿", "Audience Sentiment",
        "show_audience", result["audience_sentiment"]
    )

    st.markdown("<div class='fancy-divider'></div>", unsafe_allow_html=True)

    # ── Section: Verdict + Themes ──
    col_themes, col_score = st.columns([2.5, 1], gap="large")

    with col_themes:
        st.markdown("<div class='section-heading'>🏷 &nbsp; Core Themes</div>", unsafe_allow_html=True)
        tags_html = "".join([f"<span class='theme-tag'>#{t.strip()}</span>" for t in result["themes"]])
        st.markdown(f"<div style='line-height:2;'>{tags_html}</div>", unsafe_allow_html=True)

    with col_score:
        st.markdown("<div class='section-heading'>🎯 &nbsp; Score</div>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='score-ring'>{result['final_verdict']['score']}</div>",
            unsafe_allow_html=True
        )

    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

    # ── Section: Intelligence Verdict ──
    v = result["final_verdict"]
    st.markdown("<div class='section-heading'>🧠 &nbsp; Intelligence Verdict</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='verdict-box'>{v['overview']}</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    w1, w2 = st.columns(2, gap="large")

    with w1:
        st.markdown("<div class='section-heading'>✅ &nbsp; What Works</div>", unsafe_allow_html=True)
        for item in v["what_works"]:
            st.markdown(
                f"<div class='point-item'><span class='dot-green'>›</span>{item}</div>",
                unsafe_allow_html=True
            )

    with w2:
        st.markdown("<div class='section-heading'>❌ &nbsp; What Falls Short</div>", unsafe_allow_html=True)
        for item in v["what_fails"]:
            st.markdown(
                f"<div class='point-item'><span class='dot-red'>›</span>{item}</div>",
                unsafe_allow_html=True
            )