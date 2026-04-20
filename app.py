import re
import requests
import streamlit as st
from agent.sentiment import analyze_movie, MODEL_CRITIC, MODEL_ADVOCATE

API_KEY = st.secrets["OMDB_API_KEY"]


# ---------------- SEARCH MOVIES ----------------
def search_movies(query: str):
    """Search OMDB for multiple matching movies."""
    if not API_KEY:
        return []
    url = "http://www.omdbapi.com/"
    params = {"s": query, "apikey": API_KEY, "type": "movie", "r": "json"}
    try:
        res = requests.get(url, params=params, timeout=10)
        data = res.json()
    except Exception:
        return []
    if not data or data.get("Response") == "False":
        return []
    return data.get("Search", [])[:6]


# ---------------- FETCH MOVIE DATA BY IMDB ID ----------------
def fetch_movie_by_id(imdb_id: str):
    if not API_KEY:
        return None
    url = "http://www.omdbapi.com/"
    params = {"i": imdb_id, "apikey": API_KEY, "plot": "full", "r": "json"}
    try:
        res = requests.get(url, params=params, timeout=10)
        data = res.json()
    except Exception:
        return None
    if not data or data.get("Response") == "False":
        return None

    imdb_rating = data.get("imdbRating", "—")
    if not imdb_rating or imdb_rating == "N/A":
        imdb_rating = "—"

    rt_rating = "—"
    for r in data.get("Ratings", []):
        if r.get("Source") == "Rotten Tomatoes":
            rt_rating = r.get("Value", "—")
            break

    return {
        "title":       data.get("Title"),
        "year":        data.get("Year"),
        "plot":        data.get("Plot"),
        "actors":      data.get("Actors"),
        "genre":       data.get("Genre"),
        "director":    data.get("Director"),
        "imdb_rating": imdb_rating,
        "rt_rating":   rt_rating,
        "poster":      data.get("Poster"),
        "runtime":     data.get("Runtime"),
    }


# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Movie Review Agent",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------- SESSION STATE ----------------
if "light_mode"       not in st.session_state: st.session_state.light_mode       = True
if "cached_query"     not in st.session_state: st.session_state.cached_query     = None
if "cached_movie"     not in st.session_state: st.session_state.cached_movie     = None
if "cached_result"    not in st.session_state: st.session_state.cached_result    = None
if "search_results"   not in st.session_state: st.session_state.search_results   = []
if "selected_imdb_id" not in st.session_state: st.session_state.selected_imdb_id = None
if "last_typed"       not in st.session_state: st.session_state.last_typed       = None

is_dark = not st.session_state.light_mode

