import re
import requests
import streamlit as st
from agent.sentiment import analyze_movie, MODEL_CRITIC, MODEL_ADVOCATE

API_KEY         = st.secrets["OMDB_API_KEY"]
YOUTUBE_API_KEY = st.secrets["YOUTUBE_API_KEY"]


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


# ---------------- FETCH YOUTUBE TRAILER ----------------
def fetch_trailer(title: str, year: str = "") -> str | None:
    if not YOUTUBE_API_KEY:
        return None
    query = f"{title} {year} official trailer".strip()
    try:
        resp = requests.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={
                "part":       "snippet",
                "q":          query,
                "type":       "video",
                "maxResults": 1,
                "key":        YOUTUBE_API_KEY,
            },
            timeout=10,
        )
        data = resp.json()
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
    page_title="CineGlow · Movie Review Agent",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ================================================================
# SESSION STATE
# ================================================================
if "cached_query"       not in st.session_state: st.session_state.cached_query     = None
if "cached_movie"       not in st.session_state: st.session_state.cached_movie     = None
if "cached_result"      not in st.session_state: st.session_state.cached_result    = None
if "cached_trailer"     not in st.session_state: st.session_state.cached_trailer   = None
if "search_results"     not in st.session_state: st.session_state.search_results   = []
if "selected_imdb_id"   not in st.session_state: st.session_state.selected_imdb_id = None
if "last_typed"         not in st.session_state: st.session_state.last_typed       = None
if "search_error"       not in st.session_state: st.session_state.search_error     = None
if "filter_genre"       not in st.session_state: st.session_state.filter_genre     = []
if "filter_polar"       not in st.session_state: st.session_state.filter_polar     = []

# ================================================================
# DARK VELVET CINEMA — DESIGN TOKENS
# ================================================================
C = {
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
}

# ================================================================
# GLOBAL CSS
# ================================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700;0,800;1,600;1,700&family=Outfit:wght@300;400;500;600&family=Space+Grotesk:wght@400;500;600&display=swap');

[data-testid="stSidebarCollapsedControl"] {{ display: none !important; }}
header[data-testid="stHeader"] {{ background: transparent !important; }}
.stApp > header {{ display: none !important; }}

.stApp {{
    background-color: {C["bg"]} !important;
    color: {C["on_surface"]};
    font-family: 'Outfit', sans-serif;
}}
.block-container {{
    max-width: 1280px;
    padding-top: 0 !important;
    padding-bottom: 6rem;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
}}

.stApp::before {{
    content: '';
    position: fixed;
    inset: 0;
    z-index: -1;
    background:
        radial-gradient(ellipse 65% 50% at 8% 0%,    rgba(232,131,58,0.13)  0%, transparent 60%),
        radial-gradient(ellipse 45% 40% at 92% 95%,  rgba(200,96,58,0.10)   0%, transparent 55%),
        radial-gradient(ellipse 30% 30% at 50% 55%,  rgba(240,144,80,0.05)  0%, transparent 65%),
        radial-gradient(ellipse 80% 20% at 50% 100%, rgba(42,29,21,0.80)    0%, transparent 80%);
    pointer-events: none;
}}

::-webkit-scrollbar {{ width: 5px; height: 5px; }}
::-webkit-scrollbar-track {{ background: {C["bg_lowest"]}; }}
::-webkit-scrollbar-thumb {{ background: {C["bg_highest"]}; border-radius: 4px; }}
::-webkit-scrollbar-thumb:hover {{ background: {C["outline"]}; }}

h1, h2, h3, h4 {{ font-family: 'Playfair Display', serif !important; }}

/* ── TOPNAV ── */
.cineglow-nav {{
    position: fixed; top: 0; left: 0; width: 100%; z-index: 999;
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 3rem; height: 68px;
    background: rgba(18,12,9,0.88);
    backdrop-filter: blur(20px);
    border-bottom: 1px solid rgba(232,131,58,0.08);
    box-shadow: 0 2px 30px rgba(0,0,0,0.5);
}}
.cineglow-nav-logo {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 18px; font-weight: 700;
    letter-spacing: 0.22em; text-transform: uppercase;
    color: {C["on_surface"]};
}}
.cineglow-nav-links {{
    display: flex; gap: 2rem; align-items: center;
}}
.cineglow-nav-links a {{
    font-family: 'Outfit', sans-serif; font-size: 13px;
    color: {C["text_muted"]}; text-decoration: none;
    letter-spacing: 0.04em; transition: color 0.2s ease;
}}
.cineglow-nav-links a:hover {{ color: {C["on_surface_var"]}; }}

