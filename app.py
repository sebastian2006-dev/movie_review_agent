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

    director = data.get("Director", "")
    if not director or director == "N/A":
        director = "—"

    return {
        "title":       data.get("Title"),
        "year":        data.get("Year"),
        "plot":        data.get("Plot"),
        "actors":      data.get("Actors"),
        "genre":       data.get("Genre"),
        "director":    director,
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
# WARM PARCHMENT LIGHT — DESIGN TOKENS
# ================================================================
C = {
    # Surfaces — warm cream / parchment scale
    "bg":               "#fdf6ec",   # warm cream page
    "bg_lowest":        "#fef9f3",   # lightest wash
    "bg_low":           "#f9f0e1",   # soft parchment
    "bg_container":     "#f4e8d4",   # card background
    "bg_high":          "#ecdcc5",   # deeper parchment
    "bg_highest":       "#e0ccb0",   # rich tan
    "bg_bright":        "#d9c4a0",   # warm linen

    # Text — warm ink scale
    "on_surface":       "#2e1f0a",   # dark espresso ink
    "on_surface_var":   "#4d3520",   # warm brown
    "on_primary":       "#fff8ee",   # light text on accent
    "text_muted":       "#9e7a52",   # warm taupe
    "text_dim":         "#c8a87a",   # faded amber

    # Primaries / Accents — warm amber / sienna
    "primary":          "#c45e00",   # rich sienna
    "primary_dim":      "#e07020",   # warm amber-orange
    "primary_container":"#b5440e",   # deep burnt sienna
    "secondary":        "#9b5a1a",   # warm chestnut
    "tertiary":         "#d4824a",   # terracotta
    "outline":          "#c8a87a",   # warm tan border
    "outline_var":      "#ddc9a8",   # soft parchment border

    # Glow helpers — warm amber
    "glow_amber":       "rgba(196,94,0,0.10)",
    "glow_amber_md":    "rgba(196,94,0,0.18)",
    "glow_amber_btn":   "rgba(196,94,0,0.20)",
    "glow_orange":      "rgba(212,130,74,0.12)",

    # Debate personas
    "critic_color":     "#b5440e",
    "advocate_color":   "#7a4a1e",
    "critic_bg":        "rgba(181,68,14,0.06)",
    "advocate_bg":      "rgba(122,74,30,0.06)",
    "critic_border":    "rgba(181,68,14,0.20)",
    "advocate_border":  "rgba(122,74,30,0.20)",
}

# ================================================================
# GLOBAL CSS — WARM PARCHMENT LIGHT DESIGN SYSTEM
# ================================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400;1,600&family=DM+Sans:wght@400;500&display=swap');

/* ── Reset sidebar toggle ── */
[data-testid="stSidebarCollapsedControl"] {{ display: none !important; }}
header[data-testid="stHeader"] {{ background: transparent !important; }}
.stApp > header {{ display: none !important; }}

/* ── App Shell ── */
.stApp {{
    background-color: {C["bg"]} !important;
    color: {C["on_surface"]};
    font-family: 'DM Sans', sans-serif;
}}
.block-container {{
    max-width: 1200px;
    padding-top: 0 !important;
    padding-bottom: 6rem;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
}}

/* ── Ambient warm paper texture overlay ── */
.stApp::before {{
    content: '';
    position: fixed;
    inset: 0;
    z-index: -1;
    background:
        radial-gradient(ellipse 75% 60% at 10% 0%,   rgba(212,170,100,0.22) 0%, transparent 60%),
        radial-gradient(ellipse 55% 50% at 90% 90%,  rgba(196,94,0,0.10)   0%, transparent 55%),
        radial-gradient(ellipse 40% 40% at 55% 45%,  rgba(255,220,160,0.12) 0%, transparent 65%);
    pointer-events: none;
}}

/* ── Scrollbar ── */
::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: {C["bg_low"]}; }}
::-webkit-scrollbar-thumb {{ background: {C["outline"]}; border-radius: 4px; }}
::-webkit-scrollbar-thumb:hover {{ background: {C["primary_dim"]}; }}

h1, h2, h3, h4 {{ font-family: 'Cormorant Garamond', serif !important; }}

