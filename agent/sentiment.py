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
    Guarantees Streamlit ALWAYS receives valid + non-empty content.
    Fixes:
    - Missing keys
    - Dict vs string drift
    - Empty LLM sections
    - Missing arrays
    """

    def extract_text(section):
        if isinstance(section, dict):
            return section.get("text", "")
        return section or ""

    critic = extract_text(data.get("critic_expert"))
    devil = extract_text(data.get("devils_advocate"))
    audience = extract_text(data.get("audience_sentiment"))

    # 🔥 EMPTY TEXT AUTO-RECOVERY
    def ensure_text(text, fallback):
        if not text or len(text.strip()) < 40:
            return fallback
        return text

    data["critic_expert"] = ensure_text(
        critic,
        "The critic panel could not generate a full technical breakdown. "
        "Regenerate to receive detailed analysis of storytelling, direction, and character psychology."
    )

    data["devils_advocate"] = ensure_text(
        devil,
        "The Devil’s Advocate failed to generate a contrarian opinion. "
        "Regenerate to see strong criticism and opposing viewpoints."
    )

    data["audience_sentiment"] = ensure_text(
        audience,
        "Audience reactions failed to generate. Regenerate to see viewer emotional impact and binge value."
    )

    # THEMES SAFETY
    if "themes" not in data or not isinstance(data["themes"], list) or len(data["themes"]) == 0:
        data["themes"] = [
            "Morality",
            "Identity",
            "Power",
            "Consequences",
            "Human nature"
        ]

    # FINAL VERDICT SAFETY
    fv = data.get("final_verdict", {})

    data["final_verdict"] = {
        "overview": fv.get("overview", "Overview not generated."),
        "what_works": fv.get("what_works", ["Strong premise"]),
        "what_fails": fv.get("what_fails", ["Inconsistent AI output"]),
        "conclusion": fv.get("conclusion", "Final conclusion missing."),
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

    # FIRST TRY
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8
    )

    text = response.choices[0].message.content

    try:
        return normalize_schema(extract_json(text))

    except Exception:
        # RETRY IF JSON BREAKS
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