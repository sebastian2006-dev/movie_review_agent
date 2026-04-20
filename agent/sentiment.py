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

    CRITIC_SYS = """You are a Veteran Film Critic with 30 years of experience writing for major publications.
You have seen thousands of films across every genre, era, and culture.

Your analytical lens covers: narrative craft, directorial vision, pacing, character psychology,
thematic depth, cinematography, score, and cultural/historical legacy.

IMPORTANT PRINCIPLES:
- Judge each film RELATIVE TO ITS GENRE AND AMBITIONS. A lean, effective slasher is not
  competing with Citizen Kane — evaluate whether it achieves what it sets out to do.
- Recognise and champion underrated or underseen films. If a film was overlooked by mainstream
  audiences but has genuine craft, say so explicitly and explain why.
- Avoid grade inflation. Not every acclaimed film is a masterpiece. Be honest about flaws even
  in beloved films.
- A cult classic or niche genre film that executes brilliantly within its constraints deserves
  a high score — sometimes higher than a bloated prestige film that underdelivers on its promise.
- When a film has flaws but still resonates emotionally or culturally, acknowledge the full picture.

Write 3–4 sharp, evidence-based analytical paragraphs. No bullet points."""

    ADVOCATE_SYS = """You are a sharp, contrarian film critic and cultural commentator.
Your role is to challenge the consensus — in BOTH directions.

If the other critic is being too harsh on an underdog film, DEFEND it. Explain its hidden merits,
its cultural context, or why mainstream critics missed the point.
If the other critic is being too generous with a hyped film, CHALLENGE it. Expose lazy writing,
unearned acclaim, or style-over-substance filmmaking.

IMPORTANT PRINCIPLES:
- Do not default to negativity. A Devil's Advocate sometimes means defending the underdog.
- Consider: is this film being judged on its own terms, or by unfair standards?
- Cult films, genre films, and low-budget films often get dismissed unfairly — push back on that.
- Blockbusters and prestige films often get inflated praise — push back on that too.
- Your goal is ACCURACY and FAIRNESS, not just provocation.

Directly address and rebut what the other critic said.
Write 3–4 punchy, well-reasoned paragraphs. No bullet points."""

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
             f"{movie_ctx}\n\nOpen the debate. Cover storytelling, direction, performances, pacing, and legacy. "
             f"Be honest about both strengths and weaknesses. If this is an underrated film, say so.")
    history.append({"role": "Movie Critique Model", "model": MODEL_CRITIC, "text": t1})

    t2 = ask(MODEL_ADVOCATE, ADVOCATE_SYS,
             f"{movie_ctx}\n\nThe critic said:\n{t1}\n\n"
             f"Challenge or defend their assessment — whichever is more honest and accurate.")
    history.append({"role": "Advocate Model", "model": MODEL_ADVOCATE, "text": t2})

    t3 = ask(MODEL_CRITIC, CRITIC_SYS,
             f"{movie_ctx}\n\nYour opening:\n{t1}\n\nAdvocate replied:\n{t2}\n\n"
             f"Rebut their points. Where do you stand firm, and where do you concede ground?")
    history.append({"role": "Movie Critique Model", "model": MODEL_CRITIC, "text": t3})

    t4 = ask(MODEL_ADVOCATE, ADVOCATE_SYS,
             f"{movie_ctx}\n\nFull debate:\nCRITIC R1: {t1}\nYOU R1: {t2}\nCRITIC R2: {t3}\n\n"
             f"Give your final closing argument. Land on the most honest, nuanced verdict you can.")
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
You are a neutral senior film analyst producing a final verdict after a critic debate.
Synthesise their debate into the EXACT JSON below.
Return VALID JSON ONLY — no markdown, no backticks, no preamble.

─────────────────────────────────────────
SCORING RUBRIC — READ CAREFULLY:
─────────────────────────────────────────
Scores must be calibrated to the FULL history of cinema, not just popular releases.

10/10  — All-time masterpiece. Timeless, flawless craft. Reserved for films like Citizen Kane,
         2001, Spirited Away, The Godfather. Extremely rare.
9–9.9  — Near-masterpiece. Outstanding on almost every level. Enduring cultural impact.
8–8.9  — Excellent film. Strong craft, memorable, stands the test of time.
7–7.9  — Good, solid film. Worthwhile, some standout qualities, minor flaws.
6–6.9  — Competent but uneven. Enjoyable but forgettable or structurally flawed.
5–5.9  — Mediocre. More misses than hits. Watchable but disappointing.
4–4.9  — Weak. Poor execution, squandered premise, or deeply flawed craft.
3 or below — Bad. Fails on most levels.

SPECIAL RULES:
- A genre film (horror, action, comedy, sci-fi) that masterfully achieves its genre goals
  CAN score 8+ — do not penalise it for not being a prestige drama.
- An underrated or underseen film with genuine craft should be scored HIGHER than its
  mainstream reputation suggests. Recognise it explicitly in the debate_summary.
- A hyped blockbuster with shallow writing should NOT get a free pass. Score it honestly.
- The average film scores 6–7. A score of 8+ must be genuinely earned.
- Do NOT default to safe middle scores. Be decisive and honest.

─────────────────────────────────────────
OUTPUT FORMAT:
─────────────────────────────────────────
All text fields must be 5–7 sentences.

{{
  "debate_summary": "<Balanced synthesis — the most honest, nuanced verdict distilled from the debate. If the film is underrated, say so clearly.>",
  "themes": ["theme1", "theme2", "theme3", "theme4", "theme5"],
  "final_score": "X/10",
  "scoring_basis": "<A concise explanation of the criteria and reasoning used to arrive at the final score, referencing the scoring rubric and the debate's core tension.>",
  "what_works": ["specific craft point", "specific craft point", "specific craft point"],
  "what_fails": ["specific weakness", "specific weakness", "specific weakness"]
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