/* ════════════════════════════════════════
   HERO / PAGE HEADER
════════════════════════════════════════ */
.hero-eyebrow {{
    font-family: 'DM Sans', sans-serif;
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.22em;
    color: {C["primary"]};
    text-transform: uppercase;
    text-align: center;
    margin-bottom: 14px;
    opacity: 0.85;
}}
.hero-title {{
    font-family: 'Cormorant Garamond', serif;
    font-size: clamp(40px, 5.5vw, 68px);
    font-weight: 700;
    letter-spacing: -0.01em;
    line-height: 1.1;
    text-align: center;
    color: {C["on_surface"]};
    margin-bottom: 10px;
}}
.hero-title em {{
    font-style: italic;
    color: {C["primary_container"]};
}}
.hero-sub {{
    font-family: 'DM Sans', sans-serif;
    font-size: 16px;
    color: {C["on_surface_var"]};
    text-align: center;
    max-width: 520px;
    margin: 0 auto 36px auto;
    line-height: 1.65;
    font-weight: 400;
}}

/* Thin warm rule under hero */
.hero-rule {{
    width: 64px;
    height: 2px;
    background: linear-gradient(to right, {C["primary_container"]}, {C["primary_dim"]});
    border-radius: 9999px;
    margin: 0 auto 36px auto;
    opacity: 0.6;
}}

/* ════════════════════════════════════════
   CHAT INPUT — WARM RECESSED FIELD
════════════════════════════════════════ */
div[data-testid="stChatInput"],
.stChatInput {{
    background: {C["bg_low"]} !important;
    border: 1.5px solid {C["outline_var"]} !important;
    border-radius: 9999px !important;
    box-shadow: inset 0 2px 6px rgba(100,60,0,0.06), 0 2px 12px rgba(180,100,20,0.06) !important;
    padding-right: 8px !important;
    padding-left: 8px !important;
    transition: border-color 0.3s ease, box-shadow 0.3s ease !important;
}}
div[data-testid="stChatInput"]:focus-within,
.stChatInput:focus-within {{
    border-color: {C["primary"]}60 !important;
    box-shadow: inset 0 2px 6px rgba(100,60,0,0.06), 0 0 24px {C["glow_amber"]} !important;
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
    font-family: 'DM Sans', sans-serif !important;
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
    box-shadow: 0 4px 16px {C["glow_amber_btn"]} !important;
    transition: all 0.2s ease !important;
    flex-shrink: 0 !important;
    margin-top: 4px !important;
}}
button[data-testid="stChatInputSubmitButton"]:hover {{
    background: {C["primary_dim"]} !important;
    box-shadow: 0 6px 24px {C["glow_amber_md"]} !important;
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
    font-family: 'DM Sans', sans-serif;
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.20em;
    text-transform: uppercase;
    color: {C["primary"]};
    margin-bottom: 18px;
    margin-top: 6px;
    opacity: 0.8;
}}

div[data-testid="column"] img {{
    border-radius: 10px !important;
    display: block !important;
    cursor: pointer !important;
    transition: transform 0.3s ease, box-shadow 0.3s ease !important;
    box-shadow: 0 4px 20px rgba(100,50,0,0.12) !important;
}}
div[data-testid="column"] img:hover {{
    transform: scale(1.04) !important;
    box-shadow: 0 14px 40px -6px rgba(180,80,20,0.22) !important;
}}

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
    background: rgba(196,94,0,0.04) !important;
}}

/* ════════════════════════════════════════
   MOVIE DETAIL — TITLE / META
════════════════════════════════════════ */
.movie-title-display {{
    font-family: 'Cormorant Garamond', serif;
    font-size: clamp(28px, 3.5vw, 48px);
    font-weight: 700;
    letter-spacing: -0.01em;
    line-height: 1.1;
    color: {C["on_surface"]};
    margin-bottom: 8px;
}}
.movie-meta-inline {{
    font-family: 'DM Sans', sans-serif;
    font-size: 14px;
    color: {C["on_surface_var"]};
    margin-bottom: 20px;
    display: flex;
    flex-wrap: wrap;
    gap: 6px 0;
    align-items: center;
    line-height: 1.8;
}}
.movie-meta-inline .meta-item {{
    display: inline-flex;
    align-items: center;
    gap: 4px;
}}
.movie-meta-inline .meta-label {{
    font-family: 'DM Sans', sans-serif;
    font-size: 10px;
    font-weight: 500;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: {C["text_muted"]};
}}
.movie-meta-inline .meta-value {{
    font-size: 14px;
    color: {C["on_surface_var"]};
}}
.movie-meta-inline .meta-value.accent {{
    color: {C["primary_container"]};
    font-weight: 600;
}}
.meta-sep {{
    color: {C["outline"]};
    margin: 0 10px;
    font-size: 12px;
    opacity: 0.5;
}}

