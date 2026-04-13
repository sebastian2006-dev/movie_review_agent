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
st.set_page_config(page_title="Movie Review Agent", layout="wide", initial_sidebar_state="collapsed")

# ---------------- SESSION STATE INIT ----------------
if "dark_mode"     not in st.session_state: st.session_state.dark_mode     = True
if "cached_query"  not in st.session_state: st.session_state.cached_query  = None
if "cached_movie"  not in st.session_state: st.session_state.cached_movie  = None
if "cached_result" not in st.session_state: st.session_state.cached_result = None

is_dark = st.session_state.dark_mode

# ---------------- THEME VARIABLES ----------------
if is_dark:
    bg_base        = "#060b18"
    bg_card        = "rgba(255,255,255,0.04)"
    bg_card_hover  = "rgba(255,255,255,0.08)"
    border_color   = "rgba(255,255,255,0.08)"
    text_primary   = "#e8eaf6"
    text_secondary = "#8892b0"
    text_muted     = "#4a5568"
    accent1        = "#7c3aed"
    accent2        = "#06b6d4"
    accent3        = "#a855f7"
    glow1          = "rgba(124,58,237,0.35)"
    glow2          = "rgba(6,182,212,0.25)"
    verdict_bg     = "rgba(124,58,237,0.08)"
    verdict_border = "#7c3aed"
    error_bg       = "rgba(239,68,68,0.1)"
    error_border   = "#ef4444"
    tag_bg         = "rgba(124,58,237,0.15)"
    tag_border     = "rgba(124,58,237,0.4)"
    score_color    = "#06b6d4"
    score_glow     = "rgba(6,182,212,0.4)"
    header_gradient= "linear-gradient(135deg, #e8eaf6 0%, #a78bfa 50%, #06b6d4 100%)"
    eyebrow_color  = "#06b6d4"
    input_bg       = "rgba(255,255,255,0.03)"
    input_border   = "rgba(124,58,237,0.4)"
    input_glow     = "rgba(124,58,237,0.3)"
    meta_color     = "#64748b"
    toggle_bg      = "rgba(255,255,255,0.06)"
    toggle_border  = "rgba(255,255,255,0.1)"
    expander_bg    = "rgba(124,58,237,0.06)"
else:
    bg_base        = "#f0f4ff"
    bg_card        = "rgba(255,255,255,0.75)"
    bg_card_hover  = "rgba(255,255,255,0.95)"
    border_color   = "rgba(124,58,237,0.15)"
    text_primary   = "#1a1a2e"
    text_secondary = "#374151"
    text_muted     = "#9ca3af"
    accent1        = "#7c3aed"
    accent2        = "#0891b2"
    accent3        = "#9333ea"
    glow1          = "rgba(124,58,237,0.15)"
    glow2          = "rgba(8,145,178,0.15)"
    verdict_bg     = "rgba(124,58,237,0.05)"
    verdict_border = "#7c3aed"
    error_bg       = "rgba(239,68,68,0.08)"
    error_border   = "#ef4444"
    tag_bg         = "rgba(124,58,237,0.1)"
    tag_border     = "rgba(124,58,237,0.3)"
    score_color    = "#0891b2"
    score_glow     = "rgba(8,145,178,0.3)"
    header_gradient= "linear-gradient(135deg, #1a1a2e 0%, #7c3aed 60%, #0891b2 100%)"
    eyebrow_color  = "#7c3aed"
    input_bg       = "rgba(255,255,255,0.8)"
    input_border   = "rgba(124,58,237,0.5)"
    input_glow     = "rgba(124,58,237,0.2)"
    meta_color     = "#6b7280"
    toggle_bg      = "rgba(124,58,237,0.08)"
    toggle_border  = "rgba(124,58,237,0.2)"
    expander_bg    = "rgba(124,58,237,0.04)"

# ---------------- GLOBAL CSS ----------------
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&family=JetBrains+Mono:wght@400;700&display=swap');

/* ── Hide sidebar collapse button & default header ── */
[data-testid="stSidebarCollapsedControl"] {{ display: none !important; }}
header[data-testid="stHeader"] {{ background: transparent !important; }}
.stApp > header {{ display: none !important; }}

/* ── Base ── */
.stApp {{
    background-color: {bg_base} !important;
    color: {text_primary};
    font-family: 'DM Sans', sans-serif;
}}
.block-container {{
    max-width: 1180px;
    padding-top: 1.2rem;
    padding-bottom: 4rem;
}}

/* ── Mesh Background ── */
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
h1, h2, h3 {{ font-family: 'Syne', sans-serif !important; }}

