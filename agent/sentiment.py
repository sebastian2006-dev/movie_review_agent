import json
import streamlit as st
from openai import OpenAI


def get_groq_client():
    return OpenAI(
        api_key=st.secrets["GROQ_API_KEY"],
        base_url="https://api.groq.com/openai/v1"
    )


def analyze_movie(raw_reviews: dict) -> dict:

    prompt = f"""
You are a ROUND-TABLE PANEL of elite film critics analysing:

TITLE: {raw_reviews['title']}

You must produce EXTREMELY DETAILED, SPECIFIC and NON-GENERIC analysis.

PERSONAS:

1) 🎬 Veteran Film Critic (technical & cinematic analysis)
   Focus on:
   - storytelling structure
   - directing style
   - pacing & tone
   - character psychology
   - cinematography & writing depth

2) 😈 Devil’s Advocate (contrarian critic)
   - Challenge hype
   - Criticise weak writing, pacing, clichés
   - Point out overrated aspects
   - Must disagree with something strongly

3) 👥 Audience Voice (viewer experience)
   - Emotional impact
   - Entertainment value
   - Binge factor / rewatchability
   - What casual viewers love & hate

DATA:
Plot: {raw_reviews['critic_reviews']}
Actors: {raw_reviews['audience_reactions']}
Genre: {raw_reviews['discussion_points']}

STRICT RULES:
- No generic phrases
- Be analytical and specific
- Each paragraph = 4–6 sentences
- Themes must be deep and meaningful

Return ONLY JSON:

{{
  "critic_expert": "",
  "devils_advocate": "",
  "audience_sentiment": "",
  "themes": ["", "", "", "", ""],
  "critic_vs_audience": "",
  "final_verdict": {{
    "overview": "",
    "what_works": ["", "", ""],
    "what_fails": ["", "", ""],
    "conclusion": "",
    "score": "X/10"
  }}
}}
"""

    client = get_groq_client()

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8
    )

    text = response.choices[0].message.content

    # Extract JSON safely
    json_start = text.find("{")
    json_end = text.rfind("}") + 1
    clean_json = text[json_start:json_end]

    return json.loads(clean_json)