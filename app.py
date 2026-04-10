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

html, body, [class*="css"] {
    background-color:#0b0f19;
    color:white;
}

/* HERO TITLE */
.title {
    font-size: 60px;
    font-weight: 800;
    text-align:center;
    background: linear-gradient(90deg,#00ffe7,#7a7cff,#ff00c8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* GLASS CARD */
.glass {
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(14px);
    padding: 25px;
    border-radius: 20px;
    border: 1px solid rgba(255,255,255,0.1);
    transition: 0.3s;
}
.glass:hover { transform: translateY(-6px); }

/* PERSONA COLORS */
.critic { border-left: 6px solid gold; }
.devil { border-left: 6px solid #c400ff; }
.audience { border-left: 6px solid #00ffa6; }

/* SCORE PILLS */
.score-pill {
    padding:15px;
    border-radius:50px;
    text-align:center;
    font-size:22px;
    font-weight:700;
    background: linear-gradient(90deg,#00ffe7,#7a7cff);
}

.center { text-align:center; }

</style>
""", unsafe_allow_html=True)

# ---------------- HERO ----------------
st.markdown("<div class='title'>MOVIE INTELLIGENCE TERMINAL</div>", unsafe_allow_html=True)
st.write("")

user_input = st.chat_input("Search movie or TV show...")

# ---------------- MAIN APP ----------------
if user_input:

    movie = fetch_movie_data(user_input)

    if not movie:
        st.error("Movie not found")
        st.stop()

    # ---------- HERO POSTER + INFO ----------
    col1, col2 = st.columns([1,2])

    with col1:
        st.image(movie["poster"], use_column_width=True)

    with col2:
        st.markdown(f"## {movie['title']} ({movie['year']})")
        st.write(f"**Genre:** {movie['genre']}")
        st.write(f"**Runtime:** {movie['runtime']}")
        st.write(f"**Actors:** {movie['actors']}")

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
        st.markdown(f"<div class='score-pill'>IMDb ⭐ {movie['imdb_rating']}</div>", unsafe_allow_html=True)
    with colB:
        st.markdown(f"<div class='score-pill'>AI Score 🎯 {result['final_verdict']['score']}</div>", unsafe_allow_html=True)

    st.write("")
    st.write("")

    # ---------- PERSONA GRID ----------
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("<div class='glass critic'>", unsafe_allow_html=True)
        st.subheader("🎬 Veteran Critic")
        st.write(result["critic_expert"])
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='glass devil'>", unsafe_allow_html=True)
        st.subheader("😈 Devil's Advocate")
        st.write(result["devils_advocate"])
        st.markdown("</div>", unsafe_allow_html=True)

    with col3:
        st.markdown("<div class='glass audience'>", unsafe_allow_html=True)
        st.subheader("👥 Audience Voice")
        st.write(result["audience_sentiment"])
        st.markdown("</div>", unsafe_allow_html=True)

    st.write("")
    st.write("")

    # ---------- THEMES ----------
    st.markdown("## 🎯 Core Themes")
    cols = st.columns(len(result["themes"]))
    for i, t in enumerate(result["themes"]):
        cols[i].markdown(f"<div class='glass center'>{t}</div>", unsafe_allow_html=True)

    # ---------- FINAL VERDICT ----------
    v = result["final_verdict"]

    st.write("")
    st.markdown("## 🧠 Final Verdict")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<div class='glass'>", unsafe_allow_html=True)
        st.subheader("Overview")
        st.write(v["overview"])
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='glass'>", unsafe_allow_html=True)
        st.subheader("Conclusion")
        st.write(v["conclusion"])
        st.markdown("</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<div class='glass'>", unsafe_allow_html=True)
        st.subheader("✅ What Works")
        for w in v["what_works"]:
            st.write("✔", w)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='glass'>", unsafe_allow_html=True)
        st.subheader("❌ What Fails")
        for f in v["what_fails"]:
            st.write("✖", f)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(f"<h1 class='center'>⭐ {v['score']}</h1>", unsafe_allow_html=True)