import json
import re
import streamlit as st
from openai import OpenAI

MODEL_CRITIC   = "llama-3.3-70b-versatile"
MODEL_ADVOCATE = "mixtral-8x7b-32768"


def get_groq_client():
    return OpenAI(
        api_key=st.secrets["GROQ_API_KEY"],
        base_url="https://api.groq.com/openai/v1"
    )


def safe_chat_completion(client, model, **kwargs):
    try:
        return client.chat.completions.create(model=model, **kwargs)
    except Exception:
        if model == MODEL_ADVOCATE:
            return client.chat.completions.create(model=MODEL_CRITIC, **kwargs)
        raise


def extract_json(text: str) -> dict:
    try:
        text = re.sub(r"```json|```", "", text)
        start = text.find("{")
        end   = text.rfind("}") + 1
        return json.loads(text[start:end])
    except Exception:
        return {
            "debate_summary": "Summary unavailable.",
            "themes":         ["Storytelling", "Characters", "Direction", "Pacing", "Legacy"],
            "final_score":    "N/A",
            "what_works":     ["Analysis unavailable — please try again."],
            "what_fails":     ["Analysis unavailable — please try again."],
        }


# ─────────────────────────────────────────────
#  DEBATE ENGINE
# ─────────────────────────────────────────────
def run_debate(raw_reviews: dict, client: OpenAI) -> list:
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

    CRITIC_SYS = """You are a Veteran Film Critic with 30 years of experience.
Analyse films through storytelling craft, directorial vision, pacing,
character psychology, and cultural legacy.
Be precise, evidence-based, and hold films to high standards.
Write 3-4 sharp analytical paragraphs — no bullet points."""

    ADVOCATE_SYS = """You are a sharp, fearless Devil's Advocate film critic.
Your role: challenge mainstream praise, expose over-hyped films, poke at
weak writing, flat characters, lazy plotting, and unearned acclaim.
Directly address and rebut what the other critic said.
Write 3-4 punchy, confrontational paragraphs — no bullet points."""

    def ask(model, system, user_msg):
        return safe_chat_completion(
            client, model,
            temperature=0.7,
            max_tokens=600,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user_msg},
            ]
        ).choices[0].message.content.strip()

    history = []

    t1 = ask(MODEL_CRITIC, CRITIC_SYS,
             f"{movie_ctx}\n\nOpen the debate. Cover storytelling, direction, performances, pacing, and legacy.")
    history.append({"role": "Movie Critique Model", "model": MODEL_CRITIC, "text": t1})

    t2 = ask(MODEL_ADVOCATE, ADVOCATE_SYS,
             f"{movie_ctx}\n\nThe critic said:\n{t1}\n\nChallenge their points head-on.")
    history.append({"role": "Advocate Model", "model": MODEL_ADVOCATE, "text": t2})

    t3 = ask(MODEL_CRITIC, CRITIC_SYS,
             f"{movie_ctx}\n\nYour opening:\n{t1}\n\nAdvocate replied:\n{t2}\n\nRebut their criticisms.")
    history.append({"role": "Movie Critique Model", "model": MODEL_CRITIC, "text": t3})

    t4 = ask(MODEL_ADVOCATE, ADVOCATE_SYS,
             f"{movie_ctx}\n\nFull debate:\nCRITIC R1: {t1}\nYOU R1: {t2}\nCRITIC R2: {t3}\n\nFinal closing argument.")
    history.append({"role": "Advocate Model", "model": MODEL_ADVOCATE, "text": t4})

    return history


# ─────────────────────────────────────────────
#  SYNTHESIS
# ─────────────────────────────────────────────
def synthesize_debate(history: list, client: OpenAI) -> dict:
    transcript = "\n\n".join(
        f"[{d['role']} — {d['model']}]\n{d['text']}"
        for d in history
    )

    prompt = f"""
You are a neutral senior film analyst. Two AI critics just debated a film.
Synthesise their debate into the EXACT JSON below.
Return VALID JSON ONLY — no markdown, no backticks, no preamble.

SCORING:
9-10 = Masterpiece, 8-8.9 = Excellent, 7-7.9 = Good,
6-6.9 = Average, 5-5.9 = Weak, 4 or below = Bad

All text fields must be 5-7 sentences.

{{
  "debate_summary": "<Balanced synthesis of both sides — the best possible answer distilled from the full debate>",
  "themes": ["theme1", "theme2", "theme3", "theme4", "theme5"],
  "final_score": "X/10",
  "what_works": ["specific point", "specific point", "specific point"],
  "what_fails": ["specific point", "specific point", "specific point"]
}}

DEBATE TRANSCRIPT:
{transcript}
"""

    resp = safe_chat_completion(
        client, MODEL_CRITIC,
        temperature=0.3,
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    ).choices[0].message.content

    return extract_json(resp)


# ─────────────────────────────────────────────
#  PUBLIC ENTRY POINT
# ─────────────────────────────────────────────
def analyze_movie(raw_reviews: dict) -> dict:
    client  = get_groq_client()
    history = run_debate(raw_reviews, client)
    result  = synthesize_debate(history, client)
    result["debate_transcript"] = history
    return result