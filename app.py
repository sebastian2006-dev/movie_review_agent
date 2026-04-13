import json
import re
import time
import streamlit as st
from openai import OpenAI
from openai import RateLimitError


# ------------------ GROQ CLIENT ------------------

def get_groq_client():
    return OpenAI(
        api_key=st.secrets["GROQ_API_KEY"],
        base_url="https://api.groq.com/openai/v1"
    )


# ------------------ JSON EXTRACTOR ------------------

def extract_json(text: str) -> dict:
    """Extract JSON safely even if model adds junk text."""
    text = re.sub(r"```json|```", "", text)
    start = text.find("{")
    end = text.rfind("}") + 1
    return json.loads(text[start:end])


# ------------------ SCHEMA NORMALIZER ------------------

def normalize_schema(data: dict) -> dict:
    """Guarantees Streamlit ALWAYS gets usable content."""

    def safe_text(value, fallback):
        if not value or len(str(value).strip()) < 50:
            return fallback
        return value

    data["critic_expert"] = safe_text(
        data.get("critic_expert"),
        "Critic analysis failed. Please regenerate."
    )

    data["devils_advocate"] = safe_text(
        data.get("devils_advocate"),
        "Devil's advocate failed. Please regenerate."
    )

    data["audience_sentiment"] = safe_text(
        data.get("audience_sentiment"),
        "Audience sentiment failed. Please regenerate."
    )

    if not isinstance(data.get("themes"), list) or len(data["themes"]) < 3:
        data["themes"] = [
            "Morality", "Identity", "Power", "Consequences", "Human nature"
        ]

    fv = data.get("final_verdict", {})

    data["final_verdict"] = {
        "overview": fv.get("overview", "Overview missing."),
        "what_works": fv.get("what_works", ["Strong premise"]),
        "what_fails": fv.get("what_fails", ["Execution issues"]),
        "conclusion": fv.get("conclusion", "Conclusion missing."),
        "score": fv.get("score", "N/A"),
    }

    return data


# ------------------ RATE LIMIT RETRY WRAPPER ------------------

def groq_chat_with_retry(client, messages, model, retries=3):
    """Retries automatically if rate limited."""
    for attempt in range(retries):
        try:
            return client.chat.completions.create(
                model=model,
                temperature=0.5,
                max_tokens=2200,
                messages=messages
            )
        except RateLimitError:
            if attempt == retries - 1:
                raise
            time.sleep(6)  # cooldown before retry


# ------------------ MAIN ANALYSIS FUNCTION ------------------

def analyze_movie(raw_reviews: dict) -> dict:
    client = get_groq_client()

    # ⭐ NEW SMART PROMPT (fixes always-high ratings problem)
    system_prompt = """
You are a professional film critic round-table.

CRITICAL RULES:
• Be realistic and honest.
• Average movies should score 5–7.
• Only masterpieces get 9–10.
• Bad films can score 3–4.
• Do NOT inflate scores.
• Use the IMDb rating as grounding.
• Be specific and reference plot, actors and genre.

Return ONLY valid JSON.
No markdown.
No extra text.
"""

    user_prompt = f"""
Analyze this movie/series:

TITLE: {raw_reviews['title']}
PLOT: {raw_reviews['critic_reviews']}
ACTORS: {raw_reviews['audience_reactions']}
GENRE: {raw_reviews['discussion_points']}

Return JSON in this exact schema:

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

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    try:
        response = groq_chat_with_retry(
            client,
            messages,
            model="llama-3.3-70b-versatile"
        )

        text = response.choices[0].message.content
        return normalize_schema(extract_json(text))

    except Exception:
        # JSON repair fallback
        repair_prompt = f"Fix this into valid JSON only:\n{text}"

        retry = groq_chat_with_retry(
            client,
            [{"role": "user", "content": repair_prompt}],
            model="llama-3.3-70b-versatile"
        )

        retry_text = retry.choices[0].message.content
        return normalize_schema(extract_json(retry_text))