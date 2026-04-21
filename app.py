import re
import requests
import streamlit as st
from agent.sentiment import analyze_movie, MODEL_CRITIC, MODEL_ADVOCATE

API_KEY = st.secrets["OMDB_API_KEY"]


# ---------------- SEARCH MOVIES ----------------
def search_movies(query: str):
    if not API_KEY:
        return [], None
    url = "http://www.omdbapi.com/"

    exact = None
    try:
        r = requests.get(url, params={"t": query, "apikey": API_KEY, "r": "json"}, timeout=10)
        d = r.json()
        if d.get("Response") == "True" and d.get("imdbID"):
            exact = {
                "Title":  d.get("Title", query),
                "Year":   d.get("Year", ""),
                "imdbID": d.get("imdbID", ""),
                "Poster": d.get("Poster", "N/A"),
                "Type":   d.get("Type", ""),
            }
    except Exception:
        pass

    fuzzy = []
    try:
        r = requests.get(url, params={"s": query, "apikey": API_KEY, "r": "json"}, timeout=10)
        d = r.json()
        if d.get("Response") == "True":
            fuzzy = d.get("Search", [])
    except Exception:
        pass

    seen = set()
    merged = []
    error_msg = None

    if exact:
        merged.append(exact)
        seen.add(exact["imdbID"])

    for item in fuzzy:
        iid = item.get("imdbID", "")
        if iid not in seen:
            merged.append(item)
            seen.add(iid)

    if not merged:
        try:
            r = requests.get(url, params={"s": query, "apikey": API_KEY}, timeout=10)
            d = r.json()
            if d.get("Response") == "False":
                error_msg = d.get("Error")
        except Exception:
            pass

    return merged[:6], error_msg


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
        source = r.get("Source", "")
        if "Rotten Tomatoes" in source:
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


# ================================================================
# PAGE CONFIG
# ================================================================
st.set_page_config(
    page_title="CineGlow · Movie Review Agent",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ================================================================
# SESSION STATE
# ================================================================
if "cached_query"     not in st.session_state: st.session_state.cached_query     = None
if "cached_movie"     not in st.session_state: st.session_state.cached_movie     = None
if "cached_result"    not in st.session_state: st.session_state.cached_result    = None
if "search_results"   not in st.session_state: st.session_state.search_results   = []
if "selected_imdb_id" not in st.session_state: st.session_state.selected_imdb_id = None
if "last_typed"       not in st.session_state: st.session_state.last_typed       = None
if "search_error"     not in st.session_state: st.session_state.search_error     = None

# ================================================================
# CINEMATIC EMBER — DESIGN TOKENS
# ================================================================
C = {
    # Surfaces
    "bg":               "#161311",
    "bg_lowest":        "#110d0c",
    "bg_low":           "#1f1b19",
    "bg_container":     "#231f1d",
    "bg_high":          "#2e2927",
    "bg_highest":       "#393431",
    "bg_bright":        "#3d3836",
    # Text
    "on_surface":       "#eae1dd",
    "on_surface_var":   "#d6c4ad",
    "on_primary":       "#442b00",
    "text_muted":       "#9f8e79",
    "text_dim":         "#514533",
    # Primaries / Accents
    "primary":          "#ffd79e",
    "primary_dim":      "#ffba47",
    "primary_container":"#ffb224",
    "secondary":        "#ffb77e",
    "tertiary":         "#fed4c2",
    "outline":          "#9f8e79",
    "outline_var":      "#514533",
    # Glow helpers
    "glow_amber":       "rgba(255,178,36,0.18)",
    "glow_amber_md":    "rgba(255,178,36,0.28)",
    "glow_amber_btn":   "rgba(255,178,36,0.22)",
    "glow_orange":      "rgba(255,183,126,0.15)",
    "critic_color":     "#ffba47",
    "advocate_color":   "#ffb77e",
    "critic_bg":        "rgba(255,186,71,0.07)",
    "advocate_bg":      "rgba(255,183,126,0.07)",
    "critic_border":    "rgba(255,186,71,0.22)",
    "advocate_border":  "rgba(255,183,126,0.22)",
}

# ================================================================
# GLOBAL CSS — CINEMATIC EMBER DESIGN SYSTEM
# ================================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Epilogue:wght@400;500;600;700;800&family=Be+Vietnam+Pro:wght@400;500&display=swap');

/* ── Reset sidebar toggle ── */
[data-testid="stSidebarCollapsedControl"] {{ display: none !important; }}
header[data-testid="stHeader"] {{ background: transparent !important; }}
.stApp > header {{ display: none !important; }}

/* ── App Shell ── */
.stApp {{
    background-color: {C["bg"]} !important;
    color: {C["on_surface"]};
    font-family: 'Be Vietnam Pro', sans-serif;
}}
.block-container {{
    max-width: 1200px;
    padding-top: 0 !important;
    padding-bottom: 6rem;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
}}

/* ── Ambient background glow ── */
.stApp::before {{
    content: '';
    position: fixed;
    inset: 0;
    z-index: -1;
    background:
        radial-gradient(ellipse 70% 55% at 15% 5%,  {C["glow_amber"]}   0%, transparent 65%),
        radial-gradient(ellipse 50% 45% at 85% 85%, {C["glow_orange"]}  0%, transparent 55%),
        radial-gradient(ellipse 35% 35% at 50% 50%, rgba(255,178,36,0.04) 0%, transparent 70%);
    pointer-events: none;
}}

/* ── Scrollbar ── */
::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: {C["bg_lowest"]}; }}
::-webkit-scrollbar-thumb {{ background: {C["bg_highest"]}; border-radius: 4px; }}
::-webkit-scrollbar-thumb:hover {{ background: {C["outline_var"]}; }}

