import re
import requests
import streamlit as st
import streamlit.components.v1 as components
from agent.sentiment import analyze_movie, MODEL_CRITIC, MODEL_ADVOCATE

API_KEY         = st.secrets["OMDB_API_KEY"]
YOUTUBE_API_KEY = st.secrets["YOUTUBE_API_KEY"]


# ================================================================
# THEME DESIGN TOKENS
# ================================================================

DARK = {
    "bg":               "#120c09",
    "bg_lowest":        "#0d0806",
    "bg_low":           "#1a120d",
    "bg_container":     "#201610",
    "bg_high":          "#2a1d15",
    "bg_highest":       "#36261c",
    "bg_bright":        "#423024",
    "on_surface":       "#f0e4d4",
    "on_surface_var":   "#c9b098",
    "on_primary":       "#1a0a00",
    "text_muted":       "#7a5c42",
    "text_dim":         "#3d2415",
    "primary":          "#e8833a",
    "primary_dim":      "#d4692a",
    "primary_container":"#f09050",
    "secondary":        "#c8603a",
    "tertiary":         "#f0b87a",
    "outline":          "#4a3020",
    "outline_var":      "#2e1e12",
    "glow_copper":      "rgba(232,131,58,0.14)",
    "glow_copper_md":   "rgba(232,131,58,0.26)",
    "glow_copper_btn":  "rgba(232,131,58,0.30)",
    "glow_ember":       "rgba(200,96,58,0.12)",
    "critic_color":     "#e8833a",
    "advocate_color":   "#c8a070",
    "critic_bg":        "rgba(232,131,58,0.07)",
    "advocate_bg":      "rgba(200,160,112,0.07)",
    "critic_border":    "rgba(232,131,58,0.20)",
    "advocate_border":  "rgba(200,160,112,0.20)",
    "orb1":             "#e8833a",
    "orb2":             "#c8603a",
    "orb3":             "#f0b87a",
    "orb_opacity":      "0.45",
    "orb_blend":        "screen",
    "bg_base":          "#120c09",
}

LIGHT = {
    "bg":               "#fdf6ee",
    "bg_lowest":        "#f5ece0",
    "bg_low":           "#faf2e8",
    "bg_container":     "#fff8f0",
    "bg_high":          "#f5e8d8",
    "bg_highest":       "#ecdcc8",
    "bg_bright":        "#e0cdb4",
    "on_surface":       "#2a1a0e",
    "on_surface_var":   "#5a3e28",
    "on_primary":       "#ffffff",
    "text_muted":       "#a07850",
    "text_dim":         "#c8a882",
    "primary":          "#c05a18",
    "primary_dim":      "#a84810",
    "primary_container":"#d46828",
    "secondary":        "#b04830",
    "tertiary":         "#c07828",
    "outline":          "#d4b898",
    "outline_var":      "#e8d4bc",
    "glow_copper":      "rgba(192,90,24,0.10)",
    "glow_copper_md":   "rgba(192,90,24,0.20)",
    "glow_copper_btn":  "rgba(192,90,24,0.22)",
    "glow_ember":       "rgba(176,72,48,0.08)",
    "critic_color":     "#c05a18",
    "advocate_color":   "#8a5c30",
    "critic_bg":        "rgba(192,90,24,0.06)",
    "advocate_bg":      "rgba(138,92,48,0.06)",
    "critic_border":    "rgba(192,90,24,0.18)",
    "advocate_border":  "rgba(138,92,48,0.18)",
    "orb1":             "#f5c890",
    "orb2":             "#e8a060",
    "orb3":             "#ffd8a0",
    "orb_opacity":      "0.30",
    "orb_blend":        "multiply",
    "bg_base":          "#fdf6ee",
}


# ================================================================
# SEARCH MOVIES
# ================================================================
def search_movies(query: str, media_type: str = "movie"):
    if not API_KEY:
        return [], None
    url = "http://www.omdbapi.com/"
    type_param = "movie" if media_type == "Movie" else "series"

    exact = None
    try:
        r = requests.get(url, params={"t": query, "apikey": API_KEY, "r": "json", "type": type_param}, timeout=10)
        d = r.json()
        if d.get("Response") == "True" and d.get("imdbID") and d.get("Title"):
            exact = {
                "Title":  d["Title"],
                "Year":   d.get("Year", "—"),
                "imdbID": d["imdbID"],
                "Poster": d.get("Poster", "N/A"),
                "Type":   d.get("Type", type_param),
            }
    except Exception:
        pass

    fuzzy = []
    try:
        r = requests.get(url, params={"s": query, "apikey": API_KEY, "r": "json", "type": type_param}, timeout=10)
        d = r.json()
        if d.get("Response") == "True":
            fuzzy = [item for item in d.get("Search", []) if item.get("Title") and item.get("imdbID")]
    except Exception:
        pass

    seen, merged, error_msg = set(), [], None

    if exact:
        try:
            r_plot = requests.get(url, params={"i": exact["imdbID"], "apikey": API_KEY, "plot": "short"}, timeout=5)
            d_plot = r_plot.json()
            exact["Plot"] = d_plot.get("Plot", "")
        except:
            exact["Plot"] = ""
        merged.append(exact)
        seen.add(exact["imdbID"])

    for item in fuzzy[:6]:
        iid = item.get("imdbID")
        if iid and iid not in seen:
            try:
                r_p = requests.get(url, params={"i": iid, "apikey": API_KEY, "plot": "short"}, timeout=5)
                d_p = r_p.json()
                item["Plot"] = d_p.get("Plot", "")
            except:
                item["Plot"] = ""
            merged.append(item)
            seen.add(iid)

    if not merged:
        try:
            r = requests.get(url, params={"s": query, "apikey": API_KEY, "type": type_param}, timeout=10)
            d = r.json()
            if d.get("Response") == "False":
                error_msg = d.get("Error")
        except Exception:
            pass

    return merged[:6], error_msg


