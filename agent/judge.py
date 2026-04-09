import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

RUBRIC = """
You are an impartial AI Judge evaluating a movie/show verdict summary.
Score the verdict on each criterion from 1-5:

1. ACCURACY (1-5): Does the verdict reflect what the reviews actually said?
2. BALANCE (1-5): Does it fairly represent both critic and audience perspectives?
3. CLARITY (1-5): Is it clearly written and easy to understand?
4. FAIRNESS (1-5): Does it avoid extreme bias toward either praise or criticism?
5. USEFULNESS (1-5): Would this help someone decide whether to watch the title?

Respond in this exact format:
ACCURACY: <score> — <one sentence reason>
BALANCE: <score> — <one sentence reason>
CLARITY: <score> — <one sentence reason>
FAIRNESS: <score> — <one sentence reason>
USEFULNESS: <score> — <one sentence reason>
TOTAL: <sum>/25
JUDGE_SUMMARY: <2 sentences — overall quality assessment and one improvement suggestion>
"""

def evaluate_verdict(verdict_data: dict) -> dict:
    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt = f"""
{RUBRIC}

TITLE BEING REVIEWED: {verdict_data['title']}

VERDICT TO EVALUATE:
{verdict_data['verdict']}

CONTEXT:
- Critic Sentiment: {verdict_data['critic_sentiment']}
- Audience Sentiment: {verdict_data['audience_sentiment']}
- Key Themes: {verdict_data['themes']}
"""

    response = model.generate_content(prompt)
    judge_text = response.text.strip()

    scores = {}
    for line in judge_text.split("\n"):
        if ":" in line:
            key = line.split(":")[0].strip()
            value = ":".join(line.split(":")[1:]).strip()
            scores[key] = value

    return {
        "judge_output": judge_text,
        "total_score": scores.get("TOTAL", "N/A"),
        "judge_summary": scores.get("JUDGE_SUMMARY", "N/A")
    }