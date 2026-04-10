import requests
import streamlit as st

TAVILY_API_KEY = st.secrets.get("TAVILY_API_KEY", "")

def search_reviews(title: str, category: str) -> str:
    """Search Tavily for movie discussion."""

    if not TAVILY_API_KEY:
        return "No external reviews available."

    query_map = {
        "critic": f"{title} movie critic reviews analysis",
        "audience": f"{title} audience reactions opinions",
        "discussion": f"{title} movie themes discussion analysis"
    }

    try:
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": TAVILY_API_KEY,
            "query": query_map.get(category, title),
            "search_depth": "basic",
            "max_results": 3
        }

        res = requests.post(url, json=payload, timeout=15)
        data = res.json()

        results = [r["content"] for r in data.get("results", [])]
        return "\n".join(results) if results else "No results."

    except Exception as e:
        print("Tavily error:", e)
        return "Search failed."