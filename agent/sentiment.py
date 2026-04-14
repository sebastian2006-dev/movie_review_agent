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
    except:
        if model == MODEL_ADVOCATE:
            return client.chat.completions.create(model=MODEL_CRITIC, **kwargs)
        raise

def extract_json(text: str) -> dict:
    try:
        text = re.sub(r"```json|```", "", text)
        start = text.find("{")
        end = text.rfind("}") + 1
        return json.loads(text[start:end])
    except:
        return {
            "debate_summary": "Summary unavailable.",
            "themes": ["Storytelling","Characters","Themes"],
            "final_score": "N/A",
            "what_works": ["Analysis unavailable"],
            "what_fails": ["Analysis unavailable"]
        }

# ---------- DEBATE ----------
def run_debate(raw_reviews: dict, client: OpenAI) -> list:
    title  = raw_reviews["title"]
    plot   = raw_reviews["critic_reviews"]
    actors = raw_reviews["audience_reactions"]
    genre  = raw_reviews["discussion_points"]

    movie_ctx = f"MOVIE: {title}\nPLOT: {plot}\nCAST: {actors}\nGENRE: {genre}"

    CRITIC_SYS = "You are a Veteran Film Critic."
    ADVOCATE_SYS = "You are a harsh Devil's Advocate critic."

    history = []

    def ask(model, system, user):
        return safe_chat_completion(
            client, model,
            temperature=0.7, max_tokens=600,
            messages=[{"role":"system","content":system},{"role":"user","content":user}]
        ).choices[0].message.content.strip()

    t1 = ask(MODEL_CRITIC, CRITIC_SYS, f"{movie_ctx}\nOpen debate.")
    history.append({"role":"Veteran Critic","model":MODEL_CRITIC,"text":t1})

    t2 = ask(MODEL_ADVOCATE, ADVOCATE_SYS, f"{movie_ctx}\nCritic:\n{t1}\nChallenge.")
    history.append({"role":"Devil's Advocate","model":MODEL_ADVOCATE,"text":t2})

    t3 = ask(MODEL_CRITIC, CRITIC_SYS, f"{movie_ctx}\nDebate:\n{t1}\n{t2}\nRebut.")
    history.append({"role":"Veteran Critic","model":MODEL_CRITIC,"text":t3})

    t4 = ask(MODEL_ADVOCATE, ADVOCATE_SYS, f"{movie_ctx}\nDebate:\n{t1}\n{t2}\n{t3}\nFinal argument.")
    history.append({"role":"Devil's Advocate","model":MODEL_ADVOCATE,"text":t4})

    return history

# ---------- SYNTHESIS ----------
def synthesize_debate(history, client):

    transcript = "\n\n".join(f"[{d['role']}]\n{d['text']}" for d in history)

    prompt = f"""
Summarize this movie debate and output STRICT JSON:

{{
"debate_summary": "...",
"themes": ["..."],
"final_score": "8.5/10",
"what_works": ["..."],
"what_fails": ["..."]
}}

DEBATE:
{transcript}
"""

    resp = safe_chat_completion(
        client, MODEL_CRITIC,
        temperature=0.3, max_tokens=1500,
        messages=[{"role":"user","content":prompt}]
    ).choices[0].message.content

    return extract_json(resp)

# ---------- ENTRY ----------
def analyze_movie(raw_reviews: dict) -> dict:
    client = get_groq_client()
    history = run_debate(raw_reviews, client)
    result = synthesize_debate(history, client)
    result["debate_transcript"] = history
    return result