/* ── HERO SEARCH SECTION ── */
.search-hero {{
    text-align: center;
    padding: 6rem 0 3rem 0;
}}
.search-hero-title {{
    font-family: 'Playfair Display', serif;
    font-size: clamp(42px, 6vw, 72px);
    font-weight: 800; letter-spacing: -0.02em; line-height: 1.08;
    color: {C["on_surface"]}; margin-bottom: 14px;
}}
.search-hero-sub {{
    font-family: 'Outfit', sans-serif; font-style: italic;
    font-size: 17px; font-weight: 300;
    color: {C["on_surface_var"]}; margin-bottom: 40px;
}}

/* ── SEARCH BAR ── */
.search-bar-wrap {{
    position: relative; max-width: 820px; margin: 0 auto;
}}
.search-bar-glow {{
    position: absolute; inset: -2px;
    background: linear-gradient(135deg, rgba(232,131,58,0.18), rgba(200,96,58,0.10));
    border-radius: 9999px; filter: blur(6px);
    opacity: 0; transition: opacity 0.4s ease;
}}
.search-bar-glow.active {{ opacity: 1; }}

/* Override Streamlit chat input to look like the archive search bar */
div[data-testid="stChatInput"] {{
    background: {C["bg_low"]} !important;
    border: 1px solid rgba(74,48,32,0.6) !important;
    border-radius: 9999px !important;
    box-shadow: inset 0 2px 12px rgba(0,0,0,0.5), 0 4px 24px rgba(0,0,0,0.4) !important;
    padding: 0 10px 0 20px !important;
    max-width: 820px !important;
    margin: 0 auto !important;
}}
div[data-testid="stChatInput"] > div,
div[data-testid="stChatInput"] div[class*="st-"] {{
    background-color: transparent !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}}
textarea[data-testid="stChatInputTextArea"] {{
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
    color: {C["on_surface"]} !important;
    -webkit-text-fill-color: {C["on_surface"]} !important;
    font-family: 'Playfair Display', serif !important;
    font-size: 22px !important;
    font-weight: 600 !important;
    padding: 18px 8px 18px 44px !important;
    box-shadow: none !important;
    caret-color: {C["primary_container"]} !important;
}}
textarea[data-testid="stChatInputTextArea"]::placeholder {{
    color: {C["text_muted"]} !important;
    -webkit-text-fill-color: {C["text_muted"]} !important;
    font-weight: 400 !important;
    font-style: italic !important;
}}
div[data-testid="stChatInput"] div:focus-within {{
    border: none !important; outline: none !important; box-shadow: none !important;
}}
button[data-testid="stChatInputSubmitButton"] {{
    background: linear-gradient(135deg, {C["primary"]}, {C["secondary"]}) !important;
    border-radius: 9999px !important;
    min-width: 90px; height: 42px;
    box-shadow: 0 4px 20px {C["glow_copper_btn"]} !important;
    margin: 8px !important;
    padding: 0 20px !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 11px !important; font-weight: 700 !important;
    letter-spacing: 0.18em !important;
    color: {C["on_primary"]} !important;
    transition: all 0.25s ease !important;
}}
button[data-testid="stChatInputSubmitButton"]:hover {{
    transform: scale(1.06) !important;
    box-shadow: 0 6px 32px {C["glow_copper_md"]} !important;
}}
button[data-testid="stChatInputSubmitButton"] svg {{
    display: none !important;
}}

/* ── SEARCH ICON PSEUDO-OVERLAY ── */
.search-icon-overlay {{
    position: absolute;
    left: calc(50% - 390px + 20px);
    top: 50%; transform: translateY(-50%);
    color: {C["text_muted"]};
    font-size: 18px;
    pointer-events: none;
    z-index: 100;
}}

/* ── RESULTS LAYOUT ── */
.results-layout {{
    display: grid;
    grid-template-columns: 260px 1fr;
    gap: 32px;
    margin-top: 48px;
    align-items: start;
}}

