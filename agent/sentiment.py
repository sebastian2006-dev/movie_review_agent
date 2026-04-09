import json
import os
from dotenv import load_dotenv
from openai import OpenAI
import ollama

load_dotenv()


def get_groq_client():
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables")

    return OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1"
    )


def analyze_movie(raw_reviews: dict) -> dict:

    prompt = f"""
You are a HIGHLY INTELLIGENT panel of film critics analyzing "{raw_reviews['title']}".

You must produce DEEP, INSIGHTFUL, NON-GENERIC analysis.

Adopt 3 DISTINCT personas:

1. 🎬 Veteran Critic (20+ years experience)
   - Analyze storytelling, direction, pacing, character arcs
   - Reference filmmaking quality and narrative depth

2. 😈 Devil's Advocate
   - Actively challenge the hype
   - Point out flaws, overrating, weak writing, pacing issues
   - Be bold, critical, slightly harsh but intelligent

3. 👥 Audience Voice
   - Reflect emotional impact, entertainment value
   - What general viewers love/hate

DATA:
Critic Reviews: {raw_reviews['critic_reviews']}
Audience Reactions: {raw_reviews['audience_reactions']}
Discussion Points: {raw_reviews['discussion_points']}

STRICT RULES:
- NO generic phrases like "great acting" or "good story"
- Be specific and analytical
- Each section must be at least 3-5 sentences
- Devil’s Advocate MUST disagree with something
- Themes must be meaningful (not obvious surface-level)

Return ONLY valid JSON:

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

    # 🔥 Try Groq first
    try:
        client = get_groq_client()

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        text = response.choices[0].message.content

    except Exception as e:
        print("Groq failed, switching to Ollama:", e)

        # 🏠 fallback
        try:
            response = ollama.chat(
                model="llama3",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            text = response["message"]["content"]

        except Exception as e:
            print("Ollama also failed:", e)
            return _error_response(raw_reviews["title"])

    # 🧼 JSON parsing
    try:
        json_start = text.find("{")
        json_end = text.rfind("}") + 1
        clean_json = text[json_start:json_end]

        data = json.loads(clean_json)
        data["title"] = raw_reviews["title"]

        return data

    except Exception as e:
        print("JSON parsing failed:", e)
        print("RAW:", text)
        return _error_response(raw_reviews["title"])


def _error_response(title):
    return {
        "title": title,
        "critic_expert": "Error generating response",
        "devils_advocate": "Error generating response",
        "audience_sentiment": "Error generating response",
        "themes": [],
        "critic_vs_audience": "",
        "final_verdict": {
            "overview": "Error",
            "what_works": [],
            "what_fails": [],
            "conclusion": "Error",
            "score": "N/A"
        }
    }