/* ════════════════════════════════════════
   SECTION HEADING
════════════════════════════════════════ */
.section-heading {{
    font-family: 'DM Sans', sans-serif;
    font-size: 10px;
    font-weight: 500;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: {C["primary"]};
    margin: 32px 0 14px 0;
    display: flex;
    align-items: center;
    gap: 10px;
    opacity: 0.85;
}}
.section-heading::after {{
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(to right, {C["outline_var"]}, transparent);
}}

/* ════════════════════════════════════════
   AGENDA / INFO CARD
════════════════════════════════════════ */
.agenda-card {{
    background: {C["bg_container"]};
    border: 1px solid {C["outline_var"]};
    border-radius: 12px;
    padding: 20px 24px;
    margin-top: 18px;
    box-shadow: 0 4px 20px rgba(120,70,10,0.07);
}}
.agenda-title {{
    font-family: 'DM Sans', sans-serif;
    font-size: 10px;
    font-weight: 500;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: {C["primary"]};
    margin-bottom: 12px;
    opacity: 0.8;
}}
.agenda-item {{
    font-family: 'DM Sans', sans-serif;
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
    background: linear-gradient(135deg, {C["bg_container"]} 0%, {C["bg_high"]}80 100%);
    border-left: 3px solid {C["primary_container"]};
    border-radius: 0 12px 12px 0;
    padding: 22px 28px;
    font-family: 'Cormorant Garamond', serif;
    font-size: 17px;
    color: {C["on_surface_var"]};
    line-height: 1.85;
    box-shadow: 0 4px 18px rgba(120,70,10,0.08);
}}

/* ════════════════════════════════════════
   THEME CHIPS
════════════════════════════════════════ */
.theme-tag {{
    display: inline-block;
    background: rgba(181,68,14,0.07);
    border: 1px solid rgba(181,68,14,0.22);
    color: {C["primary_container"]};
    font-family: 'DM Sans', sans-serif;
    font-size: 12px;
    font-weight: 500;
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
    font-family: 'DM Sans', sans-serif;
    font-size: 15px;
    line-height: 1.75;
    max-width: 88%;
    color: {C["on_surface_var"]};
    box-shadow: 0 3px 14px rgba(120,70,10,0.07);
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
    font-family: 'DM Sans', sans-serif;
    font-size: 10px;
    font-weight: 500;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    margin-bottom: 10px;
}}
.bubble-label-critic   {{ color: {C["critic_color"]}; }}
.bubble-label-advocate {{ color: {C["advocate_color"]}; }}
.bubble-model-tag {{
    font-family: 'DM Sans', sans-serif;
    font-size: 10px;
    opacity: 0.45;
    margin-left: 8px;
    letter-spacing: 0.05em;
}}
.round-pill {{
    display: block;
    width: fit-content;
    font-family: 'DM Sans', sans-serif;
    font-size: 10px;
    font-weight: 500;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    background: rgba(181,68,14,0.08);
    border: 1px solid rgba(181,68,14,0.22);
    color: {C["primary"]};
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
    background: linear-gradient(to right, transparent, {C["outline_var"]}, transparent);
    margin: 32px 0;
}}

/* ════════════════════════════════════════
   ERROR BOX
════════════════════════════════════════ */
.err-box {{
    background: rgba(196,94,0,0.05);
    border: 1px solid rgba(196,94,0,0.18);
    border-radius: 12px;
    padding: 20px 28px;
    font-family: 'DM Sans', sans-serif;
    font-size: 14px;
    font-weight: 500;
    color: {C["primary"]};
    text-align: center;
    letter-spacing: 0.02em;
}}

/* ════════════════════════════════════════
   POSTER IMAGE
════════════════════════════════════════ */
[data-testid="stImage"] img {{
    border-radius: 12px !important;
    box-shadow: 0 20px 56px -12px rgba(100,50,0,0.25),
                0 0 32px -12px rgba(196,94,0,0.12) !important;
}}