h1, h2, h3, h4 {{ font-family: 'Epilogue', sans-serif !important; }}

/* ════════════════════════════════════════
   TOP NAV BAR
════════════════════════════════════════ */
.cineglow-nav {{
    position: sticky;
    top: 0;
    z-index: 100;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 2rem;
    height: 68px;
    background: rgba(17,13,12,0.85);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    border-bottom: 1px solid {C["outline_var"]}40;
    box-shadow: 0 10px 40px -15px {C["glow_amber_md"]};
    margin-left: -2rem;
    margin-right: -2rem;
    margin-bottom: 2.5rem;
}}
.nav-brand {{
    font-family: 'Epilogue', sans-serif;
    font-size: 22px;
    font-weight: 800;
    color: {C["primary_container"]};
    letter-spacing: -0.03em;
    cursor: pointer;
}}
.nav-brand span {{
    color: {C["on_surface"]};
    font-weight: 400;
    opacity: 0.5;
    font-size: 14px;
    margin-left: 6px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    vertical-align: middle;
}}
.nav-pill {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: {C["bg_high"]};
    border: 1px solid {C["outline_var"]};
    border-radius: 9999px;
    padding: 6px 14px;
    font-family: 'Epilogue', sans-serif;
    font-size: 12px;
    font-weight: 600;
    color: {C["on_surface_var"]};
    letter-spacing: 0.08em;
    text-transform: uppercase;
}}
.nav-dot {{
    width: 6px; height: 6px;
    border-radius: 50%;
    background: {C["primary_container"]};
    box-shadow: 0 0 8px {C["primary_container"]};
    animation: pulse-dot 2.5s ease-in-out infinite;
}}
@keyframes pulse-dot {{
    0%, 100% {{ opacity: 1; transform: scale(1); }}
    50%       {{ opacity: 0.5; transform: scale(0.75); }}
}}

/* ════════════════════════════════════════
   HERO / PAGE HEADER
════════════════════════════════════════ */
.hero-eyebrow {{
    font-family: 'Epilogue', sans-serif;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.2em;
    color: {C["primary_container"]};
    text-transform: uppercase;
    text-align: center;
    margin-bottom: 14px;
}}
.hero-title {{
    font-family: 'Epilogue', sans-serif;
    font-size: clamp(36px, 5.5vw, 60px);
    font-weight: 800;
    letter-spacing: -0.02em;
    line-height: 1.1;
    text-align: center;
    color: {C["on_surface"]};
    margin-bottom: 10px;
}}
.hero-title em {{
    font-style: normal;
    color: {C["primary_container"]};
}}
.hero-sub {{
    font-family: 'Be Vietnam Pro', sans-serif;
    font-size: 17px;
    color: {C["on_surface_var"]};
    text-align: center;
    max-width: 520px;
    margin: 0 auto 36px auto;
    line-height: 1.6;
}}

