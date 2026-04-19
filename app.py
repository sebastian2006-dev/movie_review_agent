import requests
import streamlit as st
from agent.sentiment import analyze_movie, MODEL_CRITIC, MODEL_ADVOCATE

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
    except Exception:
        return None

    if not data or data.get("Response") == "False":
        return None

    imdb_rating = data.get("imdbRating")
    if not imdb_rating or imdb_rating == "N/A":
        imdb_rating = "—"

    return {
        "title":       data.get("Title"),
        "year":        data.get("Year"),
        "plot":        data.get("Plot"),
        "actors":      data.get("Actors"),
        "genre":       data.get("Genre"),
        "director":    data.get("Director"),
        "imdb_rating": imdb_rating,
        "poster":      data.get("Poster"),
        "runtime":     data.get("Runtime"),
    }


# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Movie Review Agent", layout="wide", initial_sidebar_state="collapsed")

# ---------------- SESSION STATE ----------------
if "light_mode"    not in st.session_state: st.session_state.light_mode    = False
if "cached_query"  not in st.session_state: st.session_state.cached_query  = None
if "cached_movie"  not in st.session_state: st.session_state.cached_movie  = None
if "cached_result" not in st.session_state: st.session_state.cached_result = None

is_dark = not st.session_state.light_mode

# ---------------- THEME VARIABLES ----------------
if is_dark:
    bg_base               = "#060b18"
    bg_card               = "rgba(255,255,255,0.04)"
    bg_card_hover         = "rgba(255,255,255,0.08)"
    border_color          = "rgba(255,255,255,0.08)"
    text_primary          = "#f0f4ff"          # brighter than before
    text_secondary        = "#c8d0e8"          # significantly brighter
    text_muted            = "#7a85a0"          # brighter muted
    accent1               = "#9b6fff"          # brighter purple
    accent2               = "#22d3ee"          # brighter cyan
    accent3               = "#c084fc"          # brighter violet
    glow1                 = "rgba(124,58,237,0.35)"
    glow2                 = "rgba(6,182,212,0.25)"
    glow3                 = "rgba(168,85,247,0.06)"
    verdict_bg            = "rgba(124,58,237,0.08)"
    verdict_border        = "#9b6fff"
    error_bg              = "rgba(239,68,68,0.1)"
    error_border          = "#ef4444"
    tag_bg                = "rgba(124,58,237,0.15)"
    tag_border            = "rgba(124,58,237,0.4)"
    score_color           = "#22d3ee"          # brighter
    score_glow            = "rgba(34,211,238,0.5)"
    score_bg              = "rgba(6,182,212,0.07)"
    score_border          = "rgba(6,182,212,0.22)"
    header_gradient       = "linear-gradient(135deg, #f0f4ff 0%, #c084fc 50%, #22d3ee 100%)"
    eyebrow_color         = "#22d3ee"
    input_border          = "rgba(155,111,255,0.5)"
    input_glow            = "rgba(155,111,255,0.3)"
    meta_color            = "#8892b0"          # brighter meta
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
else:
    bg_base               = "#fdfbf7"          # warm off-white/cream
    bg_card               = "rgba(255,255,255,0.85)"
    bg_card_hover         = "rgba(255,255,255,1)"
    border_color          = "rgba(217,119,54,0.15)"
    text_primary          = "#2c2421"          # deep warm brownish-black
    text_secondary        = "#4a3f3c"          # warm dark gray/brown
    text_muted            = "#7a6b68"          # warm gray
    accent1               = "#d97736"          # terracotta/orange
    accent2               = "#4a7c59"          # sage green
    accent3               = "#c4554b"          # muted red
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
    input_border          = text_primary
    input_glow            = "rgba(44,36,33,0.25)"
    meta_color            = "#665a58"
    expander_bg           = "rgba(255,255,255,0.7)"
    chatinput_bg          = text_primary
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
    font-size: 13px;              /* up from 11px */
    letter-spacing: 5px;
    color: {eyebrow_color};
    text-align: center;
    text-transform: uppercase;
    margin-bottom: 12px;
    opacity: 1;                   /* was 0.85 */
}}
.hero-title {{
    font-family: 'Syne', sans-serif;
    font-size: clamp(38px, 6vw, 68px);   /* up from 34/64 */
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
    font-size: 17px;              /* up from 15px */
    color: {text_muted};
    text-align: center;
    margin-bottom: 32px;
}}

