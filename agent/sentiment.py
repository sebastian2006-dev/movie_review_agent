import json
import re
import streamlit as st
from openai import OpenAI


# ------------------ GROQ CLIENT ------------------

def get_groq_client():
    return OpenAI(
        api_key=st.secrets["GROQ_API_KEY"],
        base_url="https://api.groq.com/openai/v1"
    )


# ------------------ JSON EXTRACTOR ------------------

def extract_json(text: str) -> dict:
    """Robust JSON extractor that survives bad LLM formatting."""
    try:
        # remove ```json ``` wrappers if model adds them
        text = re.sub(r"```json|```", "", text)

        start = text.find("{")
        end = text.rfind("}") + 1
        clean = text[start:end]

        return json.loads(clean)
    except Exception:
        raise ValueError("Model returned invalid JSON")


# ------------------ SCHEMA NORMALIZER ------------------

def normalize_schema(data: dict) -> dict:
    """
    Forces the LLM output to match the schema expected by Streamlit UI.
    Prevents KeyError crashes forever.
    """

    def extract_text(section):
        # Sometimes model returns {text:"...", points:[...]}
        if isinstance(section, dict):
            return section.get("text", "")
        return section or ""

    data["critic_expert"] = extract_text(data.get("critic_expert"))
    data["devils_advocate"] = extract_text(data.get("devils_advocate"))
    data["audience_sentiment"] = extract_text(data.get("audience_sentiment"))

    # Themes safety
    if "themes" not in data or not isinstance(data["themes"], list):
        data["themes"] = []

    # Final verdict safety
    fv = data.get("final_verdict", {})

    data["final_verdict"] = {
        "overview": fv.get("overview", "No overview generated."),
        "what_works": fv.get("what_works", []),
        "what_fails": fv.get("what_fails", []),
        "conclusion": fv.get("conclusion", "No conclusion generated."),
        "score": fv.get("score", "N/A"),
    }

    return data


# ------------------ MAIN ANALYSIS FUNCTION ------------------

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

    # ---------- FIRST TRY ----------
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8
    )

    text = response.choices[0].message.content

    try:
        return normalize_schema(extract_json(text))

    except Exception:
        # ---------- AUTO RETRY IF JSON BREAKS ----------
        retry_prompt = f"""
Your previous response was NOT valid JSON.
Return ONLY valid JSON. No explanation.

{prompt}
"""

        retry = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": retry_prompt}],
            temperature=0.5
        )

        retry_text = retry.choices[0].message.content
        return normalize_schema(extract_json(retry_text))