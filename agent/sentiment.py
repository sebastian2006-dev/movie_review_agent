import json
import re
import streamlit as st
from openai import OpenAI

# ─────────────────────────────────────────────
#  MODEL CONFIG
#  Critic  → llama-3.3-70b-versatile  (analytical, authoritative)
#  Advocate→ gemma2-9b-it              (sharp, contrarian, different arch)
# ─────────────────────────────────────────────
MODEL_CRITIC   = "llama-3.3-70b-versatile"
MODEL_ADVOCATE = "gemma2-9b-it"


# ─────────────────────────────────────────────
#  CLIENT
# ─────────────────────────────────────────────
def get_groq_client():
    return OpenAI(
        api_key=st.secrets["GROQ_API_KEY"],
        base_url="https://api.groq.com/openai/v1"
    )


# ─────────────────────────────────────────────
#  JSON HELPERS
# ─────────────────────────────────────────────
def extract_json(text: str) -> dict:
    try:
        text = re.sub(r"```json|```", "", text)
        start = text.find("{")
        end   = text.rfind("}") + 1
        return json.loads(text[start:end])
    except Exception:
        raise ValueError("Model returned invalid JSON")


def normalize_schema(data: dict) -> dict:
    """Guarantees every key exists and has meaningful content."""

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
        "The Veteran Critic analysis could not be generated. Regenerate to see full breakdown."
    )
    data["devils_advocate"] = ensure_text(
        extract_text(data.get("devils_advocate")),
        "The Devil's Advocate failed to generate a contrarian opinion. Regenerate to see opposing viewpoints."
    )
    data["audience_sentiment"] = ensure_text(
        extract_text(data.get("audience_sentiment")),
        "Audience reactions failed to generate. Regenerate to see viewer emotional impact."
    )

    if "themes" not in data or not isinstance(data["themes"], list) or len(data["themes"]) == 0:
        data["themes"] = ["Morality", "Identity", "Power", "Consequences", "Human nature"]

    fv = data.get("final_verdict", {})
    data["final_verdict"] = {
        "overview":   fv.get("overview",   "Overview not generated."),
        "what_works": fv.get("what_works", ["Strong premise"]),
        "what_fails": fv.get("what_fails", ["Inconsistent output"]),
        "conclusion": fv.get("conclusion", "Conclusion missing."),
        "score":      fv.get("score",      "N/A"),
    }

    # Preserve debate transcript if present
    if "debate_transcript" not in data:
        data["debate_transcript"] = []

    return data


# ─────────────────────────────────────────────
#  DEBATE ENGINE
# ─────────────────────────────────────────────
def run_debate(raw_reviews: dict, client: OpenAI) -> list:
    """
    4-turn debate between two LLMs.
    Returns list of { role, model, text } dicts.
    """

    title  = raw_reviews["title"]
    plot   = raw_reviews["critic_reviews"]
    actors = raw_reviews["audience_reactions"]
    genre  = raw_reviews["discussion_points"]

    movie_ctx = (
        f"MOVIE: {title}\n"
        f"PLOT: {plot}\n"
        f"CAST: {actors}\n"
        f"GENRE: {genre}"
    )

    # ── Persona system prompts ──────────────────
    CRITIC_SYS = """You are a Veteran Film Critic with 30 years of industry experience.
You analyse films through storytelling craft, directorial vision, pacing, 
character psychology, and cultural legacy.
Be precise, evidence-based, and hold films to high standards.
Write 3-4 sharp analytical paragraphs — no bullet points."""

    ADVOCATE_SYS = """You are a sharp, fearless Devil's Advocate film critic.
Your role: challenge mainstream praise, expose over-hyped films, poke at 
weak writing, flat characters, lazy plotting, and unearned acclaim.
You MUST directly address and rebut what the other critic said.
Write 3-4 punchy, confrontational paragraphs — no bullet points."""

    history = []

    # ── Turn 1 — Critic opens ───────────────────
    t1 = client.chat.completions.create(
        model=MODEL_CRITIC,
        temperature=0.65,
        max_tokens=600,
        messages=[
            {"role": "system", "content": CRITIC_SYS},
            {"role": "user",   "content": (
                f"{movie_ctx}\n\n"
                "Open the debate. Cover storytelling, direction, performances, pacing, and the film's legacy."
            )}
        ]
    ).choices[0].message.content.strip()

    history.append({"role": "Veteran Critic", "model": MODEL_CRITIC, "text": t1})

    # ── Turn 2 — Advocate challenges ────────────
    t2 = client.chat.completions.create(
        model=MODEL_ADVOCATE,
        temperature=0.75,
        max_tokens=600,
        messages=[
            {"role": "system", "content": ADVOCATE_SYS},
            {"role": "user",   "content": (
                f"{movie_ctx}\n\n"
                f"The Veteran Critic opened with:\n\n{t1}\n\n"
                "Challenge their points head-on. What are they wrong about? "
                "What flaws and over-praised elements are they glossing over?"
            )}
        ]
    ).choices[0].message.content.strip()

    history.append({"role": "Devil's Advocate", "model": MODEL_ADVOCATE, "text": t2})

    # ── Turn 3 — Critic rebuts ───────────────────
    t3 = client.chat.completions.create(
        model=MODEL_CRITIC,
        temperature=0.65,
        max_tokens=600,
        messages=[
            {"role": "system", "content": CRITIC_SYS},
            {"role": "user",   "content": (
                f"{movie_ctx}\n\n"
                f"Your opening:\n{t1}\n\n"
                f"Devil's Advocate replied:\n{t2}\n\n"
                "Rebut their criticisms. Defend your position or concede the valid points with nuance."
            )}
        ]
    ).choices[0].message.content.strip()

    history.append({"role": "Veteran Critic", "model": MODEL_CRITIC, "text": t3})

    # ── Turn 4 — Advocate closes ─────────────────
    t4 = client.chat.completions.create(
        model=MODEL_ADVOCATE,
        temperature=0.75,
        max_tokens=600,
        messages=[
            {"role": "system", "content": ADVOCATE_SYS},
            {"role": "user",   "content": (
                f"{movie_ctx}\n\n"
                f"Full debate so far:\n"
                f"CRITIC (Round 1): {t1}\n\n"
                f"YOU (Round 1): {t2}\n\n"
                f"CRITIC (Round 2): {t3}\n\n"
                "Give your final closing argument. What is your ultimate verdict on this film?"
            )}
        ]
    ).choices[0].message.content.strip()

    history.append({"role": "Devil's Advocate", "model": MODEL_ADVOCATE, "text": t4})

    return history