/* ── Chat Input ── */
/* The entire Chat Input widget container */
div[data-testid="stChatInput"],
.stChatInput {{
    background: {chatinput_bg} !important;
    border: { '1px solid ' + input_border if is_dark else '2px solid ' + input_border } !important;
    border-radius: 16px !important;
    box-shadow: { 'none' if is_dark else '0 4px 16px rgba(0,0,0,0.06)' } !important;
    padding-right: 6px !important;
    padding-left: 6px !important;
}}

/* The div directly wrapping the textarea */
div[data-testid="stChatInput"] > div,
.stChatInput > div {{
    background: {chatinput_bg} !important;
    border: none !important;
    border-radius: 16px !important;
}}

/* The textarea itself */
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

/* ── Movie Info ── */
.movie-meta {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;              /* up from 12px */
    color: {meta_color};
    letter-spacing: 1.2px;
    margin-bottom: 12px;
}}
.movie-title-display {{
    font-family: 'Syne', sans-serif;
    font-size: clamp(28px, 4vw, 44px);   /* up from 24/40 */
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
    padding: 18px 22px;           /* slightly more padding */
    font-size: 15px;              /* up from 14px */
    line-height: 1.75;            /* slightly more leading */
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
    font-size: 11px;              /* up from 10px */
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 8px;
    font-weight: 700;
}}
.bubble-label-critic   {{ color: {critic_color}; }}
.bubble-label-advocate {{ color: {advocate_color}; }}
.bubble-model-tag {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;              /* up from 9px */
    opacity: 0.6;                 /* was 0.45 — more visible */
    margin-left: 8px;
    letter-spacing: 1px;
}}
.round-pill {{
    display: block;
    width: fit-content;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;              /* up from 9px */
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
    font-size: 15px;              /* up from 14px */
    color: {text_secondary};
    line-height: 1.85;
    margin-bottom: 8px;
}}

/* ── Score ── */
.score-pill {{
    display: inline-flex;
    align-items: center;
    gap: 12px;
    background: {score_bg};
    border: 1px solid {score_border};
    border-radius: 14px;
    padding: 14px 24px;
    margin: 4px 0 16px 0;
}}
.score-label {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;              /* up from 11px */
    letter-spacing: 2px;
    color: {meta_color};
    text-transform: uppercase;
}}
.score-value {{
    font-family: 'Syne', sans-serif;
    font-size: 36px;              /* up from 32px */
    font-weight: 800;
    color: {score_color};
    text-shadow: 0 0 20px {score_glow};
    line-height: 1;
}}

/* ── Themes ── */
.theme-tag {{
    display: inline-block;
    background: {tag_bg};
    border: 1px solid {tag_border};
    color: {accent3};
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;              /* up from 11px */
    padding: 5px 14px;
    border-radius: 100px;
    margin: 4px 3px;
    letter-spacing: 0.5px;
}}

/* ── Section Heading ── */
.section-heading {{
    font-family: 'Syne', sans-serif;
    font-size: 19px;              /* up from 17px */
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
    font-size: 15px;              /* up from 14px */
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
    font-size: 14px;              /* up from 13px */
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
    font-size: 12px !important;   /* up from 11px */
    color: {accent1} !important;
    letter-spacing: 1px !important;
}}