# ---------------- THEME VARIABLES ----------------
if is_dark:
    bg_base               = "#060b18"
    bg_card               = "rgba(255,255,255,0.04)"
    bg_card_hover         = "rgba(255,255,255,0.08)"
    border_color          = "rgba(255,255,255,0.08)"
    text_primary          = "#f0f4ff"
    text_secondary        = "#c8d0e8"
    text_muted            = "#7a85a0"
    accent1               = "#9b6fff"
    accent2               = "#22d3ee"
    accent3               = "#c084fc"
    glow1                 = "rgba(124,58,237,0.35)"
    glow2                 = "rgba(6,182,212,0.25)"
    glow3                 = "rgba(168,85,247,0.06)"
    verdict_bg            = "rgba(124,58,237,0.08)"
    verdict_border        = "#9b6fff"
    error_bg              = "rgba(239,68,68,0.1)"
    error_border          = "#ef4444"
    tag_bg                = "rgba(124,58,237,0.15)"
    tag_border            = "rgba(124,58,237,0.4)"
    score_color           = "#22d3ee"
    score_glow            = "rgba(34,211,238,0.5)"
    score_bg              = "rgba(6,182,212,0.07)"
    score_border          = "rgba(6,182,212,0.22)"
    header_gradient       = "linear-gradient(135deg, #f0f4ff 0%, #c084fc 50%, #22d3ee 100%)"
    eyebrow_color         = "#22d3ee"
    input_border          = "rgba(155,111,255,0.5)"
    input_glow            = "rgba(155,111,255,0.3)"
    meta_color            = "#8892b0"
    expander_bg           = "rgba(124,58,237,0.06)"
    chatinput_bg          = "rgba(255,255,255,0.04)"
    chatinput_text        = "#f0f4ff"
    chatinput_placeholder = "#6a7590"
    btn_bg                = "linear-gradient(135deg, #7c3aed, #06b6d4)"
    btn_hover_bg          = "linear-gradient(135deg, #6d28d9, #0891b2)"
    btn_shadow            = "rgba(124,58,237,0.45)"
    critic_color          = "#22d3ee"
    critic_bg             = "rgba(6,182,212,0.07)"
    critic_border         = "rgba(6,182,212,0.2)"
    advocate_color        = "#f97316"
    advocate_bg           = "rgba(249,115,22,0.07)"
    advocate_border       = "rgba(249,115,22,0.2)"
    card_overlay_bg       = "linear-gradient(to top, rgba(6,11,24,0.97) 0%, rgba(6,11,24,0.5) 50%, transparent 100%)"
    card_bg_empty         = "rgba(255,255,255,0.05)"
    card_hover_border     = "#9b6fff"
    search_section_bg     = "rgba(255,255,255,0.02)"
    search_section_border = "rgba(255,255,255,0.06)"
    # Ring chart colors
    ai_ring_color         = "#22d3ee"
    ai_ring_glow          = "rgba(34,211,238,0.5)"
    ai_ring_bg            = "rgba(6,182,212,0.15)"
    ai_text_color         = "#22d3ee"
else:
    bg_base               = "#fdfbf7"
    bg_card               = "rgba(255,255,255,0.85)"
    bg_card_hover         = "rgba(255,255,255,1)"
    border_color          = "rgba(217,119,54,0.15)"
    text_primary          = "#2c2421"
    text_secondary        = "#4a3f3c"
    text_muted            = "#7a6b68"
    accent1               = "#d97736"
    accent2               = "#4a7c59"
    accent3               = "#c4554b"
    glow1                 = "rgba(217,119,54,0.12)"
    glow2                 = "rgba(196,85,75,0.12)"
    glow3                 = "rgba(217,119,54,0.06)"
    verdict_bg            = "rgba(217,119,54,0.06)"
    verdict_border        = "#d97736"
    error_bg              = "rgba(220,38,38,0.06)"
    error_border          = "#dc2626"
    tag_bg                = "rgba(217,119,54,0.08)"
    tag_border            = "rgba(217,119,54,0.25)"
    score_color           = "#c4554b"
    score_glow            = "rgba(196,85,75,0.15)"
    score_bg              = "rgba(196,85,75,0.07)"
    score_border          = "rgba(196,85,75,0.22)"
    header_gradient       = "linear-gradient(135deg, #2c2421 0%, #d97736 60%, #c4554b 100%)"
    eyebrow_color         = "#d97736"
    input_border          = "#2c2421"
    input_glow            = "rgba(44,36,33,0.25)"
    meta_color            = "#665a58"
    expander_bg           = "rgba(255,255,255,0.7)"
    chatinput_bg          = "#2c2421"
    chatinput_text        = "#ffffff"
    chatinput_placeholder = "rgba(255,255,255,0.6)"
    btn_bg                = "linear-gradient(135deg, #d97736, #c4554b)"
    btn_hover_bg          = "linear-gradient(135deg, #c4554b, #a34139)"
    btn_shadow            = "rgba(217,119,54,0.2)"
    critic_color          = "#4a7c59"
    critic_bg             = "rgba(74,124,89,0.07)"
    critic_border         = "rgba(74,124,89,0.2)"
    advocate_color        = "#d97736"
    advocate_bg           = "rgba(217,119,54,0.07)"
    advocate_border       = "rgba(217,119,54,0.2)"
    card_overlay_bg       = "linear-gradient(to top, rgba(44,36,33,0.97) 0%, rgba(44,36,33,0.5) 50%, transparent 100%)"
    card_bg_empty         = "rgba(217,119,54,0.06)"
    card_hover_border     = "#d97736"
    search_section_bg     = "rgba(217,119,54,0.03)"
    search_section_border = "rgba(217,119,54,0.1)"
    # Ring chart colors
    ai_ring_color         = "#c4554b"
    ai_ring_glow          = "rgba(196,85,75,0.5)"
    ai_ring_bg            = "rgba(196,85,75,0.15)"
    ai_text_color         = "#c4554b"