# ================================================================
# FETCH MOVIE DATA BY IMDB ID
# ================================================================
def fetch_movie_by_id(imdb_id: str):
    if not API_KEY:
        return None
    url = "http://www.omdbapi.com/"
    params = {"i": imdb_id, "apikey": API_KEY, "plot": "full", "r": "json"}
    try:
        res  = requests.get(url, params=params, timeout=10)
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
        if "Rotten Tomatoes" in r.get("Source", ""):
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
# FETCH YOUTUBE TRAILER
# ================================================================
def fetch_trailer(title: str, year: str = "") -> str | None:
    if not YOUTUBE_API_KEY:
        return None
    query = f"{title} {year} official trailer".strip()
    try:
        resp = requests.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={"part": "snippet", "q": query, "type": "video", "maxResults": 1, "key": YOUTUBE_API_KEY},
            timeout=10,
        )
        data  = resp.json()
        items = data.get("items", [])
        if items:
            return items[0]["id"]["videoId"]
    except Exception:
        pass
    return None


# ================================================================
# PAGE CONFIG
# ================================================================
st.set_page_config(
    page_title="NoCap Reviews",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ================================================================
# SESSION STATE
# ================================================================
if "conversations"  not in st.session_state: st.session_state.conversations  = {}
if "active_id"      not in st.session_state: st.session_state.active_id      = None
if "search_history" not in st.session_state: st.session_state.search_history = []
if "search_results" not in st.session_state: st.session_state.search_results = []
if "last_typed"     not in st.session_state: st.session_state.last_typed     = None
if "search_error"   not in st.session_state: st.session_state.search_error   = None
if "media_type"     not in st.session_state: st.session_state.media_type     = "Movie"
if "theme"          not in st.session_state: st.session_state.theme          = "dark"

# ── resolve token map for current SSR render ────────────────────
current_theme = st.session_state.theme
C = DARK if current_theme == "dark" else LIGHT

# ── resolve sidebar icon color: near-black in light, near-white in dark ──
sidebar_icon_color = "#1a1a1a" if current_theme == "light" else "#f0f0f0"


# ================================================================
# GLOBAL CSS  (uses C tokens for SSR)
# ================================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700;0,800;1,600;1,700&family=Outfit:wght@300;400;500;600&display=swap');

/* ── ROOT CSS CUSTOM PROPERTIES ── */
:root {{
  --ncr-bg:               {C["bg"]};
  --ncr-bg-lowest:        {C["bg_lowest"]};
  --ncr-bg-low:           {C["bg_low"]};
  --ncr-bg-container:     {C["bg_container"]};
  --ncr-bg-high:          {C["bg_high"]};
  --ncr-bg-highest:       {C["bg_highest"]};
  --ncr-bg-bright:        {C["bg_bright"]};
  --ncr-on-surface:       {C["on_surface"]};
  --ncr-on-surface-var:   {C["on_surface_var"]};
  --ncr-on-primary:       {C["on_primary"]};
  --ncr-text-muted:       {C["text_muted"]};
  --ncr-text-dim:         {C["text_dim"]};
  --ncr-primary:          {C["primary"]};
  --ncr-primary-dim:      {C["primary_dim"]};
  --ncr-primary-container:{C["primary_container"]};
  --ncr-secondary:        {C["secondary"]};
  --ncr-tertiary:         {C["tertiary"]};
  --ncr-outline:          {C["outline"]};
  --ncr-outline-var:      {C["outline_var"]};
  --ncr-glow-copper:      {C["glow_copper"]};
  --ncr-glow-copper-md:   {C["glow_copper_md"]};
  --ncr-glow-copper-btn:  {C["glow_copper_btn"]};
  --ncr-critic-color:     {C["critic_color"]};
  --ncr-advocate-color:   {C["advocate_color"]};
  --ncr-critic-bg:        {C["critic_bg"]};
  --ncr-advocate-bg:      {C["advocate_bg"]};
  --ncr-critic-border:    {C["critic_border"]};
  --ncr-advocate-border:  {C["advocate_border"]};
}}

/* ── HIDE DEFAULT HEADER ── */
header[data-testid="stHeader"] {{ background: transparent !important; }}
.stApp > header {{ display: none !important; }}

/* ================================================================
   FIX 1 — SIDEBAR COLLAPSE ARROW
   Uses baked-in sidebar_icon_color (black in light, white in dark)
   so the icon is always visible regardless of theme.
================================================================ */
/* FIX — SIDEBAR COLLAPSE ARROW: black in light, white in dark */
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"] {{
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    background: {C["bg_container"]} !important;
    border: 1px solid {C["outline"]} !important;
    border-radius: 0 8px 8px 0 !important;
    box-shadow: 2px 0 12px {C["glow_copper"]} !important;
}}

[data-testid="stSidebarCollapsedControl"] button,
[data-testid="stSidebarCollapsedControl"] button:hover,
[data-testid="stSidebarCollapsedControl"] button:focus,
[data-testid="collapsedControl"] button,
[data-testid="collapsedControl"] button:hover,
[data-testid="collapsedControl"] button:focus {{
    color: {"#1a1a1a" if current_theme == "light" else "#f0f0f0"} !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    opacity: 1 !important;
    visibility: visible !important;
}}

[data-testid="stSidebarCollapsedControl"] svg,
[data-testid="stSidebarCollapsedControl"] svg *,
[data-testid="stSidebarCollapsedControl"] button svg,
[data-testid="stSidebarCollapsedControl"] button svg *,
[data-testid="collapsedControl"] svg,
[data-testid="collapsedControl"] svg *,
[data-testid="collapsedControl"] button svg,
[data-testid="collapsedControl"] button svg * {{
    fill:    {"#1a1a1a" if current_theme == "light" else "#f0f0f0"} !important;
    stroke:  {"#1a1a1a" if current_theme == "light" else "#f0f0f0"} !important;
    color:   {"#1a1a1a" if current_theme == "light" else "#f0f0f0"} !important;
    opacity: 1 !important;
    visibility: visible !important;
}}

div[data-testid="stSidebarCollapsedControl"] > div,
div[data-testid="collapsedControl"] > div {{
    background: {C["bg_container"]} !important;
    border-radius: 0 8px 8px 0 !important;
    opacity: 1 !important;
    visibility: visible !important;
}}

/* Fix toggle to top-right */
div[data-testid="column"]:last-child {{
    position: relative;
}}

div[data-testid="stButton"]:has(button#theme_toggle) {{
    position: fixed !important;
    top: 12px !important;
    left: 20px !important;
    right: auto !important;   /* IMPORTANT: kill right positioning */
    z-index: 999999 !important;
}}