/* ── SIDEBAR FILTERS ── */
.filter-sidebar {{
    position: sticky; top: 88px;
}}
.filter-section {{
    margin-bottom: 36px;
}}
.filter-label {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 10px; font-weight: 600;
    letter-spacing: 0.22em; text-transform: uppercase;
    color: {C["text_muted"]}; margin-bottom: 16px;
    display: block;
}}
.filter-checkbox-row {{
    display: flex; align-items: center; gap: 12px;
    margin-bottom: 12px; cursor: pointer;
}}
.filter-checkbox {{
    width: 18px; height: 18px;
    border: 1px solid {C["outline"]};
    border-radius: 3px;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0; transition: border-color 0.2s ease;
}}
.filter-checkbox.checked {{
    background: {C["secondary"]};
    border-color: {C["secondary"]};
}}
.filter-checkbox-label {{
    font-family: 'Outfit', sans-serif; font-size: 14px;
    color: {C["on_surface_var"]};
}}
.genre-pills {{ display: flex; flex-wrap: wrap; gap: 8px; }}
.genre-pill {{
    padding: 6px 14px;
    border: 1px solid {C["outline"]};
    border-radius: 9999px;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 10px; font-weight: 600;
    letter-spacing: 0.14em; text-transform: uppercase;
    color: {C["on_surface_var"]}; cursor: pointer;
    transition: all 0.2s ease;
    background: transparent;
}}
.genre-pill.active {{
    border-color: {C["primary"]};
    color: {C["primary_container"]};
    background: rgba(232,131,58,0.10);
}}
.recent-item {{
    display: flex; align-items: center; gap: 12px;
    padding: 12px; border-radius: 8px;
    background: {C["bg_container"]};
    border: 1px solid transparent;
    margin-bottom: 8px; cursor: pointer;
    transition: all 0.2s ease;
}}
.recent-item:hover {{ border-color: rgba(74,48,32,0.5); background: {C["bg_high"]}; }}
.recent-icon {{
    color: {C["secondary"]}; font-size: 16px; flex-shrink: 0;
}}
.recent-title {{
    font-family: 'Outfit', sans-serif; font-size: 13px; font-weight: 500;
    color: {C["on_surface_var"]}; white-space: nowrap; overflow: hidden;
    text-overflow: ellipsis;
}}
.recent-score {{
    font-family: 'Space Grotesk', sans-serif; font-size: 9px;
    letter-spacing: 0.14em; color: {C["text_muted"]};
    text-transform: uppercase;
}}

/* ── RESULTS PANEL ── */
.results-header {{
    display: flex; align-items: center; justify-content: space-between;
    border-bottom: 1px solid rgba(74,48,32,0.3);
    padding-bottom: 16px; margin-bottom: 24px;
}}
.results-header-title {{
    font-family: 'Playfair Display', serif;
    font-size: 28px; font-weight: 700;
    color: {C["on_surface"]};
}}
.results-count {{
    font-family: 'Space Grotesk', sans-serif; font-size: 10px;
    font-weight: 600; letter-spacing: 0.18em; text-transform: uppercase;
    color: {C["text_muted"]};
}}

/* ── RESULT CARD ── */
.result-card {{
    display: flex; position: relative;
    background: {C["bg_container"]};
    border: 1px solid rgba(74,48,32,0.25);
    border-radius: 12px; overflow: hidden;
    margin-bottom: 20px;
    transition: all 0.4s ease;
    cursor: pointer;
    box-shadow: 0 4px 24px rgba(0,0,0,0.4);
}}
.result-card:hover {{
    background: {C["bg_high"]};
    border-color: rgba(232,131,58,0.22);
    box-shadow: 0 12px 48px -8px rgba(0,0,0,0.6),
                0 0 0 1px rgba(232,131,58,0.12);
    transform: translateY(-2px);
}}
.result-poster {{
    width: 160px; min-height: 240px; flex-shrink: 0;
    position: relative; overflow: hidden;
    background: {C["bg_high"]};
}}
.result-poster img {{
    width: 100%; height: 100%; object-fit: cover;
    filter: grayscale(0.3);
    transition: filter 0.6s ease;
}}
.result-card:hover .result-poster img {{ filter: grayscale(0); }}
.result-poster-fade {{
    position: absolute; inset: 0;
    background: linear-gradient(to right, transparent 70%, {C["bg_container"]} 100%);
    pointer-events: none;
}}
.result-no-poster {{
    width: 100%; height: 100%;
    display: flex; align-items: center; justify-content: center;
    font-size: 40px; color: {C["text_dim"]};
}}
.result-body {{
    flex: 1; padding: 28px 28px 24px 28px;
    display: flex; flex-direction: column; justify-content: space-between;
}}
.result-title-row {{
    display: flex; align-items: flex-start; justify-content: space-between;
    margin-bottom: 8px; gap: 16px;
}}
.result-title {{
    font-family: 'Playfair Display', serif;
    font-size: 24px; font-weight: 700;
    color: {C["on_surface"]}; line-height: 1.15;
    transition: color 0.2s ease;
}}
.result-card:hover .result-title {{ color: {C["primary_container"]}; }}
.result-meta {{
    font-family: 'Outfit', sans-serif; font-size: 13px;
    color: {C["on_surface_var"]}; margin-bottom: 16px;
    letter-spacing: 0.02em;
}}
.result-excerpt {{
    font-family: 'Outfit', sans-serif; font-size: 14px; font-weight: 300;
    color: rgba(201,176,152,0.7); line-height: 1.7;
    display: -webkit-box; -webkit-line-clamp: 2;
    -webkit-box-orient: vertical; overflow: hidden;
    margin-bottom: 18px;
}}
.result-badges {{ display: flex; gap: 8px; flex-wrap: wrap; }}
.result-badge {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 9px; font-weight: 600;
    letter-spacing: 0.16em; text-transform: uppercase;
    padding: 4px 12px; border-radius: 3px;
}}
.badge-genre {{
    background: rgba(74,48,32,0.5);
    color: {C["tertiary"]};
    border: 1px solid rgba(74,48,32,0.8);
}}
.badge-type {{
    background: rgba(232,131,58,0.10);
    color: {C["primary"]};
    border: 1px solid rgba(232,131,58,0.25);
}}