/* ── Body text baseline ── */
p, li, div {{
    font-size: 15px;
}}
</style>
""", unsafe_allow_html=True)

# ---------------- THEME TOGGLE (top right) ----------------
_, tog_col = st.columns([8, 2])
with tog_col:
    label_text  = "🌙 Dark" if is_dark else "☀️ Light"
    label_color = text_primary
    
    st.toggle(label_text, key="light_mode")
    
    st.markdown(f"""
    <style>
    /* Explicitly target the text inside the toggle widget to override Streamlit defaults */
    [data-testid="stWidgetLabel"] p,
    [data-testid="stWidgetLabel"] span,
    [data-testid="stToggle"] p,
    [data-testid="stToggle"] span,
    [data-testid="stCheckbox"] p,
    [data-testid="stCheckbox"] span {{
        color: {label_color} !important;
        -webkit-text-fill-color: {label_color} !important;
        font-family: 'JetBrains Mono', monospace !important;
        letter-spacing: 1px !important;
        font-size: 14px !important;
        font-weight: 800 !important;
    }}
    
    /* Align the toggle switch properly without breaking its internal click target */
    [data-testid="stWidgetLabel"],
    [data-testid="stToggle"],
    [data-testid="stCheckbox"] {{
        float: right;
        margin-top: { '-10px' if is_dark else '0' } !important;
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
            with st.spinner("AI models are debating the film..."):
                st.session_state.cached_result = analyze_movie(raw_reviews)

movie  = st.session_state.cached_movie
result = st.session_state.cached_result

# ---------------- ERROR STATE ----------------
if movie is None and st.session_state.cached_query is not None:
    st.markdown(
        "<div class='err-box'>⚠ &nbsp; No results found for that title. Try a different spelling.</div>",
        unsafe_allow_html=True
    )

# ---------------- RENDER ----------------
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
            f" &nbsp;·&nbsp; {movie['runtime']} &nbsp;·&nbsp; ⭐ IMDb {movie['imdb_rating']}</div>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<p style='font-size:15px;color:{text_secondary};line-height:1.8;margin-top:12px;'>{movie['plot']}</p>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<p style='font-size:13px;color:{text_muted};font-family:JetBrains Mono,monospace;margin-top:6px;'>"
            f"CAST: {movie['actors']}</p>",
            unsafe_allow_html=True
        )

    st.markdown("<div class='fancy-divider'></div>", unsafe_allow_html=True)

    # ── 1. DEBATE TRANSCRIPT ────────────────────────────────────────────────
    debate = result.get("debate_transcript", [])
    if debate:
        st.markdown("<div class='section-heading'>⚔️ &nbsp; Live Debate Transcript</div>", unsafe_allow_html=True)
        st.markdown(
            f"<p style='font-size:13px;color:{text_muted};margin-bottom:12px;"
            f"font-family:JetBrains Mono,monospace;'>"
            f"{MODEL_CRITIC} &nbsp;vs&nbsp; {MODEL_ADVOCATE} &nbsp;·&nbsp; 4 rounds</p>",
            unsafe_allow_html=True
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

    st.markdown("<div class='fancy-divider'></div>", unsafe_allow_html=True)

    # ── 2. DEBATE SUMMARY ───────────────────────────────────────────────────
    st.markdown("<div class='section-heading'>🧠 &nbsp; Debate Summary</div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='summary-box'>{result.get('debate_summary', 'Summary unavailable.')}</div>",
        unsafe_allow_html=True
    )

    # ── What Works / What Falls Short ──────────────────────────────────────
    w1, w2 = st.columns(2, gap="large")

    with w1:
        st.markdown("<div class='section-heading'>✅ &nbsp; What Works</div>", unsafe_allow_html=True)
        for item in result.get("what_works", []):
            st.markdown(
                f"<div class='point-item'><span class='dot-green'>›</span>{item}</div>",
                unsafe_allow_html=True
            )

    with w2:
        st.markdown("<div class='section-heading'>❌ &nbsp; What Falls Short</div>", unsafe_allow_html=True)
        for item in result.get("what_fails", []):
            st.markdown(
                f"<div class='point-item'><span class='dot-red'>›</span>{item}</div>",
                unsafe_allow_html=True
            )

    st.markdown("<div class='fancy-divider'></div>", unsafe_allow_html=True)

    # ── 3. THEMES + FINAL SCORE ─────────────────────────────────────────────
    col_themes, col_score = st.columns([3, 1], gap="large")

    with col_themes:
        st.markdown("<div class='section-heading'>🏷 &nbsp; Core Themes</div>", unsafe_allow_html=True)
        tags_html = "".join(
            f"<span class='theme-tag'>#{t.strip()}</span>"
            for t in result.get("themes", [])
        )
        st.markdown(f"<div style='line-height:2.4;'>{tags_html}</div>", unsafe_allow_html=True)

    with col_score:
        st.markdown("<div class='section-heading'>🎯 &nbsp; Final Score</div>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='score-pill'>"
            f"<span class='score-label'>Overall</span>"
            f"<span class='score-value'>{result.get('final_score', 'N/A')}</span>"
            f"</div>",
            unsafe_allow_html=True
        )