/* Clean small circular button */
div[data-testid="column"]:last-child button {{
    height: 38px !important;
    width: 38px !important;
    border-radius: 50% !important;
    padding: 0 !important;
    font-size: 16px !important;

    background: var(--ncr-bg-container) !important;
    border: 1px solid var(--ncr-outline) !important;
    color: var(--ncr-primary) !important;

    display: flex !important;
    align-items: center;
    justify-content: center;
}}

/* Hover effect */
div[data-testid="column"]:last-child button:hover {{
    background: var(--ncr-critic-bg) !important;
    border-color: var(--ncr-primary) !important;
}}

.stApp {{
    background: transparent !important;
    color: var(--ncr-on-surface);
    font-family: 'Outfit', sans-serif;
}}
[data-testid="stAppViewContainer"] {{
    background: transparent !important;
}}
.block-container {{
    max-width: 1200px;
    padding-top: 0 !important;
    padding-bottom: 6rem;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
}}

/* ── GLOBAL SMOOTH TRANSITION for theme switch ── */
*, *::before, *::after {{
    transition-property: background-color, border-color, color, box-shadow, fill, stroke;
    transition-duration: 0.35s;
    transition-timing-function: ease;
}}
button, a {{ transition: all 0.22s ease !important; }}
.glow-orb {{ transition: background 0.5s ease, opacity 0.5s ease !important; }}

/* ── ANIMATED BG ── */
.cinema-bg {{
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    z-index: -999;
    background-color: {C["bg_base"]};
    overflow: hidden;
    transition: background-color 0.5s ease;
}}
.glow-orb {{
    position: absolute; border-radius: 50%;
    filter: blur(80px);
    opacity: {C["orb_opacity"]};
    mix-blend-mode: {C["orb_blend"]};
    animation: orbMove 15s ease-in-out infinite alternate;
}}
.orb-1 {{
    width: 600px; height: 600px;
    background: radial-gradient(circle, {C["orb1"]} 0%, transparent 70%);
    top: -10%; left: -10%; animation-duration: 18s;
}}
.orb-2 {{
    width: 500px; height: 500px;
    background: radial-gradient(circle, {C["orb2"]} 0%, transparent 70%);
    bottom: -10%; right: -5%; animation-delay: -5s;
}}
.orb-3 {{
    width: 400px; height: 400px;
    background: radial-gradient(circle, {C["orb3"]} 0%, transparent 70%);
    top: 40%; left: 30%; animation-duration: 22s; animation-delay: -2s;
}}
@keyframes orbMove {{
    0%   {{ transform: translate(0,0) scale(1); }}
    50%  {{ transform: translate(15%,10%) scale(1.15); }}
    100% {{ transform: translate(-10%,20%) scale(0.9); }}
}}

::-webkit-scrollbar {{ width: 5px; height: 5px; }}
::-webkit-scrollbar-track {{ background: var(--ncr-bg-lowest); }}
::-webkit-scrollbar-thumb {{ background: var(--ncr-bg-highest); border-radius: 4px; }}
::-webkit-scrollbar-thumb:hover {{ background: var(--ncr-outline); }}

h1, h2, h3, h4 {{ font-family: 'Playfair Display', serif !important; }}

/* ── HERO ── */
.hero-eyebrow {{
    font-family: 'Outfit', sans-serif; font-size: 10px; font-weight: 600;
    letter-spacing: 0.28em; color: var(--ncr-primary); text-transform: uppercase;
    text-align: center; margin-bottom: 16px; opacity: 0.9;
}}
.hero-title {{
    font-family: 'Playfair Display', serif;
    font-size: clamp(38px,5.5vw,66px); font-weight: 800;
    letter-spacing: -0.01em; line-height: 1.08;
    text-align: center; color: var(--ncr-on-surface); margin-bottom: 12px;
}}
.hero-title em {{
    font-style: italic; color: var(--ncr-primary-container);
    text-shadow: 0 0 40px var(--ncr-glow-copper-md);
}}
.hero-sub {{
    font-family: 'Outfit', sans-serif; font-size: 16px; font-weight: 300;
    color: var(--ncr-on-surface-var); text-align: center;
    max-width: 500px; margin: 0 auto 12px auto; line-height: 1.65;
}}
.hero-ornament {{
    text-align: center; font-size: 18px; color: var(--ncr-primary);
    opacity: 0.45; letter-spacing: 0.5em; margin-bottom: 8px;
}}

/* ── TYPE TOGGLE & BUTTONS ── */
div[data-testid="stButton"] > button {{
    font-family: 'Outfit', sans-serif !important;
    font-size: 12px !important; font-weight: 600 !important;
    letter-spacing: 0.18em !important; text-transform: uppercase !important;
    transition: all 0.22s ease !important;
    border: 1px solid var(--ncr-outline) !important;
    background: var(--ncr-bg-container) !important;
    color: var(--ncr-text-muted) !important;
    border-radius: 9999px !important;
    padding: 10px 30px !important; box-shadow: none !important;
}}
div[data-testid="stButton"] > button:hover {{
    border-color: var(--ncr-primary) !important;
    color: var(--ncr-primary-container) !important;
    background: var(--ncr-critic-bg) !important;
    box-shadow: 0 4px 20px var(--ncr-glow-copper) !important;
}}
div[data-testid="stButton"] > button:focus {{
    outline: none !important;
    box-shadow: 0 0 0 2px var(--ncr-glow-copper-md) !important;
}}
div[data-testid="stButton"] > button[kind="primary"] {{
    background: linear-gradient(135deg, var(--ncr-primary), var(--ncr-secondary)) !important;
    border-color: var(--ncr-primary) !important;
    color: var(--ncr-on-primary) !important;
    box-shadow: 0 4px 20px var(--ncr-glow-copper-btn) !important;
    font-size: 11px !important; letter-spacing: 0.20em !important;
    padding: 10px 28px !important;
}}
div[data-testid="stButton"] > button[kind="primary"]:hover {{
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 32px var(--ncr-glow-copper-md) !important;
    background: linear-gradient(135deg, var(--ncr-primary-container), var(--ncr-primary)) !important;
}}

/* Override global button style for the theme toggle — stays small */
.ncr-toggle-container div[data-testid="stButton"] > button {{
    padding: 3px 10px !important;
    font-size: 9px !important;
    height: 22px !important;
    min-height: 22px !important;
    letter-spacing: 0.13em !important;
    background: {C["bg_container"]} !important;
    border: 1px solid {C["outline"]} !important;
    color: {C["text_muted"]} !important;
    box-shadow: 0 2px 10px {C["glow_copper"]} !important;
}}

