import streamlit as st
from agent.sentiment import analyze_movie
from agent.tools import fetch_movie_data

# 🔥 Page config
st.set_page_config(page_title="Movie & Show Review Aggregator AI Agent", layout="wide")

# 🎨 Styling (AI + Netflix vibe)
st.markdown("""
<style>
body {
    background-color: #0f0f0f;
    color: white;
}
.stChatInputContainer {
    background-color: #1c1c1c !important;
    border-radius: 20px !important;
    padding: 10px !important;
}
.stChatMessage {
    background-color: #1a1a1a !important;
    border-radius: 15px !important;
    padding: 15px !important;
}
.rating-box {
    background-color: #e50914;
    padding: 10px;
    border-radius: 8px;
    text-align: center;
    font-weight: bold;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# 🤖 Title
st.title("🤖 AI Agent for Movie & Show Reviews")

# 💬 Chat Input
user_input = st.chat_input("Ask about a movie or show...")

if user_input:

    # 👤 User message
    st.chat_message("user").write(user_input)

    # 🤖 Assistant response
    with st.chat_message("assistant"):

        movie = fetch_movie_data(user_input)

        if not movie:
            st.error("Movie not found")
        else:

            # 🎥 HERO POSTER (FIXED NO CROP)
            st.markdown(f"""
            <div style="position: relative; border-radius: 15px; overflow: hidden;">
                <img src="{movie['poster']}" style="
                    width: 100%;
                    height: 500px;
                    object-fit: contain;
                    background-color: #000;
                ">
                <div style="
                    position: absolute;
                    bottom: 0;
                    width: 100%;
                    padding: 20px;
                    background: linear-gradient(to top, rgba(0,0,0,0.9), transparent);
                    color: white;
                ">
                    <h1>{movie['title']}</h1>
                    <p>{movie['year']} • {movie['genre']}</p>
                    <p>{movie['actors']}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # 🧠 Prepare AI input
            raw_reviews = {
                "title": movie["title"],
                "critic_reviews": movie["plot"],
                "audience_reactions": f"Actors: {movie['actors']}",
                "discussion_points": movie["genre"]
            }

            with st.spinner("🧠 AI critics are debating..."):
                result = analyze_movie(raw_reviews)

            # ⭐ RATINGS
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(
                    f"<div class='rating-box'>IMDb ⭐ {movie['imdb_rating']}</div>",
                    unsafe_allow_html=True
                )

            with col2:
                st.markdown(
                    f"<div class='rating-box'>AI 🎯 {result['final_verdict']['score']}</div>",
                    unsafe_allow_html=True
                )

            # 🎭 MULTI-PERSONALITY OUTPUT

            st.subheader("🎬 Veteran Critic (20+ yrs experience)")
            st.write(result["critic_expert"])

            st.subheader("😈 Devil’s Advocate")
            st.write(result["devils_advocate"])

            st.subheader("👥 Audience Perspective")
            st.write(result["audience_sentiment"])

            # 🎯 THEMES
            st.subheader("🎯 Themes")
            for t in result["themes"]:
                st.write(f"• {t}")

            # 📝 FINAL VERDICT
            v = result["final_verdict"]

            st.subheader("📝 Overview")
            st.write(v["overview"])

            st.subheader("✅ What Works")
            for w in v["what_works"]:
                st.write(f"✔ {w}")

            st.subheader("❌ What Fails")
            for f in v["what_fails"]:
                st.write(f"✖ {f}")

            st.subheader("🎯 Final Conclusion")
            st.write(v["conclusion"])

            st.subheader(f"⭐ Score: {v['score']}")