/* ── Checkbox as toggle switch ── */
div[data-testid="stCheckbox"] {{
    display: flex !important;
    justify-content: flex-end !important;
}}
div[data-testid="stCheckbox"] label {{
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
    background: transparent !important;
    border: none !important;
    padding: 4px 0 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 11px !important;
    color: {text_secondary} !important;
    cursor: pointer !important;
    letter-spacing: 1px !important;
}}
div[data-testid="stCheckbox"] input[type="checkbox"] {{
    appearance: none !important;
    -webkit-appearance: none !important;
    width: 44px !important;
    height: 24px !important;
    border-radius: 100px !important;
    background: {"#7c3aed" if is_dark else "rgba(0,0,0,0.15)"} !important;
    border: none !important;
    position: relative !important;
    cursor: pointer !important;
    transition: background 0.3s ease !important;
    flex-shrink: 0 !important;
}}
div[data-testid="stCheckbox"] input[type="checkbox"]::after {{
    content: '' !important;
    position: absolute !important;
    top: 3px !important;
    left: {"22px" if is_dark else "3px"} !important;
    width: 18px !important;
    height: 18px !important;
    border-radius: 50% !important;
    background: white !important;
    transition: left 0.3s ease !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.3) !important;
}}

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
    font-size: 15px;
    color: {text_muted};
    text-align: center;
    margin-bottom: 32px;
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
    transition: box-shadow 0.3s ease, border-color 0.3s ease !important;
}}
div[data-testid="stChatInput"] textarea:focus {{
    box-shadow: 0 0 24px {input_glow}, 0 0 0 1px {input_border} !important;
    border-color: {accent1} !important;
    outline: none !important;
}}

/* ── Movie Meta ── */
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

/* ── Glass Cards ── */
.glass-card {{
    background: {bg_card};
    border: 1px solid {border_color};
    border-radius: 20px;
    padding: 22px 24px;
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    transition: transform 0.25s ease, box-shadow 0.25s ease, background 0.25s ease;
    box-sizing: border-box;
    margin-bottom: 8px;
}}
.glass-card:hover {{
    transform: translateY(-3px) scale(1.01);
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
    font-size: 14px;
    color: {text_secondary};
    line-height: 1.65;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
}}

/* ── Expander styled ── */
[data-testid="stExpander"] {{
    background: {expander_bg} !important;
    border: 1px solid {border_color} !important;
    border-radius: 12px !important;
    margin-top: 2px !important;
}}
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary p {{
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 11px !important;
    color: {accent1} !important;
    letter-spacing: 1px !important;
}}