# ---------------- GLOBAL CSS ----------------
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&family=JetBrains+Mono:wght@400;700&display=swap');

[data-testid="stSidebarCollapsedControl"] {{ display: none !important; }}
header[data-testid="stHeader"] {{ background: transparent !important; }}
.stApp > header {{ display: none !important; }}

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
.stApp::before {{
    content: '';
    position: fixed;
    inset: 0;
    z-index: -1;
    background:
        radial-gradient(ellipse 80% 60% at 20% 10%, {glow1} 0%, transparent 60%),
        radial-gradient(ellipse 60% 50% at 80% 80%, {glow2} 0%, transparent 55%),
        radial-gradient(ellipse 40% 40% at 50% 50%, {glow3} 0%, transparent 70%);
    pointer-events: none;
}}
h1, h2, h3 {{ font-family: 'Syne', sans-serif !important; }}

/* ── Hero ── */
.hero-eyebrow {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    letter-spacing: 5px;
    color: {eyebrow_color};
    text-align: center;
    text-transform: uppercase;
    margin-bottom: 12px;
    opacity: 1;
}}
.hero-title {{
    font-family: 'Syne', sans-serif;
    font-size: clamp(38px, 6vw, 68px);
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
    font-size: 17px;
    color: {text_muted};
    text-align: center;
    margin-bottom: 32px;
}}

/* ── Chat Input ── */
div[data-testid="stChatInput"],
.stChatInput {{
    background: {chatinput_bg} !important;
    border: 1px solid {input_border} !important;
    border-radius: 16px !important;
    box-shadow: none !important;
    padding-right: 6px !important;
    padding-left: 6px !important;
}}
div[data-testid="stChatInput"] > div,
.stChatInput > div {{
    background: {chatinput_bg} !important;
    border: none !important;
    border-radius: 16px !important;
}}
textarea[data-testid="stChatInputTextArea"],
div[data-testid="stChatInput"] textarea,
.stChatInput textarea {{
    background: transparent !important;
    border: none !important;
    color: {chatinput_text} !important;
    -webkit-text-fill-color: {chatinput_text} !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 16px !important;
    padding: 16px 20px !important;
    box-shadow: none !important;
    outline: none !important;
    caret-color: {accent1} !important;
}}
textarea[data-testid="stChatInputTextArea"]::placeholder,
div[data-testid="stChatInput"] textarea::placeholder,
.stChatInput textarea::placeholder {{
    color: {chatinput_placeholder} !important;
    -webkit-text-fill-color: {chatinput_placeholder} !important;
}}
textarea[data-testid="stChatInputTextArea"]:focus,
div[data-testid="stChatInput"] textarea:focus,
.stChatInput textarea:focus {{
    box-shadow: none !important; outline: none !important; border: none !important;
}}
div[data-testid="stChatInput"]:focus-within,
.stChatInput:focus-within {{
    border-color: {accent1} !important;
    box-shadow: 0 0 20px {input_glow} !important;
}}

/* ── Send Button ── */
button[data-testid="stChatInputSubmitButton"],
div[data-testid="stChatInput"] button,
.stChatInput button {{
    background: {btn_bg} !important;
    border: none !important;
    border-radius: 10px !important;
    width: 36px !important;
    height: 36px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    cursor: pointer !important;
    box-shadow: 0 4px 14px {btn_shadow} !important;
    transition: all 0.2s ease !important;
    flex-shrink: 0 !important;
    margin-top: 6px !important;
}}
button[data-testid="stChatInputSubmitButton"]:hover,
div[data-testid="stChatInput"] button:hover,
.stChatInput button:hover {{
    background: {btn_hover_bg} !important;
    box-shadow: 0 6px 20px {btn_shadow} !important;
    transform: scale(1.06) !important;
}}
button[data-testid="stChatInputSubmitButton"] svg,
div[data-testid="stChatInput"] button svg,
.stChatInput button svg {{
    stroke: #ffffff !important;
    fill: none !important;
    width: 16px !important;
    height: 16px !important;
}}