/* ════════════════════════════════════════
   CHAT INPUT — RECESSED DARK FIELD
════════════════════════════════════════ */
div[data-testid="stChatInput"],
.stChatInput {{
    background: {C["bg_lowest"]} !important;
    border: 1px solid {C["outline_var"]} !important;
    border-radius: 9999px !important;
    box-shadow: inset 0 2px 8px rgba(0,0,0,0.4) !important;
    padding-right: 8px !important;
    padding-left: 8px !important;
    transition: border-color 0.3s ease, box-shadow 0.3s ease !important;
}}
div[data-testid="stChatInput"]:focus-within,
.stChatInput:focus-within {{
    border-color: {C["primary_container"]}80 !important;
    box-shadow: inset 0 2px 8px rgba(0,0,0,0.4), 0 0 24px {C["glow_amber"]} !important;
}}
div[data-testid="stChatInput"] > div,
.stChatInput > div {{
    background: transparent !important;
    border: none !important;
    border-radius: 9999px !important;
}}
textarea[data-testid="stChatInputTextArea"],
div[data-testid="stChatInput"] textarea,
.stChatInput textarea {{
    background: transparent !important;
    border: none !important;
    color: {C["on_surface"]} !important;
    -webkit-text-fill-color: {C["on_surface"]} !important;
    font-family: 'Be Vietnam Pro', sans-serif !important;
    font-size: 16px !important;
    padding: 14px 20px !important;
    box-shadow: none !important;
    caret-color: {C["primary_container"]} !important;
}}
textarea[data-testid="stChatInputTextArea"]::placeholder,
div[data-testid="stChatInput"] textarea::placeholder {{
    color: {C["text_muted"]} !important;
    -webkit-text-fill-color: {C["text_muted"]} !important;
}}

/* ── Send Button ── */
button[data-testid="stChatInputSubmitButton"],
div[data-testid="stChatInput"] button,
.stChatInput button {{
    background: {C["primary_container"]} !important;
    border: none !important;
    border-radius: 9999px !important;
    width: 38px !important;
    height: 38px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    cursor: pointer !important;
    box-shadow: 0 4px 20px {C["glow_amber_btn"]} !important;
    transition: all 0.2s ease !important;
    flex-shrink: 0 !important;
    margin-top: 4px !important;
}}
button[data-testid="stChatInputSubmitButton"]:hover {{
    background: {C["primary_dim"]} !important;
    box-shadow: 0 6px 28px {C["glow_amber_md"]} !important;
    transform: scale(1.08) !important;
}}
button[data-testid="stChatInputSubmitButton"] svg,
div[data-testid="stChatInput"] button svg {{
    stroke: {C["on_primary"]} !important;
    fill: none !important;
    width: 16px !important; height: 16px !important;
}}

/* ════════════════════════════════════════
   SEARCH RESULT CARDS — Poster Grid
════════════════════════════════════════ */
.search-label {{
    font-family: 'Epilogue', sans-serif;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: {C["primary_container"]};
    margin-bottom: 18px;
    margin-top: 6px;
}}

/* Override streamlit image rounding + hover */
div[data-testid="column"] img {{
    border-radius: 12px !important;
    display: block !important;
    cursor: pointer !important;
    transition: transform 0.3s ease, box-shadow 0.3s ease !important;
}}
div[data-testid="column"] img:hover {{
    transform: scale(1.04) !important;
    box-shadow: 0 16px 48px -8px {C["glow_amber_md"]} !important;
}}

/* Invisible poster overlay button */
div[data-testid="column"] div[data-testid="stButton"] > button {{
    background: transparent !important;
    border: none !important;
    border-radius: 0 !important;
    color: transparent !important;
    -webkit-text-fill-color: transparent !important;
    font-size: 1px !important;
    padding: 0 !important;
    margin-top: -300px !important;
    height: 300px !important;
    width: 100% !important;
    cursor: pointer !important;
    position: relative !important;
    z-index: 10 !important;
}}
div[data-testid="column"] div[data-testid="stButton"] > button:hover {{
    background: rgba(255,178,36,0.06) !important;
}}

