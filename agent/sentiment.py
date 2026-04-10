import json
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate


def analyze_movie(raw_reviews: dict) -> str:
    """
    Takes movie data + reviews and generates a rich multi-critic panel analysis.
    """

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.9   # higher creativity for richer output
    )

    prompt = ChatPromptTemplate.from_template(f"""
You are simulating a **ROUND-TABLE PANEL of ELITE film critics** analysing the movie or TV show:

TITLE: {raw_reviews['title']}

Your panel includes:
• A veteran Hollywood critic (20+ yrs experience)
• A modern Gen-Z pop-culture critic
• A cynical “Devil’s Advocate” critic
• A passionate audience representative

Your job is to generate a **LONG, RICH, DETAILED cinematic analysis**.

The tone should feel like a magazine feature or YouTube film essay.
Write with personality, depth and storytelling — NOT short summaries.

------------------------------------------------------------

MOVIE DATA:
Plot: {raw_reviews.get("plot")}
IMDB Rating: {raw_reviews.get("rating")}
Genres: {raw_reviews.get("genre")}

User Reviews:
{raw_reviews.get("reviews")}

------------------------------------------------------------

Return the result in THIS FORMAT:

🎬 Veteran Critic (20+ yrs experience)
<3–5 rich paragraphs of deep film analysis>

🔥 Modern Pop-Culture Critic
<modern, energetic perspective>

😈 Devil’s Advocate
<critical / controversial take>

👥 Audience Perspective
<what general viewers feel overall>

🎯 Themes
• list 5–7 deep themes

📝 Detailed Overview
<long cinematic summary>

✅ What Works
✔ point  
✔ point  
✔ point  

❌ What Fails
✖ point  
✖ point  
✖ point  

🎯 Final Verdict
<big closing statement>

⭐ Score: X/10
Be bold and decisive with the score.
""")

    chain = prompt | llm
    response = chain.invoke({})
    return response.content