/* ── CHAT INPUT ── */
div[data-testid="stChatInput"] {{
    background: var(--ncr-bg-low) !important;
    border: 1px solid var(--ncr-outline) !important;
    border-radius: 9999px !important;
    box-shadow: inset 0 2px 10px rgba(0,0,0,0.15), 0 2px 20px rgba(0,0,0,0.10) !important;
    padding: 0 8px !important;
}}
div[data-testid="stChatInput"] > div,
div[data-testid="stChatInput"] div[class*="st-"] {{
    background-color: transparent !important; background: transparent !important;
    border: none !important; box-shadow: none !important;
}}
textarea[data-testid="stChatInputTextArea"] {{
    background: transparent !important; background-color: transparent !important;
    border: none !important;
    color: var(--ncr-on-surface) !important;
    -webkit-text-fill-color: var(--ncr-on-surface) !important;
    font-family: 'Outfit', sans-serif !important; font-size: 16px !important;
    padding: 14px 20px !important; box-shadow: none !important;
    caret-color: var(--ncr-primary-container) !important;
}}
textarea[data-testid="stChatInputTextArea"]::placeholder {{
    color: var(--ncr-text-muted) !important;
    -webkit-text-fill-color: var(--ncr-text-muted) !important;
}}
button[data-testid="stChatInputSubmitButton"] {{
    background: linear-gradient(135deg, var(--ncr-primary), var(--ncr-secondary)) !important;
    border-radius: 9999px !important;
    box-shadow: 0 4px 20px var(--ncr-glow-copper-btn) !important;
    margin-top: 5px !important;
}}
button[data-testid="stChatInputSubmitButton"]:hover {{
    transform: scale(1.10) !important;
    box-shadow: 0 6px 30px var(--ncr-glow-copper-md) !important;
}}
button[data-testid="stChatInputSubmitButton"] svg {{
    stroke: var(--ncr-on-primary) !important; fill: none !important;
    width: 16px !important; height: 16px !important;
}}

/* ── SEARCH LABEL ── */
.search-label {{
    font-family: 'Outfit', sans-serif; font-size: 10px; font-weight: 600;
    letter-spacing: 0.24em; text-transform: uppercase; color: var(--ncr-primary);
    margin-bottom: 18px; margin-top: 6px; opacity: 0.8;
}}

/* ── RESULT CARDS ── */
.result-card {{
    background: var(--ncr-bg-container); border: 1px solid var(--ncr-outline-var);
    border-radius: 14px; overflow: hidden; margin-bottom: 4px;
    transition: all 0.30s ease; box-shadow: 0 4px 24px rgba(0,0,0,0.08);
    display: flex; flex-direction: row;
}}
.result-card:hover {{
    background: var(--ncr-bg-high); border-color: var(--ncr-outline);
    box-shadow: 0 12px 48px -8px rgba(0,0,0,0.12), 0 0 0 1px var(--ncr-glow-copper-md);
    transform: translateY(-2px);
}}

/* ── MOVIE TITLE / META ── */
.movie-title-display {{
    font-family: 'Playfair Display', serif;
    font-size: clamp(26px,3.5vw,46px); font-weight: 800;
    letter-spacing: -0.01em; line-height: 1.08;
    color: var(--ncr-on-surface); margin-bottom: 10px;
}}
.movie-meta-inline {{
    font-family: 'Outfit', sans-serif; font-size: 13px; font-weight: 400;
    color: var(--ncr-on-surface-var); margin-bottom: 20px;
    display: flex; flex-wrap: wrap; gap: 6px 0; align-items: center;
}}
.meta-label {{ font-size: 9px; font-weight: 600; letter-spacing: 0.18em; text-transform: uppercase; color: var(--ncr-text-muted); }}
.meta-value {{ font-size: 13px; color: var(--ncr-on-surface-var); }}
.meta-value.accent {{ color: var(--ncr-primary-container); font-weight: 600; }}
.meta-sep {{ color: var(--ncr-outline); margin: 0 10px; font-size: 11px; opacity: 0.5; }}

/* ── SECTION HEADING ── */
.section-heading {{
    font-family: 'Outfit', sans-serif; font-size: 10px; font-weight: 600;
    letter-spacing: 0.24em; text-transform: uppercase; color: var(--ncr-primary);
    margin: 32px 0 14px 0; display: flex; align-items: center; gap: 10px; opacity: 0.85;
}}
.section-heading::after {{
    content: ''; flex: 1; height: 1px;
    background: linear-gradient(to right, var(--ncr-outline), transparent); opacity: 0.5;
}}

/* ── TRAILER ── */
.trailer-wrapper {{
    position: relative; width: 100%; padding-top: 56.25%;
    border-radius: 14px; overflow: hidden; background: var(--ncr-bg-lowest);
    box-shadow: 0 24px 72px -12px rgba(0,0,0,0.15),
                0 0 0 1px var(--ncr-outline),
                0 0 60px -20px var(--ncr-glow-copper-md);
}}
.trailer-wrapper iframe {{
    position: absolute; top: 0; left: 0;
    width: 100%; height: 100%; border: none; border-radius: 14px;
}}
.trailer-badge {{
    display: inline-flex; align-items: center; gap: 6px;
    background: var(--ncr-critic-bg); border: 1px solid var(--ncr-critic-border);
    color: var(--ncr-primary-container); font-family: 'Outfit', sans-serif;
    font-size: 10px; font-weight: 600; letter-spacing: 0.18em; text-transform: uppercase;
    padding: 4px 14px; border-radius: 9999px; margin-bottom: 14px;
}}
.trailer-badge::before {{ content: '▶'; font-size: 8px; color: var(--ncr-primary); }}
.trailer-no-result {{
    display: flex; align-items: center; justify-content: center;
    height: 120px; background: var(--ncr-bg-container);
    border: 1px dashed var(--ncr-outline); border-radius: 14px;
    font-family: 'Outfit', sans-serif; font-size: 13px;
    color: var(--ncr-text-muted); letter-spacing: 0.04em;
}}