/* Score ring */
.score-ring-wrap {{
    position: relative; width: 56px; height: 56px;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
}}
.score-ring-wrap svg {{
    position: absolute; inset: 0; width: 100%; height: 100%;
    transform: rotate(-90deg);
}}
.score-ring-label {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 11px; font-weight: 600;
    color: {C["on_surface"]}; z-index: 1; position: relative;
}}

/* ── RESULT CARD BUTTON INVISIBLE OVERLAY ── */
div[data-testid="column"] div[data-testid="stButton"] > button.card-btn {{
    position: absolute; inset: 0;
    background: transparent !important;
    border: none !important;
    color: transparent !important;
    border-radius: 12px !important;
    z-index: 20;
}}

/* ── ERROR BOX ── */
.err-box {{
    background: rgba(232,131,58,0.06); border: 1px solid rgba(232,131,58,0.18);
    border-radius: 12px; padding: 20px 28px;
    font-family: 'Outfit', sans-serif; font-size: 14px; font-weight: 500;
    color: {C["primary"]}; text-align: center; letter-spacing: 0.02em;
}}

/* ── FANCY DIVIDER ── */
.fancy-divider {{
    height: 1px;
    background: linear-gradient(to right, transparent, {C["outline"]}70, transparent);
    margin: 32px 0;
}}

/* ── MOVIE TITLE / META ── */
.movie-title-display {{
    font-family: 'Playfair Display', serif;
    font-size: clamp(26px, 3.5vw, 46px); font-weight: 800;
    letter-spacing: -0.01em; line-height: 1.08;
    color: {C["on_surface"]}; margin-bottom: 10px;
}}
.movie-meta-inline {{
    font-family: 'Outfit', sans-serif; font-size: 13px; font-weight: 400;
    color: {C["on_surface_var"]}; margin-bottom: 20px;
    display: flex; flex-wrap: wrap; gap: 6px 0; align-items: center;
}}
.meta-label {{
    font-size: 9px; font-weight: 600; letter-spacing: 0.18em;
    text-transform: uppercase; color: {C["text_muted"]};
}}
.meta-value {{ font-size: 13px; color: {C["on_surface_var"]}; }}
.meta-value.accent {{ color: {C["primary_container"]}; font-weight: 600; }}
.meta-sep {{ color: {C["outline"]}; margin: 0 10px; font-size: 11px; opacity: 0.5; }}

/* ── SECTION HEADING ── */
.section-heading {{
    font-family: 'Outfit', sans-serif; font-size: 10px; font-weight: 600;
    letter-spacing: 0.24em; text-transform: uppercase; color: {C["primary"]};
    margin: 32px 0 14px 0; display: flex; align-items: center; gap: 10px; opacity: 0.85;
}}
.section-heading::after {{
    content: ''; flex: 1; height: 1px;
    background: linear-gradient(to right, {C["outline"]}80, transparent);
}}

