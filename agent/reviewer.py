from agent.tools import search_reviews

def collect_reviews(title: str) -> dict:
    """
    Runs three targeted Tavily searches and returns raw review data.
    """
    print(f"[Review Collector] Searching for: {title}")

    critic_data     = search_reviews(title, "critic")
    audience_data   = search_reviews(title, "audience")
    discussion_data = search_reviews(title, "discussion")

    return {
        "title": title,
        "critic_reviews": critic_data,
        "audience_reactions": audience_data,
        "discussion_points": discussion_data
    }