/* ════════════════════════════════════════
   EXPANDERS
════════════════════════════════════════ */
[data-testid="stExpander"] {{
    background: {C["bg_container"]} !important;
    border: 1px solid {C["outline_var"]} !important;
    border-radius: 12px !important;
    margin-top: 4px !important;
}}
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary p {{
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    letter-spacing: 0.04em !important;
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
# HERO SECTION
# ================================================================
st.markdown("<div style='height:2.5rem'></div>", unsafe_allow_html=True)
st.markdown("<div class='hero-eyebrow'>⬡ Curated by AI · Two Models · One Verdict</div>", unsafe_allow_html=True)
st.markdown("<div class='hero-title'>Movie Review <em>Agent</em></div>", unsafe_allow_html=True)
st.markdown("<div class='hero-rule'></div>", unsafe_allow_html=True)
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
                        f"<div style='height:300px;background:{C['bg_high']};border-radius:10px;"
                        f"display:flex;align-items:center;justify-content:center;"
                        f"font-size:42px;cursor:pointer;'>🎬</div>",
                        unsafe_allow_html=True,
                    )
            else:
                st.markdown(
                    f"<div style='height:300px;background:{C['bg_high']};border-radius:10px;"
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
        # Title
        st.markdown(f"<div class='movie-title-display'>{movie['title']}</div>", unsafe_allow_html=True)

        # Inline meta: Director · Year · Runtime · Cast
        director_val = movie.get("director") or "—"
        year_val     = movie.get("year")     or "—"
        runtime_val  = movie.get("runtime")  or "—"
        actors_val   = movie.get("actors")   or "—"

        st.markdown(f"""
        <div class="movie-meta-inline">
            <span class="meta-item">
                <span class="meta-label">Dir.</span>
                <span class="meta-value accent">&nbsp;{director_val}</span>
            </span>
            <span class="meta-sep">·</span>
            <span class="meta-item">
                <span class="meta-label">Year</span>
                <span class="meta-value">&nbsp;{year_val}</span>
            </span>
            <span class="meta-sep">·</span>
            <span class="meta-item">
                <span class="meta-label">Runtime</span>
                <span class="meta-value">&nbsp;{runtime_val}</span>
            </span>
        </div>
        <div style="font-family:'DM Sans',sans-serif;font-size:12px;
                    letter-spacing:0.06em;color:{C['text_muted']};margin-bottom:18px;">
            CAST &nbsp;·&nbsp; {actors_val}
        </div>
        """, unsafe_allow_html=True)

        # ── CORE THEMES ───────────────────────────────────────────
        themes = result.get("themes", [])
        if themes:
            st.markdown("<div class='section-heading' style='margin-top:10px;'>Core Themes</div>", unsafe_allow_html=True)
            tags_html = "".join(
                f"<span class='theme-tag'>#{t.strip()}</span>"
                for t in themes
            )
            st.markdown(f"<div style='line-height:2.6;margin-bottom:8px;'>{tags_html}</div>", unsafe_allow_html=True)

        # ── OVERVIEW ─────────────────────────────────────────────
        st.markdown("<div class='section-heading'>Overview</div>", unsafe_allow_html=True)
        st.markdown(
            f"<p style='font-family:Cormorant Garamond,serif;font-size:17px;"
            f"color:{C['on_surface_var']};line-height:1.85;margin-top:0;'>{movie['plot']}</p>",
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

    st.markdown("<div class='fancy-divider'></div>", unsafe_allow_html=True)

    # ── DEBATE SUMMARY ────────────────────────────────────────────
    st.markdown("<div class='section-heading'>Debate Summary</div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='summary-box'>{result.get('debate_summary', 'Summary unavailable.')}</div>",
        unsafe_allow_html=True,
    )

    st.markdown("<div class='fancy-divider'></div>", unsafe_allow_html=True)

    # ── SCORES — RING CHARTS ──────────────────────────────────────
    st.markdown("<div class='section-heading'>Scores</div>", unsafe_allow_html=True)

    raw_ai_score = str(result.get("final_score", "N/A"))
    try:
        if "/" in raw_ai_score:
            ai_num = float(raw_ai_score.split("/")[0].strip())
            ai_den = float(raw_ai_score.split("/")[1].strip())
            ai_pct = (ai_num / ai_den) * 100
        else:
            ai_num = float(re.sub(r"[^\d.]", "", raw_ai_score))
            ai_pct = ai_num * 10
        ai_pct = min(max(ai_pct, 0), 100)
    except Exception:
        ai_pct = 0
    ai_display = raw_ai_score if raw_ai_score != "N/A" else "—"

    raw_imdb = str(movie.get("imdb_rating", "—"))
    try:
        imdb_num = float(raw_imdb.split("/")[0] if "/" in raw_imdb else raw_imdb)
        imdb_pct = (imdb_num / 10) * 100
        imdb_pct = min(max(imdb_pct, 0), 100)
    except Exception:
        imdb_pct = 0

    raw_rt = str(movie.get("rt_rating", "—"))
    try:
        rt_num = float(re.sub(r"[^\d.]", "", raw_rt.split("/")[0]))
        rt_pct = min(max(rt_num, 0), 100)
    except Exception:
        rt_pct = 0

    CIRC = 100.0

    def ring_svg(pct, display, stroke, glow, track, anim_id):
        filled   = round(pct, 2)
        gap      = round(CIRC - filled, 2)
        anim_name = f"scoreAnim_{anim_id}"
        return f"""
<svg viewBox="0 0 36 36" style="display:block;width:130px;height:130px;">
  <defs>
    <style>
      @keyframes {anim_name} {{
        from {{ stroke-dasharray: 0 {CIRC}; }}
        to   {{ stroke-dasharray: {filled} {gap}; }}
      }}
    </style>
  </defs>
  <circle cx="18" cy="18" r="15.9155"
    style="fill:none;stroke:{track};stroke-width:3.5;"/>
  <circle cx="18" cy="18" r="15.9155"
    style="fill:none;
           stroke:{stroke};
           stroke-width:2.8;
           stroke-linecap:round;
           filter:drop-shadow(0 0 5px {glow});
           transform:rotate(-90deg);
           transform-origin:18px 18px;
           stroke-dasharray:{filled} {gap};
           animation:{anim_name} 1.4s cubic-bezier(0.4,0,0.2,1) forwards;"/>
  <text x="18" y="19.5"
    style="fill:{stroke};
           font-family:Cormorant Garamond,serif;
           font-size:6.5px;
           font-weight:700;
           text-anchor:middle;
           letter-spacing:-0.3px;">{display}</text>
</svg>"""

    def score_card(svg, label):
        return (
            f'<div style="text-align:center;display:flex;flex-direction:column;align-items:center;gap:10px;">'
            f'{svg}'
            f'<div style="font-family:DM Sans,sans-serif;font-size:10px;font-weight:500;'
            f'color:{C["text_muted"]};letter-spacing:0.18em;text-transform:uppercase;">{label}</div>'
            f'</div>'
        )

    scores_html = (
        f'<div style="display:flex;gap:52px;align-items:center;margin:20px 0 16px 0;flex-wrap:wrap;">'
        + score_card(ring_svg(ai_pct,   ai_display, C["primary_container"], "rgba(181,68,14,0.5)",  C["outline_var"], "ai"),   "AI Verdict")
        + score_card(ring_svg(imdb_pct, raw_imdb,   "#b07800",              "rgba(176,120,0,0.4)",  C["outline_var"],  "imdb"), "IMDb")
        + score_card(ring_svg(rt_pct,   raw_rt,     "#c04020",              "rgba(192,64,32,0.4)",  C["outline_var"],  "rt"),   "Rotten Tomatoes")
        + '</div>'
    )
    st.markdown(scores_html, unsafe_allow_html=True)

    st.markdown("<div class='fancy-divider'></div>", unsafe_allow_html=True)

    # ── DEBATE TRANSCRIPT ─────────────────────────────────────────
    debate = result.get("debate_transcript", [])
    if debate:
        st.markdown("<div class='section-heading'>Live Debate Transcript</div>", unsafe_allow_html=True)
        st.markdown(
            f"<p style='font-family:DM Sans,sans-serif;font-size:12px;"
            f"letter-spacing:0.07em;color:{C['text_muted']};margin-bottom:14px;text-transform:uppercase;'>"
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

    # ── SCORING BASIS ─────────────────────────────────────────────
    basis = result.get("scoring_basis")
    if basis:
        st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
        with st.expander("⚖ View AI Scoring Basis & Methodology"):
            st.markdown(
                f"<div style='padding:14px;font-family:DM Sans,sans-serif;"
                f"color:{C['on_surface_var']};line-height:1.75;font-size:14px;'>"
                f"<b style='color:{C['on_surface']};'>Criteria for this Rating:</b><br><br>{basis}"
                f"<br><br>"
                f"<hr style='border:0;border-top:1px solid {C['outline_var']};margin:16px 0;'>"
                f"<span style='font-size:12px;color:{C['text_muted']};font-family:DM Sans,sans-serif;"
                f"letter-spacing:0.03em;'>"
                f"This score is calculated using a neutral synthesis model that evaluates conflicting "
                f"arguments from the debate, calibrated against a global 10-point scale of cinematic quality."
                f"</span></div>",
                unsafe_allow_html=True,
            )

    st.markdown("<div style='margin-bottom:100px;'></div>", unsafe_allow_html=True)