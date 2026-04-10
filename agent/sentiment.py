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

    # ---------- SYSTEM PROMPT (very important) ----------
    system_prompt = """
You are an elite Hollywood critic round-table.

CRITICAL RULES:

• You NEVER give safe or generic reviews.
• You NEVER give similar ratings to every film.
• You MUST calibrate scores realistically like IMDb/RottenTomatoes critics.
• Scores must vary strongly between average, good, and masterpiece.

SCORING CALIBRATION:

9–10  → Masterpiece / genre-defining / cultural impact
8–8.9 → Excellent but flawed
7–7.9 → Good but inconsistent
6–6.9 → Average / watchable
5–5.9 → Weak / forgettable
4 or below → Bad

You must justify the score using:
- storytelling quality
- originality
- character depth
- direction & pacing
- cultural impact / legacy
- comparison to top films in the genre

Every text field must contain 5–7 sentences minimum.
Return PERFECT VALID JSON ONLY.
No markdown. No backticks.
"""

    # ---------- USER PROMPT ----------
    user_prompt = f"""
You are a ROUND-TABLE PANEL of elite film critics analysing:

TITLE: {raw_reviews['title']}

PERSONAS:

1) Veteran Film Critic
   - storytelling structure
   - directing style
   - pacing & tone
   - character psychology
   - cinematography & writing depth

2) Devil’s Advocate
   - Challenge hype
   - Criticise weak writing, pacing, clichés
   - Strong disagreement required

3) Audience Voice
   - Emotional impact
   - Entertainment value
   - Binge factor / rewatchability

DATA:
Plot: {raw_reviews['critic_reviews']}
Actors: {raw_reviews['audience_reactions']}
Genre: {raw_reviews['discussion_points']}

Return ONLY JSON in this schema:

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

    # ⭐⭐⭐ FIRST GENERATION — HIGH QUALITY MODEL ⭐⭐⭐
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",   # 🔥 UPGRADED MODEL
        temperature=0.5,                   # more reliable
        max_tokens=2500,                   # allows long analysis
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )

    text = response.choices[0].message.content

    try:
        return normalize_schema(extract_json(text))

    except Exception:
        # ---------- AUTO JSON REPAIR RETRY ----------
        repair_prompt = f"""
Fix this JSON. Return ONLY valid JSON.

{text}
"""

        retry = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            temperature=0.2,
            max_tokens=2500,
            messages=[{"role": "user", "content": repair_prompt}]
        )

        retry_text = retry.choices[0].message.content
        return normalize_schema(extract_json(retry_text))