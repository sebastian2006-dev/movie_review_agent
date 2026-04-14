import json
import re
import streamlit as st
from openai import OpenAI

# ─────────────────────────────────────────────
# MODEL CONFIG  (UPDATED)
# ─────────────────────────────────────────────
MODEL_CRITIC   = "llama-3.3-70b-versatile"
MODEL_ADVOCATE = "mixtral-8x7b-32768"   # ← FIXED MODEL NAME


# ─────────────────────────────────────────────
# GROQ CLIENT
# ─────────────────────────────────────────────
def get_groq_client():
    return OpenAI(
        api_key=st.secrets["GROQ_API_KEY"],
        base_url="https://api.groq.com/openai/v1"
    )


# ─────────────────────────────────────────────
# SAFETY WRAPPER (NEW 🔥)
# Prevents debate from crashing if a model fails
# ─────────────────────────────────────────────
def safe_chat_completion(client, model, **kwargs):
    try:
        return client.chat.completions.create(model=model, **kwargs)
    except Exception as e:
        # fallback to critic model if advocate fails
        if model == MODEL_ADVOCATE:
            return client.chat.completions.create(model=MODEL_CRITIC, **kwargs)
        raise e


# ─────────────────────────────────────────────
# JSON HELPERS
# ─────────────────────────────────────────────
def extract_json(text: str) -> dict:
    """
    Robust JSON extractor that never crashes the app.
    """
    try:
        # Remove markdown fences
        text = re.sub(r"```json|```", "", text)

        # Extract JSON block
        start = text.find("{")
        end = text.rfind("}") + 1
        json_str = text[start:end]

        return json.loads(json_str)

    except Exception as e:
        # Hard fallback so Streamlit never crashes
        return {
            "critic_expert": "Analysis unavailable due to parsing error.",
            "devils_advocate": "Analysis unavailable due to parsing error.",
            "audience_sentiment": "Analysis unavailable due to parsing error.",
            "themes": ["Storytelling", "Characters", "Pacing", "Themes"],
            "final_verdict": {
                "overview": "The AI debate failed to produce structured output.",
                "what_works": ["Concept has potential"],
                "what_fails": ["Model formatting error"],
                "conclusion": "Try running the analysis again.",
                "score": "N/A",
            },
        }


def normalize_schema(data: dict) -> dict:

    def extract_text(section):
        if isinstance(section, dict):
            return section.get("text", "")
        return section or ""

    def ensure_text(text, fallback):
        if not text or len(text.strip()) < 40:
            return fallback
        return text

    data["critic_expert"] = ensure_text(
        extract_text(data.get("critic_expert")),
        "Critic analysis unavailable."
    )
    data["devils_advocate"] = ensure_text(
        extract_text(data.get("devils_advocate")),
        "Devil's Advocate unavailable."
    )
    data["audience_sentiment"] = ensure_text(
        extract_text(data.get("audience_sentiment")),
        "Audience sentiment unavailable."
    )

    if "themes" not in data or not isinstance(data["themes"], list):
        data["themes"] = ["Storytelling", "Characters", "Themes", "Pacing", "Impact"]

    fv = data.get("final_verdict", {})
    data["final_verdict"] = {
        "overview":   fv.get("overview", "Overview unavailable."),
        "what_works": fv.get("what_works", ["Strong premise"]),
        "what_fails": fv.get("what_fails", ["Inconsistent execution"]),
        "conclusion": fv.get("conclusion", "Conclusion unavailable."),
        "score":      fv.get("score", "N/A"),
    }

    if "debate_transcript" not in data:
        data["debate_transcript"] = []

    return data


# ─────────────────────────────────────────────
# DEBATE ENGINE (UPDATED WITH SAFE CALLS)
# ─────────────────────────────────────────────
def run_debate(raw_reviews: dict, client: OpenAI) -> list:

    title  = raw_reviews["title"]
    plot   = raw_reviews["critic_reviews"]
    actors = raw_reviews["audience_reactions"]
    genre  = raw_reviews["discussion_points"]

    movie_ctx = (
        f"MOVIE: {title}\nPLOT: {plot}\nCAST: {actors}\nGENRE: {genre}"
    )

    CRITIC_SYS = """You are a Veteran Film Critic with 30 years experience.
Analyse storytelling craft, direction, pacing, performances and legacy.
Write 3–4 analytical paragraphs."""

    ADVOCATE_SYS = """You are a fearless Devil's Advocate critic.
Attack hype, expose flaws and directly rebut the other critic.
Write 3–4 punchy confrontational paragraphs."""

    history = []

    # Turn 1 — Critic
    t1 = safe_chat_completion(
        client,
        MODEL_CRITIC,
        temperature=0.65,
        max_tokens=600,
        messages=[
            {"role": "system", "content": CRITIC_SYS},
            {"role": "user", "content": f"{movie_ctx}\nOpen the debate."}
        ]
    ).choices[0].message.content.strip()

    history.append({"role": "Veteran Critic", "model": MODEL_CRITIC, "text": t1})

    # Turn 2 — Advocate
    t2 = safe_chat_completion(
        client,
        MODEL_ADVOCATE,
        temperature=0.75,
        max_tokens=600,
        messages=[
            {"role": "system", "content": ADVOCATE_SYS},
            {"role": "user", "content": f"{movie_ctx}\nCritic said:\n{t1}\nChallenge them."}
        ]
    ).choices[0].message.content.strip()

    history.append({"role": "Devil's Advocate", "model": MODEL_ADVOCATE, "text": t2})

    # Turn 3 — Critic rebuttal
    t3 = safe_chat_completion(
        client,
        MODEL_CRITIC,
        temperature=0.65,
        max_tokens=600,
        messages=[
            {"role": "system", "content": CRITIC_SYS},
            {"role": "user", "content": f"{movie_ctx}\nDebate:\n{t1}\n{t2}\nRebut."}
        ]
    ).choices[0].message.content.strip()

    history.append({"role": "Veteran Critic", "model": MODEL_CRITIC, "text": t3})

    # Turn 4 — Advocate closing
    t4 = safe_chat_completion(
        client,
        MODEL_ADVOCATE,
        temperature=0.75,
        max_tokens=600,
        messages=[
            {"role": "system", "content": ADVOCATE_SYS},
            {"role": "user", "content": f"{movie_ctx}\nDebate:\n{t1}\n{t2}\n{t3}\nFinal verdict."}
        ]
    ).choices[0].message.content.strip()

    history.append({"role": "Devil's Advocate", "model": MODEL_ADVOCATE, "text": t4})

    return history


# ─────────────────────────────────────────────
# SYNTHESIS (BUG FIXED HERE 🔥)
# ─────────────────────────────────────────────
def synthesize_debate(raw_reviews, history, client):

    transcript = "\n\n".join(
        f"[{d['role']} — {d['model']}]\n{d['text']}" for d in history
    )

    prompt = f"""Summarise this debate into VALID JSON ONLY.

DEBATE:
{transcript}
"""

    resp = safe_chat_completion(
        client,
        MODEL_CRITIC,
        temperature=0.3,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    ).choices[0].message.content

    return extract_json(resp)


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
def analyze_movie(raw_reviews: dict) -> dict:
    client = get_groq_client()

    debate_history = run_debate(raw_reviews, client)

    # FIXED: JSON repair bug removed
    raw_result = synthesize_debate(raw_reviews, debate_history, client)

    raw_result["debate_transcript"] = debate_history
    return normalize_schema(raw_result)