/* ════════════════════════════════════════
   MOVIE DETAIL — TITLE / META
════════════════════════════════════════ */
.movie-title-display {{
    font-family: 'Epilogue', sans-serif;
    font-size: clamp(26px, 3.5vw, 42px);
    font-weight: 800;
    letter-spacing: -0.02em;
    line-height: 1.1;
    color: {C["on_surface"]};
    margin-bottom: 8px;
}}
.movie-meta {{
    font-family: 'Epilogue', sans-serif;
    font-size: 13px;
    font-weight: 500;
    letter-spacing: 0.05em;
    color: {C["text_muted"]};
    margin-bottom: 18px;
    text-transform: uppercase;
}}
.movie-meta b {{
    color: {C["primary_container"]};
}}

/* ════════════════════════════════════════
   SECTION HEADING
════════════════════════════════════════ */
.section-heading {{
    font-family: 'Epilogue', sans-serif;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: {C["primary_container"]};
    margin: 32px 0 14px 0;
    display: flex;
    align-items: center;
    gap: 10px;
}}
.section-heading::after {{
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(to right, {C["outline_var"]}80, transparent);
}}

/* ════════════════════════════════════════
   AGENDA / INFO CARD
════════════════════════════════════════ */
.agenda-card {{
    background: {C["bg_container"]};
    border: 1px solid {C["outline_var"]}60;
    border-radius: 12px;
    padding: 20px 24px;
    margin-top: 18px;
    box-shadow: 0 8px 32px -12px rgba(0,0,0,0.5);
}}
.agenda-title {{
    font-family: 'Epilogue', sans-serif;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: {C["primary_container"]};
    margin-bottom: 12px;
}}
.agenda-item {{
    font-family: 'Be Vietnam Pro', sans-serif;
    font-size: 14px;
    color: {C["on_surface_var"]};
    line-height: 1.7;
    padding: 3px 0;
}}
.agenda-item b {{
    color: {C["on_surface"]};
}}

/* ════════════════════════════════════════
   SUMMARY / VERDICT BOX
════════════════════════════════════════ */
.summary-box {{
    background: linear-gradient(135deg, {C["bg_container"]} 0%, {C["bg_high"]}60 100%);
    border-left: 3px solid {C["primary_container"]};
    border-radius: 0 12px 12px 0;
    padding: 22px 28px;
    font-family: 'Be Vietnam Pro', sans-serif;
    font-size: 15px;
    color: {C["on_surface_var"]};
    line-height: 1.85;
    box-shadow: 0 4px 20px -8px rgba(0,0,0,0.4);
}}

/* ════════════════════════════════════════
   THEME CHIPS
════════════════════════════════════════ */
.theme-tag {{
    display: inline-block;
    background: rgba(255,178,36,0.09);
    border: 1px solid rgba(255,178,36,0.25);
    color: {C["secondary"]};
    font-family: 'Epilogue', sans-serif;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.04em;
    padding: 5px 14px;
    border-radius: 9999px;
    margin: 4px 3px;
    transition: all 0.2s ease;
}}

/* ════════════════════════════════════════
   DEBATE TRANSCRIPT BUBBLES
════════════════════════════════════════ */
.debate-wrap {{
    display: flex;
    flex-direction: column;
    gap: 18px;
    margin-top: 10px;
}}
.debate-bubble {{
    padding: 18px 22px;
    font-family: 'Be Vietnam Pro', sans-serif;
    font-size: 15px;
    line-height: 1.75;
    max-width: 88%;
    color: {C["on_surface_var"]};
    box-shadow: 0 4px 18px -8px rgba(0,0,0,0.35);
}}
.bubble-critic {{
    background: {C["critic_bg"]};
    border: 1px solid {C["critic_border"]};
    border-radius: 16px 16px 16px 4px;
    align-self: flex-start;
}}
.bubble-advocate {{
    background: {C["advocate_bg"]};
    border: 1px solid {C["advocate_border"]};
    border-radius: 16px 16px 4px 16px;
    align-self: flex-end;
}}
.bubble-label {{
    font-family: 'Epilogue', sans-serif;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 10px;
}}
.bubble-label-critic   {{ color: {C["critic_color"]}; }}
.bubble-label-advocate {{ color: {C["advocate_color"]}; }}
.bubble-model-tag {{
    font-family: 'Epilogue', sans-serif;
    font-size: 10px;
    opacity: 0.5;
    margin-left: 8px;
    letter-spacing: 0.05em;
}}
.round-pill {{
    display: block;
    width: fit-content;
    font-family: 'Epilogue', sans-serif;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    background: rgba(255,186,71,0.1);
    border: 1px solid rgba(255,186,71,0.3);
    color: {C["primary_dim"]};
    padding: 3px 12px;
    border-radius: 9999px;
    margin: 14px auto 6px auto;
    text-align: center;
}}