/* ── AGENDA STRIP ── */
.agenda-strip {{
    display: grid; grid-template-columns: repeat(4,1fr);
    gap: 0; background: var(--ncr-bg-container);
    border: 1px solid var(--ncr-outline); border-radius: 14px;
    overflow: hidden; margin-top: 14px;
    box-shadow: 0 8px 40px rgba(0,0,0,0.08);
}}
.agenda-cell {{
    padding: 26px 24px; border-right: 1px solid var(--ncr-outline-var);
    position: relative; transition: background 0.25s ease;
}}
.agenda-cell:last-child {{ border-right: none; }}
.agenda-cell:hover {{ background: var(--ncr-critic-bg); }}
.agenda-round {{
    font-family: 'Outfit', sans-serif; font-size: 9px; font-weight: 700;
    letter-spacing: 0.22em; text-transform: uppercase;
    color: var(--ncr-primary); margin-bottom: 10px; opacity: 0.70;
}}
.agenda-num {{
    font-family: 'Playfair Display', serif; font-size: 36px; font-weight: 700;
    color: var(--ncr-bg-highest); line-height: 1; margin-bottom: 14px;
}}
.agenda-text {{
    font-family: 'Outfit', sans-serif; font-size: 13px; font-weight: 400;
    color: var(--ncr-on-surface-var); line-height: 1.6;
}}
.agenda-text b {{ color: var(--ncr-on-surface); font-weight: 600; }}

/* ── SUMMARY BOX ── */
.summary-box {{
    background: linear-gradient(135deg, var(--ncr-bg-container) 0%, var(--ncr-bg-high) 100%);
    border-left: 3px solid var(--ncr-primary);
    border-radius: 0 14px 14px 0; padding: 24px 30px;
    font-family: 'Playfair Display', serif; font-size: 17px; font-style: italic;
    color: var(--ncr-on-surface-var); line-height: 1.9;
    box-shadow: 0 4px 24px rgba(0,0,0,0.06);
}}

/* ── THEME CHIPS ── */
.theme-tag {{
    display: inline-block; background: var(--ncr-critic-bg);
    border: 1px solid var(--ncr-critic-border);
    color: var(--ncr-tertiary); font-family: 'Outfit', sans-serif;
    font-size: 12px; font-weight: 500; letter-spacing: 0.04em;
    padding: 5px 14px; border-radius: 9999px; margin: 4px 3px;
}}

/* ── DEBATE BUBBLES ── */
.debate-wrap {{ display: flex; flex-direction: column; gap: 18px; margin-top: 10px; }}
.debate-bubble {{
    padding: 18px 22px; font-family: 'Outfit', sans-serif;
    font-size: 15px; font-weight: 400; line-height: 1.75;
    max-width: 88%; color: var(--ncr-on-surface-var);
    box-shadow: 0 4px 20px rgba(0,0,0,0.06);
}}
.bubble-critic   {{ background: var(--ncr-critic-bg); border: 1px solid var(--ncr-critic-border); border-radius: 16px 16px 16px 4px; align-self: flex-start; }}
.bubble-advocate {{ background: var(--ncr-advocate-bg); border: 1px solid var(--ncr-advocate-border); border-radius: 16px 16px 4px 16px; align-self: flex-end; }}
.bubble-label {{ font-family: 'Outfit', sans-serif; font-size: 9px; font-weight: 700; letter-spacing: 0.18em; text-transform: uppercase; margin-bottom: 10px; }}
.bubble-label-critic   {{ color: var(--ncr-critic-color); }}
.bubble-label-advocate {{ color: var(--ncr-advocate-color); }}
.bubble-model-tag {{ font-size: 9px; opacity: 0.4; margin-left: 8px; letter-spacing: 0.06em; }}
.round-pill {{
    display: block; width: fit-content; font-family: 'Outfit', sans-serif;
    font-size: 9px; font-weight: 700; letter-spacing: 0.18em; text-transform: uppercase;
    background: var(--ncr-critic-bg); border: 1px solid var(--ncr-critic-border);
    color: var(--ncr-primary); padding: 3px 14px; border-radius: 9999px;
    margin: 14px auto 6px auto; text-align: center;
}}

/* ── DIVIDER ── */
.fancy-divider {{
    height: 1px;
    background: linear-gradient(to right, transparent, var(--ncr-outline), transparent);
    margin: 32px 0; opacity: 0.5;
}}

/* ── ERROR BOX ── */
.err-box {{
    background: var(--ncr-critic-bg); border: 1px solid var(--ncr-critic-border);
    border-radius: 12px; padding: 20px 28px; font-family: 'Outfit', sans-serif;
    font-size: 14px; font-weight: 500; color: var(--ncr-primary);
    text-align: center; letter-spacing: 0.02em;
}}

[data-testid="stImage"] img {{
    border-radius: 12px !important;
    box-shadow: 0 24px 72px -12px rgba(0,0,0,0.20), 0 0 50px -18px var(--ncr-glow-copper-md) !important;
}}
[data-testid="stExpander"] {{
    background: var(--ncr-bg-container) !important;
    border: 1px solid var(--ncr-outline) !important;
    border-radius: 12px !important; margin-top: 4px !important;
}}
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary p {{
    font-family: 'Outfit', sans-serif !important; font-size: 13px !important;
    font-weight: 600 !important; letter-spacing: 0.06em !important;
    color: var(--ncr-primary-container) !important;
}}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {{
    background-color: var(--ncr-bg-low) !important;
    border-right: 1px solid var(--ncr-outline) !important;
}}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{
    padding-top: 2rem !important; gap: 0.5rem !important;
}}

p, li, div {{ font-size: 15px; }}
</style>
""", unsafe_allow_html=True)


# ================================================================
# SIDEBAR
# ================================================================
with st.sidebar:
    st.markdown(f"<div class='hero-eyebrow' style='text-align:left;'>Collection</div>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='color:{C['on_surface']}; margin-top:0;'>Your Archive</h3>", unsafe_allow_html=True)

    if not st.session_state.conversations:
        st.markdown(f"<div style='color:{C['text_muted']}; font-size:13px;'>Analyzed movies will appear here.</div>", unsafe_allow_html=True)

    for imdb_id, data in st.session_state.conversations.items():
        if st.button(f"🎬 {data['movie']['title']}", key=f"nav_{imdb_id}", use_container_width=True):
            st.session_state.active_id = imdb_id
            st.session_state.search_results = []
            st.rerun()


# ================================================================
# BACKGROUND ORBS
# ================================================================
st.markdown(f"""
    <div class="cinema-bg">
        <div class="glow-orb orb-1"></div>
        <div class="glow-orb orb-2"></div>
        <div class="glow-orb orb-3"></div>
    </div>