/* ── TRAILER ── */
.trailer-wrapper {{
    position: relative; width: 100%; padding-top: 56.25%;
    border-radius: 14px; overflow: hidden;
    background: {C["bg_lowest"]};
    box-shadow: 0 24px 72px -12px rgba(0,0,0,0.75),
                0 0 0 1px {C["outline"]},
                0 0 60px -20px rgba(232,131,58,0.20);
}}
.trailer-wrapper iframe {{
    position: absolute; top: 0; left: 0;
    width: 100%; height: 100%; border: none; border-radius: 14px;
}}
.trailer-badge {{
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(232,131,58,0.10);
    border: 1px solid rgba(232,131,58,0.25);
    color: {C["primary_container"]};
    font-family: 'Outfit', sans-serif; font-size: 10px; font-weight: 600;
    letter-spacing: 0.18em; text-transform: uppercase;
    padding: 4px 14px; border-radius: 9999px; margin-bottom: 14px;
}}
.trailer-badge::before {{ content: '▶'; font-size: 8px; color: {C["primary"]}; }}
.trailer-no-result {{
    display: flex; align-items: center; justify-content: center;
    height: 120px; background: {C["bg_container"]};
    border: 1px dashed {C["outline"]}; border-radius: 14px;
    font-family: 'Outfit', sans-serif; font-size: 13px;
    color: {C["text_muted"]}; letter-spacing: 0.04em;
}}

/* ── AGENDA STRIP ── */
.agenda-strip {{
    display: grid; grid-template-columns: repeat(4, 1fr);
    gap: 0; background: {C["bg_container"]};
    border: 1px solid {C["outline"]}; border-radius: 14px;
    overflow: hidden; margin-top: 14px;
    box-shadow: 0 8px 40px rgba(0,0,0,0.45), inset 0 1px 0 rgba(232,131,58,0.08);
    width: 100%;
}}
.agenda-cell {{
    padding: 26px 24px; border-right: 1px solid {C["outline_var"]};
    position: relative; transition: background 0.25s ease;
}}
.agenda-cell:last-child {{ border-right: none; }}
.agenda-cell:hover {{ background: rgba(232,131,58,0.05); }}
.agenda-round {{
    font-family: 'Outfit', sans-serif; font-size: 9px; font-weight: 700;
    letter-spacing: 0.22em; text-transform: uppercase;
    color: {C["primary"]}; margin-bottom: 10px; opacity: 0.70;
}}
.agenda-num {{
    font-family: 'Playfair Display', serif; font-size: 36px; font-weight: 700;
    color: {C["bg_highest"]}; line-height: 1; margin-bottom: 14px;
    letter-spacing: -0.02em;
}}
.agenda-text {{
    font-family: 'Outfit', sans-serif; font-size: 13px; font-weight: 400;
    color: {C["on_surface_var"]}; line-height: 1.6;
}}
.agenda-text b {{ color: {C["on_surface"]}; font-weight: 600; }}

/* ── SUMMARY BOX ── */
.summary-box {{
    background: linear-gradient(135deg, {C["bg_container"]} 0%, {C["bg_high"]}80 100%);
    border-left: 3px solid {C["primary"]};
    border-radius: 0 14px 14px 0; padding: 24px 30px;
    font-family: 'Playfair Display', serif; font-size: 17px; font-style: italic;
    color: {C["on_surface_var"]}; line-height: 1.9;
    box-shadow: 0 4px 24px rgba(0,0,0,0.35);
}}

/* ── THEME CHIPS ── */
.theme-tag {{
    display: inline-block;
    background: rgba(232,131,58,0.08); border: 1px solid rgba(232,131,58,0.22);
    color: {C["tertiary"]}; font-family: 'Outfit', sans-serif;
    font-size: 12px; font-weight: 500; letter-spacing: 0.04em;
    padding: 5px 14px; border-radius: 9999px; margin: 4px 3px;
}}

