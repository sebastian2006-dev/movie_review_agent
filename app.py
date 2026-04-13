import os
import requests
import streamlit as st
from groq import Groq

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="🎬 Movie Review AI", layout="wide")

# ---------------- THEME STATE ----------------
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

is_dark = st.session_state.dark_mode

# ---------------- TOP RIGHT TOGGLE (REAL SWITCH) ----------------
_, tog_col = st.columns([8, 1])
with tog_col:
    st.session_state.dark_mode = st.toggle(
        "🌙 Dark" if is_dark else "☀️ Light",
        value=is_dark,
        key="dark_mode",
    )

# ---------------- API KEYS SAFE LOADING ----------------
# Groq key (required)
GROQ_API_KEY = (
    st.secrets.get("GROQ_API_KEY", None)
    if hasattr(st, "secrets")
    else None
)
if not GROQ_API_KEY:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# OMDB key (optional now — app will still run without it)
OMDB_API_KEY = None
try:
    OMDB_API_KEY = st.secrets.get("OMDB_API_KEY", None)
except:
    pass

if not OMDB_API_KEY:
    OMDB_API_KEY = os.getenv("OMDB_API_KEY")

# ---------------- GROQ CLIENT ----------------
client = None
if GROQ_API_KEY:
    client = Groq(api_key=GROQ_API_KEY)

# ---------------- FUNCTIONS ----------------
def analyze_movie(movie_name: str):
    if not client:
        return "⚠️ Groq API key missing. Add GROQ_API_KEY to secrets."

    prompt = f"""
You are a professional movie critic.

Give a detailed review of the movie: {movie_name}

Include:
• Story summary  
• Acting  
• Direction  
• Overall verdict  
• Final rating out of 10
"""

    completion = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )

    return completion.choices[0].message.content


def fetch_movie_poster(movie_name):
    if not OMDB_API_KEY:
        return None

    url = f"http://www.omdbapi.com/?t={movie_name}&apikey={OMDB_API_KEY}"
    res = requests.get(url).json()
    return res.get("Poster")


# ---------------- UI ----------------
st.title("🎬 Movie Review AI")

movie = st.text_input("Enter a movie name")

if st.button("Generate Review"):
    if movie:
        with st.spinner("Analyzing movie..."):
            review = analyze_movie(movie)
            poster = fetch_movie_poster(movie)

        col1, col2 = st.columns([1, 2])

        with col1:
            if poster and poster != "N/A":
                st.image(poster)

        with col2:
            st.write(review)
    else:
        st.warning("Please enter a movie name.")