""", unsafe_allow_html=True)

st.markdown("<div style='height:2.5rem'></div>", unsafe_allow_html=True)
st.markdown("<div class='hero-eyebrow'>⬡ Curated by AI · Two Models · One Verdict</div>", unsafe_allow_html=True)
st.markdown("<div class='hero-title'>NoCap <em>Reviews</em></div>", unsafe_allow_html=True)
st.markdown(
    "<div class='hero-sub'>Search any film or series — a Critic and an Advocate debate it across four rounds, then deliver a calibrated verdict.</div>",
    unsafe_allow_html=True,
)
st.markdown("<div class='hero-ornament'>— ✦ —</div>", unsafe_allow_html=True)


# ================================================================
# THEME TOGGLE — fixed top-right, small pill
# Inject fixed-position wrapper, render button, then JS-reparent it.
# Raised to top: 6px, shrunk to height: 22px.
# ================================================================
toggle_icon  = "☀️" if current_theme == "dark" else "🌙"
toggle_label = "Light" if current_theme == "dark" else "Dark"
next_theme   = "light" if current_theme == "dark" else "dark"

st.markdown(f"""
<style>
.ncr-toggle-container {{
    position: fixed !important;
    top: 6px !important;
    right: 20px !important;
    z-index: 999999 !important;
    width: auto !important;
    height: auto !important;
    display: flex !important;
    align-items: center !important;
}}

.ncr-toggle-container div[data-testid="stButton"] > button:hover {{
    border-color: {C["primary"]} !important;
    color: {C["primary_container"]} !important;
    background: {C["critic_bg"]} !important;
    box-shadow: 0 4px 18px {C["glow_copper_md"]} !important;
    transform: translateY(-1px) !important;
}}

</style>

""", unsafe_allow_html=True)


# TOP RIGHT TOGGLE (NO JS NEEDED)
col1, col2 = st.columns([10, 1])

with col2:
    if st.button(f"{toggle_icon}", key="theme_toggle"):
        st.session_state.theme = next_theme
        st.rerun()


# ================================================================
# SEARCH UI: Type Toggle → Search Bar
# ================================================================
show_search_ui = not st.session_state.active_id
active_type    = st.session_state.media_type

if show_search_ui:
    active_idx = 1 if active_type == "Movie" else 2
    st.markdown(f"""
    <style>
    div[data-testid="stHorizontalBlock"] div[data-testid="column"]:nth-child({active_idx})
        div[data-testid="stButton"] > button {{
        background: linear-gradient(135deg, {C["primary"]}, {C["secondary"]}) !important;
        border-color: {C["primary"]} !important;
        color: {C["on_primary"]} !important;
        box-shadow: 0 4px 22px {C["glow_copper_btn"]} !important;
    }}
    </style>
    <div style="height:4px;"></div>
    """, unsafe_allow_html=True)

    _, col_t1, col_t2, _ = st.columns([2, 1, 1, 2])
    with col_t1:
        if st.button("Movie", key="btn_type_movie", use_container_width=True):
            st.session_state.media_type = "Movie"
            st.rerun()
    with col_t2:
        if st.button("Series", key="btn_type_series", use_container_width=True):
            st.session_state.media_type = "Series"
            st.rerun()

    st.markdown(f"""
    <div style="display:flex;justify-content:center;margin:-4px 0 22px 0;">
        <div style="display:flex;width:280px;gap:10px;">
            <div style="flex:1;height:2px;border-radius:2px;
                background:{'linear-gradient(90deg,' + C['primary'] + ',' + C['secondary'] + ')' if active_type=='Movie' else C['bg_highest']};"></div>
            <div style="flex:1;height:2px;border-radius:2px;
                background:{'linear-gradient(90deg,' + C['primary'] + ',' + C['secondary'] + ')' if active_type=='Series' else C['bg_highest']};"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

c1, c2, c3 = st.columns([1, 2.6, 1])
with c2:
    placeholder = (
        f"Search a {st.session_state.media_type.lower()} title, e.g. Oppenheimer…"
        if show_search_ui else "Search another title…"
    )
    user_input = st.chat_input(placeholder)

st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)


# ================================================================
# HANDLE SEARCH INPUT
# ================================================================
if user_input and user_input.strip():
    if user_input != st.session_state.last_typed:
        st.session_state.last_typed = user_input
        st.session_state.active_id  = None
        with st.spinner("Searching the archive…"):
            results, err = search_movies(user_input, st.session_state.media_type)
            st.session_state.search_results = results
            st.session_state.search_error   = err
        st.rerun()


# ================================================================
# RESULTS — CARDS
# ================================================================
search_results = st.session_state.search_results