/* ── DEBATE BUBBLES ── */
.debate-wrap {{ display: flex; flex-direction: column; gap: 18px; margin-top: 10px; }}
.debate-bubble {{
    padding: 18px 22px; font-family: 'Outfit', sans-serif;
    font-size: 15px; font-weight: 400; line-height: 1.75;
    max-width: 88%; color: {C["on_surface_var"]};
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}}
.bubble-critic  {{ background: {C["critic_bg"]}; border: 1px solid {C["critic_border"]}; border-radius: 16px 16px 16px 4px; align-self: flex-start; }}
.bubble-advocate{{ background: {C["advocate_bg"]}; border: 1px solid {C["advocate_border"]}; border-radius: 16px 16px 4px 16px; align-self: flex-end; }}
.bubble-label {{ font-family: 'Outfit', sans-serif; font-size: 9px; font-weight: 700; letter-spacing: 0.18em; text-transform: uppercase; margin-bottom: 10px; }}
.bubble-label-critic   {{ color: {C["critic_color"]}; }}
.bubble-label-advocate {{ color: {C["advocate_color"]}; }}
.bubble-model-tag {{ font-size: 9px; opacity: 0.4; margin-left: 8px; letter-spacing: 0.06em; }}
.round-pill {{
    display: block; width: fit-content;
    font-family: 'Outfit', sans-serif; font-size: 9px; font-weight: 700;
    letter-spacing: 0.18em; text-transform: uppercase;
    background: rgba(232,131,58,0.09); border: 1px solid rgba(232,131,58,0.25);
    color: {C["primary"]}; padding: 3px 14px; border-radius: 9999px;
    margin: 14px auto 6px auto; text-align: center;
}}

[data-testid="stImage"] img {{
    border-radius: 12px !important;
    box-shadow: 0 24px 72px -12px rgba(0,0,0,0.75), 0 0 50px -18px {C["glow_copper_md"]} !important;
}}

[data-testid="stExpander"] {{
    background: {C["bg_container"]} !important; border: 1px solid {C["outline"]} !important;
    border-radius: 12px !important; margin-top: 4px !important;
}}
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary p {{
    font-family: 'Outfit', sans-serif !important; font-size: 13px !important;
    font-weight: 600 !important; letter-spacing: 0.06em !important;
    color: {C["primary_container"]} !important;
}}

p, li, div {{ font-size: 15px; }}
</style>
""", unsafe_allow_html=True)


# ================================================================
# TOP NAV
# ================================================================
st.markdown(f"""
<div class="cineglow-nav">
    <div class="cineglow-nav-logo">✦ CineGlow</div>
    <div class="cineglow-nav-links">
        <a href="#">Archive</a>
        <a href="#">Live Debates</a>
        <a href="#">Agent Intel</a>
        <a href="#">Collections</a>
    </div>
    <div style="width:28px;height:28px;border-radius:50%;border:1px solid {C['outline']};
                display:flex;align-items:center;justify-content:center;color:{C['text_muted']};
                font-size:16px;">⊙</div>
</div>
<div style="height:68px;"></div>
""", unsafe_allow_html=True)


# ================================================================
# SEARCH HERO + CHAT INPUT
# ================================================================
show_search = not st.session_state.selected_imdb_id or not st.session_state.cached_movie

if show_search:
    st.markdown("""
    <div class="search-hero">
        <div class="search-hero-title">Search the Archive</div>
        <div class="search-hero-sub">Interrogate the agentic consciousness on cinematic history.</div>
    </div>
    """, unsafe_allow_html=True)

    # Centered search input
    _, col_search, _ = st.columns([1, 3, 1])
    with col_search:
        # Search icon overlay
        st.markdown(f"""
        <div style="position:relative;">
            <div style="position:absolute;left:22px;top:50%;transform:translateY(-50%);
                        color:{C['text_muted']};font-size:18px;z-index:100;pointer-events:none;
                        line-height:1;">🔍</div>
        </div>
        """, unsafe_allow_html=True)
        user_input = st.chat_input("Explore titles, directors, or thematic conflicts…")
else:
    user_input = None
    _, col_search, _ = st.columns([1, 3, 1])
    with col_search:
        user_input = st.chat_input("Search another film…")


# ================================================================
# HANDLE SEARCH INPUT
# ================================================================
if user_input and user_input.strip():
    if user_input != st.session_state.last_typed:
        st.session_state.last_typed       = user_input
        st.session_state.selected_imdb_id = None
        st.session_state.cached_movie     = None
        st.session_state.cached_result    = None
        st.session_state.cached_trailer   = None
        with st.spinner("Searching the archive…"):
            results, err = search_movies(user_input)
            st.session_state.search_results = results
            st.session_state.search_error   = err
        st.rerun()


# ================================================================
# HELPER: SCORE RING SVG (for result cards)
# ================================================================
def score_ring_html(score_str, size=56):
    """Returns a score ring HTML element."""
    try:
        num = float(re.sub(r"[^\d.]", "", score_str.split("/")[0]))
        pct = min(max((num / 10) * 100, 0), 100) if num <= 10 else min(max(num, 0), 100)
    except Exception:
        pct = 0
    circ = 100.0
    r = 45
    dasharray = round((pct / 100) * (2 * 3.14159 * r / 2), 2)  # simplified
    filled = round(pct, 2)
    gap    = round(circ - filled, 2)
    return f"""