/* ════════════════════════════════════════
   DIVIDER
════════════════════════════════════════ */
.fancy-divider {{
    height: 1px;
    background: linear-gradient(to right, transparent, {C["outline_var"]}60, transparent);
    margin: 32px 0;
}}

/* ════════════════════════════════════════
   ERROR BOX
════════════════════════════════════════ */
.err-box {{
    background: rgba(255,178,36,0.06);
    border: 1px solid rgba(255,178,36,0.2);
    border-radius: 12px;
    padding: 20px 28px;
    font-family: 'Epilogue', sans-serif;
    font-size: 14px;
    font-weight: 500;
    color: {C["secondary"]};
    text-align: center;
    letter-spacing: 0.02em;
}}

/* ════════════════════════════════════════
   POSTER IMAGE
════════════════════════════════════════ */
[data-testid="stImage"] img {{
    border-radius: 12px !important;
    box-shadow: 0 24px 64px -12px rgba(0,0,0,0.65),
                0 0 40px -15px {C["glow_amber"]} !important;
}}

/* ════════════════════════════════════════
   EXPANDERS
════════════════════════════════════════ */
[data-testid="stExpander"] {{
    background: {C["bg_container"]} !important;
    border: 1px solid {C["outline_var"]}60 !important;
    border-radius: 12px !important;
    margin-top: 4px !important;
}}
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary p {{
    font-family: 'Epilogue', sans-serif !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    letter-spacing: 0.05em !important;
    color: {C["primary_container"]} !important;
}}

/* ════════════════════════════════════════
   GENERAL TEXT
════════════════════════════════════════ */
p, li, div {{
    font-size: 15px;
}}
</style>
""", unsafe_allow_html=True)


# ================================================================
# TOP NAV BAR
# ================================================================
st.markdown(f"""
<div class="cineglow-nav">
    <div class="nav-brand">CineGlow <span>Movie Agent</span></div>
    <div class="nav-pill">
        <div class="nav-dot"></div>
        Multi-Agent · AI Debate Engine
    </div>