if search_results and not st.session_state.active_id:
    n = len(search_results[:6])
    st.markdown(
        f"<div class='search-label'>▸ {n} result{'s' if n != 1 else ''} found — select a title to start the AI debate</div>",
        unsafe_allow_html=True,
    )

    for i, item in enumerate(search_results[:6]):
        poster  = item.get("Poster", "N/A")
        title   = item.get("Title", "Unknown")
        year    = item.get("Year", "")
        imdb_id = item.get("imdbID", "")
        itype   = item.get("Type", "movie").title()
        has_poster = poster and poster != "N/A" and poster.startswith("http")

        poster_bg   = f"url('{poster}')" if has_poster else "none"
        placeholder = "" if has_poster else "<div style=\"font-size:34px;opacity:0.18;\">🎬</div>"

        desc_text = item.get("Plot") or "A Critic and an Advocate will debate this title across four rounds and deliver a calibrated verdict."
        if len(desc_text) > 135:
            desc_text = desc_text[:132] + "..."

        card_html = f"""
<!DOCTYPE html><html>
<head>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Outfit:wght@300;400;600&display=swap" rel="stylesheet">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:transparent; font-family:'Outfit',sans-serif; }}
  .card {{
    display:flex; background:{C["bg_container"]};
    border:1px solid {C["outline_var"]}; border-radius:14px;
    overflow:hidden; min-height:200px; box-shadow:0 4px 24px rgba(0,0,0,0.08);
  }}
  .poster {{
    width:140px; min-width:140px; min-height:200px; flex-shrink:0;
    position:relative; background-image:{poster_bg}; background-size:cover;
    background-position:center top; background-repeat:no-repeat;
    background-color:{C["bg_high"]}; display:flex; align-items:center; justify-content:center;
  }}
  .poster-fade {{
    position:absolute; top:0; left:0; right:0; bottom:0;
    background:linear-gradient(to right,transparent 60%,{C["bg_container"]} 100%);
  }}
  .body {{ flex:1; padding:20px 24px 18px 18px; display:flex; flex-direction:column; justify-content:space-between; min-width:0; }}
  .title {{ font-family:'Playfair Display',serif; font-size:21px; font-weight:700; color:{C["on_surface"]}; line-height:1.2; margin-bottom:8px; }}
  .desc {{ font-size:13px; font-weight:300; color:{C["on_surface_var"]}; opacity:0.75; line-height:1.65; margin-bottom:12px; }}
  .badge {{ display:inline-block; font-size:9px; font-weight:600; letter-spacing:0.14em; text-transform:uppercase; padding:4px 11px; border-radius:3px; margin-right:5px; }}
  .badge-type {{ background:{C["critic_bg"]}; color:{C["primary"]}; border:1px solid {C["critic_border"]}; }}
  .badge-year {{ background:rgba(74,48,32,0.12); color:{C["tertiary"]}; border:1px solid {C["outline"]}; }}
</style>
</head>
<body>
<div class="card">
  <div class="poster">{placeholder}<div class="poster-fade"></div></div>
  <div class="body">
    <div>
      <div class="title">{title}</div>
      <div class="desc">{desc_text}</div>
    </div>
    <div>
      <span class="badge badge-type">{itype}</span>
      <span class="badge badge-year">{year}</span>
    </div>
  </div>
</div>
</body></html>"""

        components.html(card_html, height=215, scrolling=False)

        if st.button(f"▶  Analyse · {title}", key=f"sel_{imdb_id}_{i}", use_container_width=True, type="primary"):
            with st.spinner("Generating AI Debate..."):
                movie_data = fetch_movie_by_id(imdb_id)
                trailer_id = fetch_trailer(movie_data["title"], movie_data.get("year", ""))
                raw_reviews = {
                    "title":              movie_data["title"],
                    "critic_reviews":     movie_data["plot"],
                    "audience_reactions": movie_data["actors"],
                    "discussion_points":  movie_data["genre"],
                }
                debate_result = analyze_movie(raw_reviews)
                st.session_state.conversations[imdb_id] = {
                    "movie":   movie_data,
                    "result":  debate_result,
                    "trailer": trailer_id
                }
                if title not in st.session_state.search_history:
                    st.session_state.search_history.insert(0, title)
                st.session_state.active_id = imdb_id
                st.session_state.search_results = []
                st.rerun()

        st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

    st.markdown("<div class='fancy-divider'></div>", unsafe_allow_html=True)


# ================================================================
# RESOLVE ACTIVE DATA
# ================================================================
if st.session_state.active_id and st.session_state.active_id in st.session_state.conversations:
    active_data = st.session_state.conversations[st.session_state.active_id]
    movie   = active_data["movie"]
    result  = active_data["result"]
    trailer = active_data["trailer"]
else:
    movie, result, trailer = None, None, None


# ================================================================
# ERROR STATE
# ================================================================
if (
    st.session_state.last_typed is not None
    and not search_results
    and not movie
    and not st.session_state.active_id
):
    err_msg = st.session_state.get("search_error") or "No results found. Try a different title or spelling."
    st.markdown(f"<div class='err-box'>⚠ &nbsp; {err_msg}</div>", unsafe_allow_html=True)