<div class="score-ring-wrap" style="width:{size}px;height:{size}px;">
  <svg viewBox="0 0 36 36" style="width:{size}px;height:{size}px;transform:rotate(-90deg);">
    <circle cx="18" cy="18" r="15.9" fill="none"
      stroke="{C['bg_highest']}" stroke-width="2.8"/>
    <circle cx="18" cy="18" r="15.9" fill="none"
      stroke="{C['primary']}" stroke-width="2.2"
      stroke-linecap="round"
      stroke-dasharray="{filled} {gap}"
      style="filter:drop-shadow(0 0 5px rgba(232,131,58,0.55));"/>
  </svg>
  <span class="score-ring-label" style="font-size:{max(9, size//5)}px;">{score_str}</span>
</div>"""


# ================================================================
# RESULTS GRID — NEW STITCH-STYLE LAYOUT
# ================================================================
search_results = st.session_state.search_results

if search_results and not st.session_state.selected_imdb_id:
    n = len(search_results[:6])

    # Two-column layout: sidebar + results
    col_sidebar, col_results = st.columns([1, 3.2], gap="large")

    with col_sidebar:
        st.markdown(f"""
        <div class="filter-sidebar">
            <div class="filter-section">
                <span class="filter-label">Polarization Level</span>
                <div class="filter-checkbox-row">
                    <div class="filter-checkbox">
                        <div style="width:10px;height:10px;background:{C['secondary']};border-radius:2px;opacity:0;"></div>
                    </div>
                    <span class="filter-checkbox-label">High Conflict</span>
                </div>
                <div class="filter-checkbox-row">
                    <div class="filter-checkbox checked">
                        <div style="width:10px;height:10px;background:{C['on_primary']};border-radius:2px;"></div>
                    </div>
                    <span class="filter-checkbox-label" style="color:{C['on_surface']};">Critical Consensus</span>
                </div>
                <div class="filter-checkbox-row">
                    <div class="filter-checkbox">
                        <div style="width:10px;height:10px;background:{C['secondary']};border-radius:2px;opacity:0;"></div>
                    </div>
                    <span class="filter-checkbox-label">Agentic Anomaly</span>
                </div>
            </div>
            <div class="filter-section">
                <span class="filter-label">Genre</span>
                <div class="genre-pills">
                    <span class="genre-pill active">Drama</span>
                    <span class="genre-pill">Sci-Fi</span>
                    <span class="genre-pill">Noir</span>
                    <span class="genre-pill">Action</span>
                    <span class="genre-pill">Horror</span>
                    <span class="genre-pill">Comedy</span>
                </div>
            </div>
            <div class="filter-section">
                <span class="filter-label">Recent Intelligence</span>
        """, unsafe_allow_html=True)

        # Recent items (show first 2 results as "recent" placeholders)
        for item in search_results[:2]:
            t = item.get("Title", "Unknown")
            y = item.get("Year", "")
            st.markdown(f"""
            <div class="recent-item">
                <span class="recent-icon">⟳</span>
                <div style="flex:1;overflow:hidden;">
                    <div class="recent-title">{t}</div>
                    <div class="recent-score">Year · {y}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div></div>", unsafe_allow_html=True)

    with col_results:
        st.markdown(f"""
        <div class="results-header">
            <div class="results-header-title">Live Suggestions</div>
            <div class="results-count">{n} Entit{'y' if n==1 else 'ies'} Matched</div>
        </div>
        """, unsafe_allow_html=True)

        for i, item in enumerate(search_results[:6]):
            poster  = item.get("Poster", "N/A")
            title   = item.get("Title", "Unknown")
            year    = item.get("Year", "")
            imdb_id = item.get("imdbID", "")
            itype   = item.get("Type", "movie").title()
            has_poster = poster and poster != "N/A"

            # Build badge HTML
            badges_html = f"""
            <span class="result-badge badge-type">{itype}</span>
            <span class="result-badge badge-genre">{year}</span>
            """

            # Poster HTML
            if has_poster:
                poster_html = f'<img src="{poster}" alt="{title}" style="width:100%;height:100%;object-fit:cover;filter:grayscale(0.25);"/>'
            else:
                poster_html = '<div class="result-no-poster">🎬</div>'

            st.markdown(f"""
            <div class="result-card" id="card_{imdb_id}">
                <div class="result-poster">
                    {poster_html}
                    <div class="result-poster-fade"></div>
                </div>
                <div class="result-body">
                    <div>
                        <div class="result-title-row">
                            <div class="result-title">{title}</div>
                            {score_ring_html("—", 56)}
                        </div>
                        <div class="result-meta">{year} · {itype}</div>
                        <div class="result-excerpt">
                            Click to start the AI debate — a Critic and an Advocate will dissect this film across four rounds and deliver a calibrated verdict.
                        </div>
                    </div>
                    <div class="result-badges">{badges_html}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Invisible click button overlaid on the card
            if st.button(f"▶ Analyse · {title}", key=f"sel_{imdb_id}_{i}", use_container_width=True):
                st.session_state.selected_imdb_id = imdb_id
                st.session_state.search_results   = []
                st.session_state.cached_movie     = None
                st.session_state.cached_result    = None
                st.session_state.cached_trailer   = None
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
        with st.spinner("Hunting down the trailer…"):
            st.session_state.cached_trailer = fetch_trailer(m["title"], m.get("year", ""))
        raw_reviews = {
            "title":              m["title"],
            "critic_reviews":     m["plot"],
            "audience_reactions": m["actors"],
            "discussion_points":  m["genre"],
        }
        with st.spinner("AI models are entering the debate hall…"):
            st.session_state.cached_result = analyze_movie(raw_reviews)


movie   = st.session_state.cached_movie
result  = st.session_state.cached_result
trailer = st.session_state.cached_trailer


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

    # ── TRAILER ──────────────────────────────────────────────────
    st.markdown("<div class='fancy-divider'></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-heading'>Official Trailer</div>", unsafe_allow_html=True)
    st.markdown("<div class='trailer-badge'>Watch Trailer</div>", unsafe_allow_html=True)

    if trailer:
        st.markdown(
            f"""
            <div class="trailer-wrapper">
                <iframe
                    src="https://www.youtube.com/embed/{trailer}?rel=0&modestbranding=1&color=white"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowfullscreen>
                </iframe>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div class='trailer-no-result'>🎬 &nbsp; Trailer not available for this title</div>",
            unsafe_allow_html=True,
        )

    # ── DEBATE AGENDA ─────────────────────────────────────────────
    st.markdown("<div class='section-heading'>The Debate Agenda</div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class="agenda-strip">
        <div class="agenda-cell">
            <div class="agenda-round">Round 01</div>
            <div class="agenda-num">01</div>
            <div class="agenda-text"><b>Opening Statements</b><br>Initial critical assessment versus a contrarian defence of the film's core premise and intent</div>
        </div>
        <div class="agenda-cell">
            <div class="agenda-round">Round 02</div>
            <div class="agenda-num">02</div>
            <div class="agenda-text"><b>Craft &amp; Vision</b><br>Deep dive into cinematography, direction, character arcs, score, and the film's technical artistry</div>
        </div>
        <div class="agenda-cell">
            <div class="agenda-round">Round 03</div>
            <div class="agenda-num">03</div>
            <div class="agenda-text"><b>Rebuttals</b><br>Pacing critiques, narrative coherence, thematic depth, and competing views on cultural legacy</div>
        </div>
        <div class="agenda-cell">
            <div class="agenda-round">Round 04</div>
            <div class="agenda-num">04</div>
            <div class="agenda-text"><b>Final Synthesis</b><br>Nuanced convergence delivering a calibrated score on a global 10-point cinematic quality scale</div>
        </div>
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

    # ── SCORES ────────────────────────────────────────────────────
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
  <defs>
    <style>
      @keyframes {aname} {{
        from {{ stroke-dasharray: 0 {CIRC}; }}
        to   {{ stroke-dasharray: {filled} {gap}; }}
      }}
    </style>
  </defs>
  <circle cx="18" cy="18" r="15.9155"
    style="fill:none;stroke:{track};stroke-width:3.2;"/>
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

    # ── DEBATE TRANSCRIPT ─────────────────────────────────────────
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

    # ── SCORING BASIS ─────────────────────────────────────────────
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