# ─────────────────────────────────────────────
#  SYNTHESIS
# ─────────────────────────────────────────────
def synthesize_debate(raw_reviews: dict, history: list, client: OpenAI) -> dict:
    """Neutral synthesis of the full debate → structured JSON."""

    transcript = "\n\n".join(
        f"[{d['role']} — {d['model']}]\n{d['text']}"
        for d in history
    )

    prompt = f"""
You are a neutral senior film analyst. Two AI critics just debated "{raw_reviews['title']}".

FULL DEBATE TRANSCRIPT:
{transcript}

Synthesise the debate into this EXACT JSON schema.
Return VALID JSON ONLY — no markdown, no backticks, no preamble.

SCORING CALIBRATION (use this strictly):
9-10 → Masterpiece / genre-defining
8-8.9 → Excellent but flawed
7-7.9 → Good but inconsistent
6-6.9 → Average / watchable
5-5.9 → Weak / forgettable
4 or below → Bad

Every text field must be 5-7 sentences.

{{
  "critic_expert": "<Veteran Critic's combined view drawn from both their debate rounds>",
  "devils_advocate": "<Devil's Advocate's combined challenges drawn from both their debate rounds>",
  "audience_sentiment": "<How general audiences would likely feel — inferred from both perspectives>",
  "themes": ["theme1", "theme2", "theme3", "theme4", "theme5"],
  "critic_vs_audience": "<1-2 sentences on the critic vs audience divide>",
  "final_verdict": {{
    "overview": "<Balanced synthesis of both sides — 4-5 sentences>",
    "what_works": ["specific point", "specific point", "specific point"],
    "what_fails": ["specific point", "specific point", "specific point"],
    "conclusion": "<One definitive sentence>",
    "score": "X/10"
  }}
}}
"""

    resp = client.chat.completions.create(
        model=MODEL_CRITIC,
        temperature=0.35,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    ).choices[0].message.content

    return extract_json(resp)


# ─────────────────────────────────────────────
#  PUBLIC ENTRY POINT  (called from app.py)
# ─────────────────────────────────────────────
def analyze_movie(raw_reviews: dict) -> dict:
    client = get_groq_client()

    # Step 1 — Run the debate
    debate_history = run_debate(raw_reviews, client)

    # Step 2 — Synthesise
    raw_result = None
    try:
        raw_result = synthesize_debate(raw_reviews, debate_history, client)
    except ValueError:
        # JSON repair fallback
        repair_prompt = (
            "The following text should be valid JSON but is malformed. "
            "Fix it and return ONLY valid JSON, nothing else:\n\n"
            + str(raw_result)
        )
        retry_text = client.chat.completions.create(
            model=MODEL_CRITIC,
            temperature=0.2,
            max_tokens=2000,
            messages=[{"role": "user", "content": repair_prompt}]
        ).choices[0].message.content
        raw_result = extract_json(retry_text)

    # Step 3 — Attach transcript + normalise
    raw_result["debate_transcript"] = debate_history
    return normalize_schema(raw_result)