# ================================================================
# RENDER ANALYSIS
# ================================================================
elif st.session_state.active_id and st.session_state.active_id in st.session_state.conversations:

    # ── MOVIE HEADER ───────────────────────────────────────────
    col_poster, col_info = st.columns([1, 2.8], gap="large")

    with col_poster:
        if movie["poster"] and movie["poster"] != "N/A":
            st.image(movie["poster"], use_column_width=True)

    with col_info:
        st.markdown(f"<div class='movie-title-display'>{movie['title']}</div>", unsafe_allow_html=True)

        director_val = movie.get("director") or "—"
        year_val     = movie.get("year")     or "—"
        runtime_val  = movie.get("runtime")  or "—"
        actors_val   = movie.get("actors")   or "—"

        st.markdown(f"""
        <div class="movie-meta-inline">
            <span style="display:inline-flex;align-items:center;gap:4px;">
                <span class="meta-label">Dir.</span>
                <span class="meta-value accent">&nbsp;{director_val}</span>
            </span>
            <span class="meta-sep">·</span>
            <span style="display:inline-flex;align-items:center;gap:4px;">
                <span class="meta-label">Year</span>
                <span class="meta-value">&nbsp;{year_val}</span>
            </span>
            <span class="meta-sep">·</span>
            <span style="display:inline-flex;align-items:center;gap:4px;">
                <span class="meta-label">Runtime</span>
                <span class="meta-value">&nbsp;{runtime_val}</span>
            </span>
        </div>
        <div style="font-family:'Outfit',sans-serif;font-size:11px;
                    letter-spacing:0.08em;color:{C['text_muted']};margin-bottom:18px;font-weight:500;">
            CAST &nbsp;·&nbsp; {actors_val}
        </div>
        """, unsafe_allow_html=True)

        themes = result.get("themes", [])
        if themes:
            st.markdown("<div class='section-heading' style='margin-top:10px;'>Core Themes</div>", unsafe_allow_html=True)
            tags_html = "".join(f"<span class='theme-tag'>#{t.strip()}</span>" for t in themes)
            st.markdown(f"<div style='line-height:2.6;margin-bottom:8px;'>{tags_html}</div>", unsafe_allow_html=True)

        st.markdown("<div class='section-heading'>Overview</div>", unsafe_allow_html=True)
        st.markdown(
            f"<p style='font-family:Outfit,sans-serif;font-size:15px;font-weight:300;"
            f"color:{C['on_surface_var']};line-height:1.85;margin-top:0;'>{movie['plot']}</p>",
            unsafe_allow_html=True,
        )

    # ── TRAILER ──────────────────────────────────────────────
    st.markdown("<div class='fancy-divider'></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-heading'>Official Trailer</div>", unsafe_allow_html=True)
    st.markdown("<div class='trailer-badge'>Watch Trailer</div>", unsafe_allow_html=True)

    if trailer:
        st.markdown(
            f"""<div class="trailer-wrapper">
                <iframe src="https://www.youtube.com/embed/{trailer}?rel=0&modestbranding=1&color=white"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowfullscreen></iframe>
            </div>""",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div class='trailer-no-result'>🎬 &nbsp; Trailer not available for this title</div>",
            unsafe_allow_html=True,
        )

    # ── DEBATE AGENDA ─────────────────────────────────────────
    st.markdown("<div class='section-heading'>The Debate Agenda</div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class="agenda-strip">
        <div class="agenda-cell">
            <div class="agenda-round">Round 01</div><div class="agenda-num">01</div>
            <div class="agenda-text"><b>Opening Statements</b><br>Initial critical assessment versus a contrarian defence of the film's core premise and intent</div>
        </div>
        <div class="agenda-cell">
            <div class="agenda-round">Round 02</div><div class="agenda-num">02</div>
            <div class="agenda-text"><b>Craft &amp; Vision</b><br>Deep dive into cinematography, direction, character arcs, score, and the film's technical artistry</div>
        </div>
        <div class="agenda-cell">
            <div class="agenda-round">Round 03</div><div class="agenda-num">03</div>
            <div class="agenda-text"><b>Rebuttals</b><br>Pacing critiques, narrative coherence, thematic depth, and competing views on cultural legacy</div>
        </div>
        <div class="agenda-cell">
            <div class="agenda-round">Round 04</div><div class="agenda-num">04</div>
            <div class="agenda-text"><b>Final Synthesis</b><br>Nuanced convergence delivering a calibrated score on a global 10-point cinematic quality scale</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='fancy-divider'></div>", unsafe_allow_html=True)

    # ── DEBATE SUMMARY ────────────────────────────────────────
    st.markdown("<div class='section-heading'>Debate Summary</div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='summary-box'>{result.get('debate_summary', 'Summary unavailable.')}</div>",
        unsafe_allow_html=True,
    )

    st.markdown("<div class='fancy-divider'></div>", unsafe_allow_html=True)

    # ── SCORES ────────────────────────────────────────────────
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
        filled = round(pct, 2)
        gap    = round(CIRC - filled, 2)
        aname  = f"scoreAnim_{anim_id}"
        return f"""
<svg viewBox="0 0 36 36" style="display:block;width:130px;height:130px;">
  <defs><style>
    @keyframes {aname} {{
      from {{ stroke-dasharray: 0 {CIRC}; }}
      to   {{ stroke-dasharray: {filled} {gap}; }}
    }}
  </style></defs>
  <circle cx="18" cy="18" r="15.9155" style="fill:none;stroke:{track};stroke-width:3.2;"/>
  <circle cx="18" cy="18" r="15.9155"
    style="fill:none;stroke:{stroke};stroke-width:2.6;stroke-linecap:round;
           filter:drop-shadow(0 0 6px {glow});
           transform:rotate(-90deg);transform-origin:18px 18px;
           stroke-dasharray:{filled} {gap};
           animation:{aname} 1.4s cubic-bezier(0.4,0,0.2,1) forwards;"/>
  <text x="18" y="19.5"
    style="fill:{stroke};font-family:Playfair Display,serif;
           font-size:6.5px;font-weight:700;text-anchor:middle;letter-spacing:-0.3px;">{display}</text>
</svg>"""

    def score_card(svg, label):
        return (
            f'<div style="text-align:center;display:flex;flex-direction:column;align-items:center;gap:10px;">'
            f'{svg}'
            f'<div style="font-family:Outfit,sans-serif;font-size:9px;font-weight:600;'
            f'color:{C["text_muted"]};letter-spacing:0.20em;text-transform:uppercase;">{label}</div>'
            f'</div>'
        )

    scores_html = (
        f'<div style="display:flex;gap:52px;align-items:center;margin:20px 0 16px 0;flex-wrap:wrap;">'
        + score_card(ring_svg(ai_pct,   ai_display, C["primary"],  "rgba(232,131,58,0.55)", C["bg_highest"], "ai"),   "AI Verdict")
        + score_card(ring_svg(imdb_pct, raw_imdb,   "#e8b84a",     "rgba(232,184,74,0.45)", C["bg_highest"], "imdb"), "IMDb")
        + score_card(ring_svg(rt_pct,   raw_rt,     "#e86040",     "rgba(232,96,64,0.45)",  C["bg_highest"], "rt"),   "Rotten Tomatoes")
        + '</div>'
    )
    st.markdown(scores_html, unsafe_allow_html=True)

    st.markdown("<div class='fancy-divider'></div>", unsafe_allow_html=True)

    # ── DEBATE TRANSCRIPT ─────────────────────────────────────
    debate = result.get("debate_transcript", [])
    if debate:
        st.markdown("<div class='section-heading'>Live Debate Transcript</div>", unsafe_allow_html=True)
        st.markdown(
            f"<p style='font-family:Outfit,sans-serif;font-size:11px;"
            f"letter-spacing:0.08em;color:{C['text_muted']};margin-bottom:14px;"
            f"text-transform:uppercase;font-weight:500;'>"
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

    # ── SCORING BASIS ─────────────────────────────────────────
    basis = result.get("scoring_basis")
    if basis:
        st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
        with st.expander("⚖ View AI Scoring Basis & Methodology"):
            st.markdown(
                f"<div style='padding:14px;font-family:Outfit,sans-serif;"
                f"color:{C['on_surface_var']};line-height:1.75;font-size:14px;font-weight:400;'>"
                f"<b style='color:{C['on_surface']};font-weight:600;'>Criteria for this Rating:</b><br><br>{basis}"
                f"<br><br>"
                f"<hr style='border:0;border-top:1px solid {C['outline']}60;margin:16px 0;'>"
                f"<span style='font-size:12px;color:{C['text_muted']};font-family:Outfit,sans-serif;"
                f"letter-spacing:0.03em;font-weight:400;'>"
                f"This score is calculated using a neutral synthesis model that evaluates conflicting "
                f"arguments from the debate, calibrated against a global 10-point scale of cinematic quality."
                f"</span></div>",
                unsafe_allow_html=True,
            )

    st.markdown("<div style='margin-bottom:100px;'></div>", unsafe_allow_html=True)