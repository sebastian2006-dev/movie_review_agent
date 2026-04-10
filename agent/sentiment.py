import json
import re
import streamlit as st
from openai import OpenAI


def get_groq_client():
    return OpenAI(
        api_key=st.secrets["GROQ_API_KEY"],
        base_url="https://api.groq.com/openai/v1"
    )


# 🔥 Robust JSON extractor (production safe)
def extract_json(text: str) -> dict:
    # remove markdown code blocks
    text = re.sub(r"```json|```", "", text)

    # grab first JSON object
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON found in model response")

    json_str = match.group(0)

    # remove trailing commas (very common LLM mistake)
    json_str = re.sub(r",\s*}", "}", json_str)
    json_str = re.sub(r",\s*]", "]", json_str)

    return json.loads(json_str)


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

    # 🧠 Try parsing safely
    try:
        return extract_json(text)

    except Exception:
        # 🔁 automatic retry forcing strict JSON
        retry_prompt = "Return ONLY valid JSON. Fix this:\n" + text

        retry = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": retry_prompt}],
            temperature=0
        )

        retry_text = retry.choices[0].message.content
        return extract_json(retry_text)