/* ── Netflix Search Cards ── */
.search-section-label {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: {eyebrow_color};
    margin-bottom: 16px;
    margin-top: 8px;
}}
.movie-card-wrap {{
    position: relative;
    border-radius: 12px;
    overflow: hidden;
    background: {card_bg_empty};
    border: 1px solid {border_color};
    transition: all 0.25s ease;
    cursor: pointer;
    aspect-ratio: 2/3;
    display: flex;
    flex-direction: column;
}}
.movie-card-wrap:hover {{
    border-color: {card_hover_border};
    transform: scale(1.04);
    box-shadow: 0 12px 40px rgba(0,0,0,0.4);
}}
.movie-card-wrap img {{
    position: absolute;
    top: 0; left: 0; bottom: 0; right: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
    border-radius: 12px;
}}
.movie-card-overlay {{
    position: absolute;
    bottom: 0; left: 0; right: 0;
    background: {card_overlay_bg};
    padding: 16px 10px 12px;
    border-radius: 0 0 12px 12px;
}}
.card-title-text {{
    font-family: 'Syne', sans-serif;
    font-size: 13px;
    font-weight: 700;
    color: #ffffff;
    margin: 0 0 2px 0;
    line-height: 1.3;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}}
.card-year-text {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    color: rgba(255,255,255,0.6);
    letter-spacing: 1px;
}}
.card-no-poster {{
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    gap: 8px;
    color: {text_muted};
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    text-align: center;
    padding: 16px;
    box-sizing: border-box;
}}

/* ── Card select buttons ── */
div[data-testid="stButton"] button.card-select-btn {{
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    width: 100% !important;
    height: 100% !important;
    position: absolute !important;
    top: 0 !important; left: 0 !important;
    cursor: pointer !important;
    opacity: 0 !important;
}}

/* Style all buttons inside card containers */
.card-btn-container button {{
    background: {btn_bg} !important;
    border: none !important;
    border-radius: 8px !important;
    color: white !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 10px !important;
    letter-spacing: 1px !important;
    padding: 6px 0 !important;
    width: 100% !important;
    cursor: pointer !important;
    margin-top: 8px !important;
    transition: all 0.2s ease !important;
}}
.card-btn-container button:hover {{
    background: {btn_hover_bg} !important;
    box-shadow: 0 4px 14px {btn_shadow} !important;
}}

/* ── Movie Info ── */
.movie-meta {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    color: {meta_color};
    letter-spacing: 1.2px;
    margin-bottom: 12px;
}}
.movie-title-display {{
    font-family: 'Syne', sans-serif;
    font-size: clamp(28px, 4vw, 44px);
    font-weight: 800;
    color: {text_primary};
    margin-bottom: 6px;
}}

/* ── Debate Bubbles ── */
.debate-wrap {{
    display: flex;
    flex-direction: column;
    gap: 16px;
    margin-top: 8px;
}}
.debate-bubble {{
    padding: 18px 22px;
    font-size: 15px;
    line-height: 1.75;
    max-width: 90%;
    color: {text_secondary};
}}
.bubble-critic {{
    background: {critic_bg};
    border: 1px solid {critic_border};
    border-radius: 16px 16px 16px 4px;
    align-self: flex-start;
}}
.bubble-advocate {{
    background: {advocate_bg};
    border: 1px solid {advocate_border};
    border-radius: 16px 16px 4px 16px;
    align-self: flex-end;
}}
.bubble-label {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 8px;
    font-weight: 700;
}}
.bubble-label-critic   {{ color: {critic_color}; }}
.bubble-label-advocate {{ color: {advocate_color}; }}
.bubble-model-tag {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    opacity: 0.6;
    margin-left: 8px;
    letter-spacing: 1px;
}}
.round-pill {{
    display: block;
    width: fit-content;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    letter-spacing: 2px;
    text-transform: uppercase;
    background: {tag_bg};
    border: 1px solid {tag_border};
    color: {accent3};
    padding: 3px 10px;
    border-radius: 100px;
    margin: 12px auto 4px auto;
    text-align: center;
}}