</div>
""", unsafe_allow_html=True)


# ================================================================
# HERO SECTION
# ================================================================
st.markdown("<div class='hero-eyebrow'>⬡ Curated by AI · Two Models · One Verdict</div>", unsafe_allow_html=True)
st.markdown("<div class='hero-title'>Movie Review <em>Agent</em></div>", unsafe_allow_html=True)
st.markdown(
    "<div class='hero-sub'>Search any film — a Critic and an Advocate debate it across four rounds, then deliver a calibrated verdict.</div>",
    unsafe_allow_html=True,
)

c1, c2, c3 = st.columns([1, 2.6, 1])
with c2:
    user_input = st.chat_input("Search a film title, e.g. Oppenheimer…")

st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)


# ================================================================
# HANDLE SEARCH INPUT
# ================================================================
if user_input and user_input.strip():
    if user_input != st.session_state.last_typed:
        st.session_state.last_typed       = user_input
        st.session_state.selected_imdb_id = None
        st.session_state.cached_movie     = None
        st.session_state.cached_result    = None
        with st.spinner("Searching the archive…"):
            results, err = search_movies(user_input)
            st.session_state.search_results = results
            st.session_state.search_error   = err
        st.rerun()


# ================================================================
# POSTER GRID — SEARCH RESULTS
# ================================================================
search_results = st.session_state.search_results
if search_results and not st.session_state.selected_imdb_id:

    st.markdown("<div class='search-label'>▸ Select a film to begin the AI debate</div>", unsafe_allow_html=True)

    display_results = search_results[:4]
    cols = st.columns(len(display_results), gap="medium")

    for i, item in enumerate(display_results):
        poster  = item.get("Poster", "N/A")
        title   = item.get("Title", "Unknown")
        year    = item.get("Year", "")
        imdb_id = item.get("imdbID", "")
        has_poster = poster and poster != "N/A"

        with cols[i]:
            if has_poster:
                try:
                    st.image(poster, use_container_width=True)
                except Exception:
                    st.markdown(
                        f"<div style='height:300px;background:{C['bg_high']};border-radius:12px;"
                        f"display:flex;align-items:center;justify-content:center;"
                        f"font-size:42px;cursor:pointer;'>🎬</div>",
                        unsafe_allow_html=True,
                    )
            else:
                st.markdown(
                    f"<div style='height:300px;background:{C['bg_high']};border-radius:12px;"
                    f"display:flex;align-items:center;justify-content:center;"
                    f"font-size:42px;cursor:pointer;'>🎬</div>",
                    unsafe_allow_html=True,
                )

            if st.button("\u200b", key=f"sel_{imdb_id}_{i}", use_container_width=True):
                st.session_state.selected_imdb_id = imdb_id
                st.session_state.search_results   = []
                st.session_state.cached_movie     = None
                st.session_state.cached_result    = None
                st.rerun()

    st.markdown("<div class='fancy-divider'></div>", unsafe_allow_html=True)


# ================================================================
# RUN ANALYSIS
# ================================================================
if st.session_state.selected_imdb_id and not st.session_state.cached_movie:
    with st.spinner("Fetching film details…"):
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
        with st.spinner("AI models are entering the debate hall…"):
            st.session_state.cached_result = analyze_movie(raw_reviews)


movie  = st.session_state.cached_movie
result = st.session_state.cached_result


# ================================================================
# ERROR STATE
# ================================================================
if (
    st.session_state.last_typed is not None
    and not search_results
    and not movie
    and not st.session_state.selected_imdb_id
):
    err_msg = st.session_state.get("search_error") or "No results found. Try a different title or spelling."
    st.markdown(f"<div class='err-box'>⚠ &nbsp; {err_msg}</div>", unsafe_allow_html=True)


# ================================================================
# RENDER ANALYSIS
# ================================================================
elif movie and result:

    # ── MOVIE HEADER ─────────────────────────────────────────────
    col_poster, col_info = st.columns([1, 2.8], gap="large")

    with col_poster:
        if movie["poster"] and movie["poster"] != "N/A":
            st.image(movie["poster"], use_column_width=True)

    with col_info:
        st.markdown(f"<div class='movie-title-display'>{movie['title']}</div>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='movie-meta'>"
            f"{movie['year']} &nbsp;·&nbsp; <b>{movie['director']}</b> &nbsp;·&nbsp; {movie['runtime']}"
            f"</div>",
            unsafe_allow_html=True,
        )

        st.markdown("<div class='section-heading'>Overview</div>", unsafe_allow_html=True)
        st.markdown(
            f"<p style='font-family:Be Vietnam Pro,sans-serif;font-size:15px;"
            f"color:{C['on_surface_var']};line-height:1.8;margin-top:0;'>{movie['plot']}</p>",
            unsafe_allow_html=True,
        )

        # Debate Agenda Card
        st.markdown(f"""
        <div class="agenda-card">
            <div class="agenda-title">The Debate Agenda</div>
            <div class="agenda-item"><b>Round 1 —</b> Initial critical assessment vs. contrarian defence</div>
            <div class="agenda-item"><b>Round 2 —</b> Deep dive into craft, cinematography &amp; character</div>
            <div class="agenda-item"><b>Round 3 —</b> Rebuttals on pacing and cultural legacy</div>
            <div class="agenda-item"><b>Round 4 —</b> Nuanced synthesis and calibrated final score</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(
            f"<p style='font-family:Epilogue,sans-serif;font-size:12px;"
            f"letter-spacing:0.05em;color:{C['text_muted']};margin-top:16px;'>"
            f"CAST &nbsp;·&nbsp; {movie['actors']}</p>",
            unsafe_allow_html=True,
        )

    st.markdown("<div class='fancy-divider'></div>", unsafe_allow_html=True)

    # ── 1. THEMES ─────────────────────────────────────────────────
    st.markdown("<div class='section-heading'>Core Themes</div>", unsafe_allow_html=True)
    tags_html = "".join(
        f"<span class='theme-tag'>#{t.strip()}</span>"
        for t in result.get("themes", [])
    )
    st.markdown(f"<div style='line-height:2.6;'>{tags_html}</div>", unsafe_allow_html=True)

    st.markdown("<div class='fancy-divider'></div>", unsafe_allow_html=True)

    # ── 2. QUICK FACTS CARD + DEBATE SUMMARY ──────────────────────
    st.markdown("<div class='section-heading'>At a Glance</div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class="agenda-card" style="display:grid;grid-template-columns:1fr 1fr;gap:0 32px;">
        <div class="agenda-item" style="padding:6px 0;border-bottom:1px solid {C['outline_var']}30;">
            <b>Director</b><br>
            <span style="color:{C['primary_container']}">{movie['director']}</span>
        </div>
        <div class="agenda-item" style="padding:6px 0;border-bottom:1px solid {C['outline_var']}30;">
            <b>Year</b><br>
            <span style="color:{C['primary_container']}">{movie['year']}</span>
        </div>
        <div class="agenda-item" style="padding:6px 0;border-bottom:1px solid {C['outline_var']}30;">
            <b>Genre</b><br>
            <span style="color:{C['on_surface_var']}">{movie['genre']}</span>
        </div>
        <div class="agenda-item" style="padding:6px 0;border-bottom:1px solid {C['outline_var']}30;">
            <b>Runtime</b><br>
            <span style="color:{C['on_surface_var']}">{movie['runtime']}</span>
        </div>
        <div class="agenda-item" style="padding:6px 0;border-bottom:1px solid {C['outline_var']}30;">
            <b>IMDb Rating</b><br>
            <span style="color:#f5c518;font-weight:700;">{movie['imdb_rating']} / 10</span>
        </div>
        <div class="agenda-item" style="padding:6px 0;border-bottom:1px solid {C['outline_var']}30;">
            <b>Rotten Tomatoes</b><br>
            <span style="color:#ff6b35;font-weight:700;">{movie['rt_rating']}</span>
        </div>
        <div class="agenda-item" style="padding:6px 0;grid-column:1/-1;">
            <b>Cast</b><br>
            <span style="color:{C['on_surface_var']}">{movie['actors']}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='section-heading'>Debate Summary</div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='summary-box'>{result.get('debate_summary', 'Summary unavailable.')}</div>",
        unsafe_allow_html=True,
    )

    st.markdown("<div class='fancy-divider'></div>", unsafe_allow_html=True)

    # ── 3. SCORES — RING CHARTS ───────────────────────────────────
    st.markdown("<div class='section-heading'>Scores</div>", unsafe_allow_html=True)

    raw_ai_score = str(result.get("final_score", "N/A"))
    try:
        if "/" in raw_ai_score:
            ai_pct = float(raw_ai_score.split("/")[0].strip()) * 10
        else:
            ai_pct = float(re.sub(r"[^\d.]", "", raw_ai_score)) * 10
        ai_pct = min(max(ai_pct, 0), 100)
    except Exception:
        ai_pct = 0
    ai_display = raw_ai_score if raw_ai_score != "N/A" else "—"

    raw_imdb = str(movie.get("imdb_rating", "—"))
    try:
        imdb_pct = float(raw_imdb.split("/")[0] if "/" in raw_imdb else raw_imdb) * 10
        imdb_pct = min(max(imdb_pct, 0), 100)
    except Exception:
        imdb_pct = 0

    raw_rt = str(movie.get("rt_rating", "—"))
    try:
        rt_pct = float(re.sub(r"[^\d.]", "", raw_rt.split("/")[0]))
        rt_pct = min(max(rt_pct, 0), 100)
    except Exception:
        rt_pct = 0

    def ring_svg(pct, display, stroke, glow, track):
        # pathLength="100" makes stroke-dasharray directly map to 0-100%
        dash_to   = f"{pct:.1f} 100"
        dash_from = f"0 100"
        arc = (
            f'<path pathLength="100" style="fill:none;stroke:{stroke};stroke-width:2.8;'
            f'stroke-linecap:round;'
            f'filter:drop-shadow(0 0 6px {glow});'
            f'transform:rotate(-90deg);transform-origin:18px 18px;'
            f'animation:scoreAnim 1.4s cubic-bezier(0.4,0,0.2,1) forwards;"'
            f' stroke-dasharray="{dash_to}"'
            f' d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"/>'
        ) if pct > 0 else ""
        return (
            f'<svg viewBox="0 0 36 36" style="display:block;width:130px;height:130px;">'
            f'<defs><style>'
            f'@keyframes scoreAnim{{'
            f'  from{{stroke-dasharray:{dash_from}}}'
            f'  to{{stroke-dasharray:{dash_to}}}'
            f'}}'
            f'</style></defs>'
            # Track ring
            f'<path pathLength="100" style="fill:none;stroke:{track};stroke-width:3.5;"'
            f' d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"/>'
            # Filled arc
            f'{arc}'
            # Center score text
            f'<text x="18" y="19.5" style="fill:{stroke};font-family:Epilogue,sans-serif;'
            f'font-size:6.5px;font-weight:800;text-anchor:middle;letter-spacing:-0.3px;">{display}</text>'
            f'</svg>'
        )

    def score_card(svg, label):
        return (
            f'<div style="text-align:center;display:flex;flex-direction:column;align-items:center;gap:10px;">'
            f'{svg}'
            f'<div style="font-family:Epilogue,sans-serif;font-size:10px;font-weight:600;'
            f'color:#9f8e79;letter-spacing:0.15em;text-transform:uppercase;">{label}</div>'
            f'</div>'
        )

    scores_html = (
        f'<div style="display:flex;gap:52px;align-items:center;margin:20px 0 16px 0;flex-wrap:wrap;">'
        + score_card(ring_svg(ai_pct,   ai_display,       C["primary_container"],  "rgba(255,178,36,0.6)",  "rgba(255,178,36,0.12)"), "AI Verdict")
        + score_card(ring_svg(imdb_pct, raw_imdb,         "#f5c518",               "rgba(245,197,24,0.5)",  "rgba(245,197,24,0.1)"),  "IMDb")
        + score_card(ring_svg(rt_pct,   raw_rt,           "#ff6b35",               "rgba(255,107,53,0.5)",  "rgba(255,107,53,0.1)"),  "Rotten Tomatoes")
        + '</div>'
    )
    st.markdown(scores_html, unsafe_allow_html=True)

    st.markdown("<div class='fancy-divider'></div>", unsafe_allow_html=True)

    # ── 4. DEBATE TRANSCRIPT ──────────────────────────────────────
    debate = result.get("debate_transcript", [])
    if debate:
        st.markdown("<div class='section-heading'>Live Debate Transcript</div>", unsafe_allow_html=True)
        st.markdown(
            f"<p style='font-family:Epilogue,sans-serif;font-size:12px;"
            f"letter-spacing:0.06em;color:{C['text_muted']};margin-bottom:14px;text-transform:uppercase;'>"
            f"{MODEL_CRITIC} &nbsp;vs&nbsp; {MODEL_ADVOCATE} &nbsp;·&nbsp; 4 Rounds</p>",
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

    # ── 5. SCORING BASIS ──────────────────────────────────────────
    basis = result.get("scoring_basis")
    if basis:
        st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
        with st.expander("⚖ View AI Scoring Basis & Methodology"):
            st.markdown(
                f"<div style='padding:14px;font-family:Be Vietnam Pro,sans-serif;"
                f"color:{C['on_surface_var']};line-height:1.75;font-size:14px;'>"
                f"<b style='color:{C['on_surface']};'>Criteria for this Rating:</b><br><br>{basis}"
                f"<br><br>"
                f"<hr style='border:0;border-top:1px solid {C['outline_var']}40;margin:16px 0;'>"
                f"<span style='font-size:12px;color:{C['text_muted']};font-family:Epilogue,sans-serif;"
                f"letter-spacing:0.03em;'>"
                f"This score is calculated using a neutral synthesis model that evaluates conflicting "
                f"arguments from the debate, calibrated against a global 10-point scale of cinematic quality."
                f"</span></div>",
                unsafe_allow_html=True,
            )

    st.markdown("<div style='margin-bottom:100px;'></div>", unsafe_allow_html=True)