import json
import ast
from openai import OpenAI
import streamlit as st


def get_groq_client():
    return OpenAI(
        api_key=st.secrets["GROQ_API_KEY"],
        base_url="https://api.groq.com/openai/v1"
    )


# 🔧 Convert weird LLM outputs into strings safely
def repair_to_string(value):
    if isinstance(value, str):
        return value

    if isinstance(value, list):
        return "\n\n".join(str(v) for v in value)

    if isinstance(value, dict):
        return "\n\n".join(str(v) for v in value.values())

    return str(value)


# 🔧 Guarantee schema so Streamlit never crashes
def ensure_schema(data, title):
    return {
        "title": title,
        "critic_expert": repair_to_string(data.get("critic_expert", "No response")),
        "devils_advocate": repair_to_string(data.get("devils_advocate", "No response")),
        "audience_sentiment": repair_to_string(data.get("audience_sentiment", "No response")),
        "themes": data.get("themes", ["Unknown"]),
        "critic_vs_audience": repair_to_string(data.get("critic_vs_audience", "")),
        "final_verdict": {
            "overview": repair_to_string(data.get("final_verdict", {}).get("overview", "")),
            "what_works": data.get("final_verdict", {}).get("what_works", []),
            "what_fails": data.get("final_verdict", {}).get("what_fails", []),
            "conclusion": repair_to_string(data.get("final_verdict", {}).get("conclusion", "")),
            "score": data.get("final_verdict", {}).get("score", "N/A")
        }
    }


def analyze_movie(raw_reviews: dict) -> dict:

    prompt = f"""
You are a panel of expert film critics analyzing "{raw_reviews['title']}".

Return ONLY valid JSON.

Schema:
{{
  "critic_expert": "string",
  "devils_advocate": "string",
  "audience_sentiment": "string",
  "themes": ["", "", "", "", ""],
  "critic_vs_audience": "string",
  "final_verdict": {{
    "overview": "string",
    "what_works": ["", "", ""],
    "what_fails": ["", "", ""],
    "conclusion": "string",
    "score": "X/10"
  }}
}}

DATA:
Critic Reviews: {raw_reviews['critic_reviews']}
Audience Reactions: {raw_reviews['audience_reactions']}
Discussion Points: {raw_reviews['discussion_points']}
"""

    try:
        client = get_groq_client()

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )

        text = response.choices[0].message.content

    except Exception as e:
        st.error(f"Groq Error: {e}")
        return ensure_schema({}, raw_reviews["title"])

    # 🧼 CLEAN MARKDOWN
    text = text.replace("```json", "").replace("```", "").strip()

    # 🧼 EXTRACT JSON
    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        clean_json = text[start:end]
        data = json.loads(clean_json)

    except:
        # 🔥 LAST RESORT AUTO REPAIR
        try:
            data = ast.literal_eval(clean_json)
        except:
            st.error("AI returned invalid JSON — auto fallback used.")
            return ensure_schema({}, raw_reviews["title"])

    return ensure_schema(data, raw_reviews["title"])