/* ── Summary Box ── */
.summary-box {{
    background: {verdict_bg};
    border-left: 3px solid {verdict_border};
    border-radius: 0 16px 16px 0;
    padding: 22px 26px;
    font-size: 15px;
    color: {text_secondary};
    line-height: 1.85;
    margin-bottom: 8px;
}}

/* ── Themes ── */
.theme-tag {{
    display: inline-block;
    background: {tag_bg};
    border: 1px solid {tag_border};
    color: {accent3};
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    padding: 5px 14px;
    border-radius: 100px;
    margin: 4px 3px;
    letter-spacing: 0.5px;
}}

/* ── Section Heading ── */
.section-heading {{
    font-family: 'Syne', sans-serif;
    font-size: 19px;
    font-weight: 700;
    color: {text_primary};
    margin: 24px 0 12px 0;
    display: flex;
    align-items: center;
    gap: 8px;
}}

/* ── Point Items ── */
.point-item {{
    display: flex;
    align-items: flex-start;
    gap: 10px;
    font-size: 15px;
    color: {text_secondary};
    padding: 9px 0;
    border-bottom: 1px solid {border_color};
    line-height: 1.6;
}}
.dot-green {{ color: #34d399; font-size: 17px; }}
.dot-red   {{ color: #f87171; font-size: 17px; }}

/* ── Misc ── */
.fancy-divider {{
    height: 1px;
    background: linear-gradient(to right, transparent, {border_color}, transparent);
    margin: 28px 0;
}}
.err-box {{
    background: {error_bg};
    border: 1px solid {error_border};
    border-radius: 12px;
    padding: 18px 22px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 14px;
    color: #f87171;
    text-align: center;
}}
[data-testid="stImage"] img {{
    border-radius: 16px !important;
    box-shadow: 0 20px 60px rgba(0,0,0,0.5) !important;
}}
[data-testid="stExpander"] {{
    background: {expander_bg} !important;
    border: 1px solid {border_color} !important;
    border-radius: 12px !important;
    margin-top: 2px !important;
}}
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary p {{
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 12px !important;
    color: {accent1} !important;
    letter-spacing: 1px !important;
}}
p, li, div {{
    font-size: 15px;
}}
</style>
""", unsafe_allow_html=True)

# ---------------- THEME TOGGLE (top right) ----------------
_, tog_col = st.columns([8, 2])
with tog_col:
    label_text  = "🌙 Dark" if is_dark else "☀️ Light"
    st.toggle(label_text, key="light_mode")
    st.markdown(f"""
    <style>
    [data-testid="stWidgetLabel"] p,
    [data-testid="stWidgetLabel"] span,
    [data-testid="stToggle"] p,
    [data-testid="stToggle"] span,
    [data-testid="stCheckbox"] p,
    [data-testid="stCheckbox"] span {{
        color: {text_primary} !important;
        -webkit-text-fill-color: {text_primary} !important;
        font-family: 'JetBrains Mono', monospace !important;
        letter-spacing: 1px !important;
        font-size: 14px !important;
        font-weight: 800 !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# ---------------- HERO ----------------
st.markdown("<div class='hero-eyebrow'>⬡ Multi-Agent Intelligence · Powered by AI</div>", unsafe_allow_html=True)
st.markdown("<div class='hero-title'>Movie Review Agent</div>", unsafe_allow_html=True)
st.markdown("<div class='hero-sub'>Ask about any film — two AI models debate it, then deliver a verdict.</div>", unsafe_allow_html=True)

c1, c2, c3 = st.columns([1, 2.5, 1])
with c2:
    user_input = st.chat_input("Search a movie title...")

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# ---------------- HANDLE SEARCH INPUT ----------------
# FIX: Allow re-search after selecting a movie (selected_imdb_id cleared means
# the user is starting fresh, so accept even the same query again).
if user_input and user_input.strip():
    query = user_input.strip()
    if query.lower() != st.session_state.last_typed or st.session_state.selected_imdb_id is None:
        st.session_state.last_typed       = query.lower()
        st.session_state.selected_imdb_id = None
        st.session_state.cached_movie     = None
        st.session_state.cached_result    = None
        st.session_state.cached_query     = None
        with st.spinner("Finding movies..."):
            st.session_state.search_results = search_movies(query)

# ---------------- NETFLIX-STYLE SEARCH RESULTS ----------------
search_results = st.session_state.search_results
if search_results and not st.session_state.selected_imdb_id:
    st.markdown(
        f"<div class='search-section-label'>▸ Select a movie to review</div>",
        unsafe_allow_html=True,
    )

    num = len(search_results)
    cols = st.columns(num, gap="small")

    for i, item in enumerate(search_results):
        poster     = item.get("Poster", "N/A")
        title      = item.get("Title", "Unknown")
        year       = item.get("Year", "")
        imdb_id    = item.get("imdbID", "")
        has_poster = poster and poster != "N/A"

        with cols[i]:
            # Poster / placeholder
            if has_poster:
                st.markdown(
                    f"""
                    <div class="movie-card-wrap" style="margin-bottom:0;">
                        <img src="{poster}" alt="{title}" />
                        <div class="movie-card-overlay">
                            <div class="card-title-text">{title}</div>
                            <div class="card-year-text">{year}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""
                    <div class="movie-card-wrap" style="min-height:200px; margin-bottom:0;">
                        <div class="card-no-poster">
                            🎬<br/>{title}<br/><span style="opacity:0.5">{year}</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Select button
            st.markdown("<div class='card-btn-container'>", unsafe_allow_html=True)
            if st.button("▶  SELECT", key=f"sel_{imdb_id}_{i}", use_container_width=True):
                st.session_state.selected_imdb_id = imdb_id
                st.session_state.search_results   = []
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='fancy-divider'></div>", unsafe_allow_html=True)

# ---------------- RUN ANALYSIS ON SELECTED MOVIE ----------------
if st.session_state.selected_imdb_id and not st.session_state.cached_movie:
    with st.spinner("Fetching movie details..."):
        st.session_state.cached_movie = fetch_movie_by_id(st.session_state.selected_imdb_id)
        st.session_state.cached_query = st.session_state.selected_imdb_id

    if st.session_state.cached_movie:
        m = st.session_state.cached_movie
        raw_reviews = {
            "title":              m["title"],
            "critic_reviews":     m["plot"],
            "audience_reactions": m["actors"],
            "discussion_points":  m["genre"],
        }
        with st.spinner("AI models are debating the film..."):
            st.session_state.cached_result = analyze_movie(raw_reviews)

movie  = st.session_state.cached_movie
result = st.session_state.cached_result

# ---------------- ERROR STATE ----------------
if (
    st.session_state.last_typed is not None
    and not search_results
    and not movie
    and not st.session_state.selected_imdb_id
):
    st.markdown(
        "<div class='err-box'>⚠ &nbsp; No results found for that title. Try a different spelling.</div>",
        unsafe_allow_html=True,
    )

# ---------------- RENDER ANALYSIS ----------------
elif movie and result:

    # ── Movie Info ──────────────────────────────────────────────────────────
    col_poster, col_info = st.columns([1, 2.6], gap="large")

    with col_poster:
        if movie["poster"] and movie["poster"] != "N/A":
            st.image(movie["poster"], use_column_width=True)

    with col_info:
        st.markdown(f"<div class='movie-title-display'>{movie['title']}</div>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='movie-meta'>{movie['year']} &nbsp;·&nbsp; DIR: {movie['director']}"
            f" &nbsp;·&nbsp; {movie['runtime']}</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<p style='font-size:15px;color:{text_secondary};line-height:1.8;margin-top:12px;'>{movie['plot']}</p>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<p style='font-size:13px;color:{text_muted};font-family:JetBrains Mono,monospace;margin-top:6px;'>"
            f"CAST: {movie['actors']}</p>",
            unsafe_allow_html=True,
        )

    st.markdown("<div class='fancy-divider'></div>", unsafe_allow_html=True)

    # ── 1. THEMES ────────────────────────────────────────────────────────────
    st.markdown("<div class='section-heading'>🏷 &nbsp; Core Themes</div>", unsafe_allow_html=True)
    tags_html = "".join(
        f"<span class='theme-tag'>#{t.strip()}</span>"
        for t in result.get("themes", [])
    )
    st.markdown(f"<div style='line-height:2.4;'>{tags_html}</div>", unsafe_allow_html=True)

    st.markdown("<div class='fancy-divider'></div>", unsafe_allow_html=True)

    # ── 2. OVERVIEW & DEBATE SUMMARY ─────────────────────────────────────────
    st.markdown("<div class='section-heading'>🎬 &nbsp; Overview</div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='summary-box'>"
        f"In this session, our AI models debate the merits and flaws of "
        f"<strong>{movie['title']}</strong> ({movie['year']}), directed by <strong>{movie['director']}</strong>. "
        f"Starring {movie['actors']}, the film is a notable entry in the <em>{movie['genre']}</em> genre."
        f"<br><br>"
        f"<em>{movie['plot']}</em>"
        f"<br><br>"
        f"The debate below features a Critic model and an Advocate model arguing their perspectives across "
        f"multiple rounds — examining cinematic execution, narrative strength, and cultural impact."
        f"</div>",
        unsafe_allow_html=True,
    )

    st.markdown("<div class='section-heading'>🧠 &nbsp; Debate Summary</div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='summary-box'>{result.get('debate_summary', 'Summary unavailable.')}</div>",
        unsafe_allow_html=True,
    )

    st.markdown("<div class='fancy-divider'></div>", unsafe_allow_html=True)

    # ── 3. RING CHART SCORES ─────────────────────────────────────────────────
    st.markdown("<div class='section-heading'>🎯 &nbsp; Scores</div>", unsafe_allow_html=True)

    # ── Parse AI score ──
    raw_ai_score = str(result.get("final_score", "N/A"))
    try:
        if "/" in raw_ai_score:
            num_str = raw_ai_score.split("/")[0].strip()
            ai_pct  = float(num_str) * 10
        else:
            ai_pct  = float(re.sub(r"[^\d.]", "", raw_ai_score)) * 10
        ai_pct = min(max(ai_pct, 0), 100)
    except Exception:
        ai_pct = 0
    ai_display = raw_ai_score if raw_ai_score != "N/A" else "—"

    # ── Parse IMDb score ──
    raw_imdb = str(movie.get("imdb_rating", "—"))
    try:
        imdb_pct = float(raw_imdb.split("/")[0] if "/" in raw_imdb else raw_imdb) * 10
        imdb_pct = min(max(imdb_pct, 0), 100)
    except Exception:
        imdb_pct = 0
    imdb_display = raw_imdb

    # ── Parse RT score ──
    raw_rt = str(movie.get("rt_rating", "—"))
    try:
        rt_pct = float(raw_rt.replace("%", "").strip())
        rt_pct = min(max(rt_pct, 0), 100)
    except Exception:
        rt_pct = 0
    rt_display = raw_rt

    # FIX: Build ring SVGs with fully inlined styles so they render correctly
    # regardless of Streamlit's CSS sandboxing between st.markdown() calls.
    def ring_svg(pct, display, stroke_color, glow_color, bg_stroke_color):
        """Build a single animated ring SVG with all styles inlined."""
        dash = f"{pct:.1f}, 100"
        ring_style = (
            f"fill:none;stroke:{stroke_color};stroke-width:2.8;stroke-linecap:round;"
            f"filter:drop-shadow(0 0 4px {glow_color});"
            f"transform:rotate(-90deg);transform-origin:18px 18px;"
            f"animation:scoreProgress 1.2s ease-out forwards;"
        )
        return f"""
        <svg viewBox="0 0 36 36"
             style="display:block;width:130px;height:130px;">
            <defs>
                <style>
                    @keyframes scoreProgress {{
                        from {{ stroke-dasharray: 0, 100; }}
                        to   {{ stroke-dasharray: {dash}; }}
                    }}
                </style>
            </defs>
            <path style="fill:none;stroke:{bg_stroke_color};stroke-width:3.8;"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831
                             a 15.9155 15.9155 0 0 1 0 -31.831" />
            <path style="{ring_style}"
                stroke-dasharray="{dash}"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831
                             a 15.9155 15.9155 0 0 1 0 -31.831" />
            <text x="18" y="21"
                  style="fill:{stroke_color};font-family:sans-serif;font-size:7.5px;
                         font-weight:800;text-anchor:middle;">
                {display}
            </text>
        </svg>
        """

    # FIX: Wrap everything — keyframes + SVGs + labels — in ONE st.markdown call
    # so styles and markup share the same HTML context and the browser renders them.
    scores_html = f"""
    <div style="display:flex;gap:48px;align-items:center;
                margin:24px 0 16px 0;flex-wrap:wrap;">

        <div style="text-align:center;display:flex;flex-direction:column;
                    align-items:center;gap:10px;">
            {ring_svg(ai_pct, ai_display,
                      score_color, score_glow, score_border)}
            <div style="font-family:'JetBrains Mono',monospace;font-size:11px;
                        color:{meta_color};letter-spacing:2px;text-transform:uppercase;">
                AI Verdict
            </div>
        </div>

        <div style="text-align:center;display:flex;flex-direction:column;
                    align-items:center;gap:10px;">
            {ring_svg(imdb_pct, imdb_display,
                      "#f5c518", "rgba(245,197,24,0.5)", "rgba(245,197,24,0.12)")}
            <div style="font-family:'JetBrains Mono',monospace;font-size:11px;
                        color:{meta_color};letter-spacing:2px;text-transform:uppercase;">
                IMDb
            </div>
        </div>

        <div style="text-align:center;display:flex;flex-direction:column;
                    align-items:center;gap:10px;">
            {ring_svg(rt_pct, rt_display,
                      "#fa320a", "rgba(250,50,10,0.5)", "rgba(250,50,10,0.12)")}
            <div style="font-family:'JetBrains Mono',monospace;font-size:11px;
                        color:{meta_color};letter-spacing:2px;text-transform:uppercase;">
                Rotten Tomatoes
            </div>
        </div>

    </div>
    """
    st.markdown(scores_html, unsafe_allow_html=True)

    st.markdown("<div class='fancy-divider'></div>", unsafe_allow_html=True)

    # ── 4. DEBATE TRANSCRIPT ─────────────────────────────────────────────────
    debate = result.get("debate_transcript", [])
    if debate:
        st.markdown("<div class='section-heading'>⚔️ &nbsp; Live Debate Transcript</div>", unsafe_allow_html=True)
        st.markdown(
            f"<p style='font-size:13px;color:{text_muted};margin-bottom:12px;"
            f"font-family:JetBrains Mono,monospace;'>"
            f"{MODEL_CRITIC} &nbsp;vs&nbsp; {MODEL_ADVOCATE} &nbsp;·&nbsp; 4 rounds</p>",
            unsafe_allow_html=True,
        )
        with st.expander("▸ Click to read the full debate"):
            bubbles_html = "<div class='debate-wrap'>"
            round_num = 0
            for i, turn in enumerate(debate):
                if i % 2 == 0:
                    round_num += 1
                    bubbles_html += f"<div class='round-pill'>Round {round_num}</div>"

                is_critic    = turn["role"] == "Movie Critique Model"
                bubble_class = "bubble-critic"       if is_critic else "bubble-advocate"
                label_class  = "bubble-label-critic" if is_critic else "bubble-label-advocate"

                bubbles_html += (
                    f"<div class='debate-bubble {bubble_class}'>"
                    f"<div class='bubble-label {label_class}'>"
                    f"{turn['role']}"
                    f"<span class='bubble-model-tag'>{turn['model']}</span>"
                    f"</div>"
                    f"{turn['text']}"
                    f"</div>"
                )
            bubbles_html += "</div>"
            st.markdown(bubbles_html, unsafe_allow_html=True)