/* ── Score pill ── */
.score-pill {{
    display: inline-flex;
    align-items: center;
    gap: 12px;
    background: rgba(6,182,212,0.07);
    border: 1px solid rgba(6,182,212,0.22);
    border-radius: 14px;
    padding: 12px 20px;
    margin-top: 4px;
}}
.score-label {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    letter-spacing: 2px;
    color: {meta_color};
    text-transform: uppercase;
}}
.score-value {{
    font-family: 'Syne', sans-serif;
    font-size: 26px;
    font-weight: 800;
    color: {score_color};
    text-shadow: 0 0 16px {score_glow};
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
.theme-tag:hover {{ background: rgba(124,58,237,0.25); }}

/* ── Section Heading ── */
.section-heading {{
    font-family: 'Syne', sans-serif;
    font-size: 17px;
    font-weight: 700;
    color: {text_primary};
    margin: 20px 0 14px 0;
    display: flex;
    align-items: center;
    gap: 8px;
}}

/* ── Verdict ── */
.verdict-box {{
    background: {verdict_bg};
    border-left: 3px solid {verdict_border};
    border-radius: 0 16px 16px 0;
    padding: 20px 24px;
    font-size: 14px;
    color: {text_secondary};
    line-height: 1.7;
}}

/* ── Points ── */
.point-item {{
    display: flex;
    align-items: flex-start;
    gap: 10px;
    font-size: 14px;
    color: {text_secondary};
    padding: 8px 0;
    border-bottom: 1px solid {border_color};
    line-height: 1.55;
}}
.dot-green {{ color: #34d399; font-size: 16px; }}
.dot-red   {{ color: #f87171; font-size: 16px; }}

/* ── Divider ── */
.fancy-divider {{
    height: 1px;
    background: linear-gradient(to right, transparent, {border_color}, transparent);
    margin: 28px 0;
}}

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

/* ── Poster ── */
[data-testid="stImage"] img {{
    border-radius: 16px !important;
    box-shadow: 0 20px 60px rgba(0,0,0,0.5) !important;
}}
</style>
""", unsafe_allow_html=True)

# ---------------- TOP-RIGHT THEME TOGGLE ----------------
_, tog_col = st.columns([8, 1])
with tog_col:
    st.checkbox(
        "🌙 Dark" if is_dark else "☀️ Light",
        value=is_dark,
        key="dark_mode",
    )

# ---------------- HERO HEADER ----------------
st.markdown("<div class='hero-eyebrow'>⬡ Multi-Agent Intelligence · Powered by AI</div>", unsafe_allow_html=True)
st.markdown("<div class='hero-title'>Movie Review Agent</div>", unsafe_allow_html=True)
st.markdown("<div class='hero-sub'>Ask about any film — get expert, contrarian, and audience perspectives.</div>", unsafe_allow_html=True)

# ── Centered Chat Input ──
c1, c2, c3 = st.columns([1, 2.5, 1])
with c2:
    user_input = st.chat_input("Search a movie title...")

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# ---------------- MAIN LOGIC ----------------
if user_input:
    query_key = user_input.strip().lower()
    if query_key != st.session_state.cached_query:
        st.session_state.cached_query  = query_key
        st.session_state.cached_movie  = fetch_movie_data(user_input)
        st.session_state.cached_result = None

        if st.session_state.cached_movie:
            raw_reviews = {
                "title":              st.session_state.cached_movie["title"],
                "critic_reviews":     st.session_state.cached_movie["plot"],
                "audience_reactions": st.session_state.cached_movie["actors"],
                "discussion_points":  st.session_state.cached_movie["genre"],
            }
            with st.spinner("Synchronizing AI personas..."):
                st.session_state.cached_result = analyze_movie(raw_reviews)

# ── Render from cache ──
movie  = st.session_state.cached_movie
result = st.session_state.cached_result

if movie is None and st.session_state.cached_query is not None:
    st.markdown(
        "<div class='err-box'>⚠ &nbsp; No results found for that title. Try a different spelling.</div>",
        unsafe_allow_html=True
    )

elif movie and result:

    # ── Movie Header ──
    col_poster, col_info = st.columns([1, 2.6], gap="large")

    with col_poster:
        if movie["poster"] and movie["poster"] != "N/A":
            st.image(movie["poster"], use_column_width=True)

    with col_info:
        st.markdown(f"<div class='movie-title-display'>{movie['title']}</div>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='movie-meta'>{movie['year']} &nbsp;·&nbsp; DIR: {movie['director']}"
            f" &nbsp;·&nbsp; {movie['runtime']} &nbsp;·&nbsp; ⭐ IMDb {movie['imdb_rating']}</div>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<p style='font-size:14px;color:{text_secondary};line-height:1.7;margin-top:12px;'>{movie['plot']}</p>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<p style='font-size:12px;color:{text_muted};font-family:JetBrains Mono,monospace;margin-top:6px;'>"
            f"CAST: {movie['actors']}</p>",
            unsafe_allow_html=True
        )

    st.markdown("<div class='fancy-divider'></div>", unsafe_allow_html=True)

    # ── Multi-Agent Perspectives ──
    st.markdown("<div class='section-heading'>🎬 &nbsp; Multi-Agent Perspectives</div>", unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns(3, gap="medium")

    def render_card(col, label_class, icon, label_text, full_text):
        preview = full_text[:200] + "…" if len(full_text) > 200 else full_text
        with col:
            st.markdown(f"""
            <div class="glass-card">
                <div class="card-label {label_class}">{icon} {label_text}</div>
                <div class="card-preview">{preview}</div>
            </div>
            """, unsafe_allow_html=True)
            with st.expander("▸ Read Analysis"):
                st.markdown(
                    f"<p style='font-size:14px;color:{text_secondary};line-height:1.7;'>{full_text}</p>",
                    unsafe_allow_html=True
                )

    render_card(col_a, "label-expert",   "🎓", "Veteran Critic",     result["critic_expert"])
    render_card(col_b, "label-devils",   "😈", "Devil's Advocate",   result["devils_advocate"])
    render_card(col_c, "label-audience", "🍿", "Audience Sentiment", result["audience_sentiment"])

    st.markdown("<div class='fancy-divider'></div>", unsafe_allow_html=True)

    # ── Themes + Score ──
    col_themes, col_score = st.columns([3, 1], gap="large")

    with col_themes:
        st.markdown("<div class='section-heading'>🏷 &nbsp; Core Themes</div>", unsafe_allow_html=True)
        tags_html = "".join([f"<span class='theme-tag'>#{t.strip()}</span>" for t in result["themes"]])
        st.markdown(f"<div style='line-height:2.2;'>{tags_html}</div>", unsafe_allow_html=True)

    with col_score:
        st.markdown("<div class='section-heading'>🎯 &nbsp; Score</div>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='score-pill'>"
            f"<span class='score-label'>Overall</span>"
            f"<span class='score-value'>{result['final_verdict']['score']}</span>"
            f"</div>",
            unsafe_allow_html=True
        )

    # ── Intelligence Verdict ──
    v = result["final_verdict"]
    st.markdown("<div class='section-heading'>🧠 &nbsp; Intelligence Verdict</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='verdict-box'>{v['overview']}</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

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