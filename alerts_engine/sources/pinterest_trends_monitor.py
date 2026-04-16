import os
import requests
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def fetch_pinterest_trends():
    """
    Fetch trending keywords from Pinterest to guide article creation.
    Specifically filtering for food, baking, recipes, sweets.
    """
    token = os.getenv("PINTEREST_ACCESS_TOKEN")
    if not token:
        logger.warning("No PINTEREST_ACCESS_TOKEN found. Cannot fetch Pinterest trends.")
        return []

    headers = {"Authorization": f"Bearer {token}"}
    trending_topics = []
    
    # Filter keywords to ensure they are related to food/sweets/recipes
    food_keywords = ["cake", "cookie", "recipe", "dessert", "sweet", "chocolate", "bake", "pie", "tart", "bread", "pastry", "dinner", "lunch", "breakfast"]

    for trend_type in ["monthly", "growing"]:
        url = f"https://api.pinterest.com/v5/trends/keywords/US/top/{trend_type}"
        params = {
            "interests": "food_and_drinks", # Pinterest category
            "limit": 50
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                for trend in data.get("trends", []):
                    keyword = trend.get("keyword", "").lower()
                    # Apply safety filter to guarantee relevance
                    if any(w in keyword for w in food_keywords):
                        # Format as a topic dict for main.py detection logic
                        topic_data = {
                            "topic": keyword.title(),
                            "matched_keyword": keyword,
                            "type": trend_type,
                            "score": trend.get("pct_growth_yoy", 100),
                            "stories": [{
                                "title": f"Pinterest Trend: {keyword.title()}",
                                "url": f"https://www.pinterest.com/search/pins/?q={keyword}",
                                "published_at": datetime.utcnow().isoformat(),
                                "source": "Pinterest Trends",
                                "story_hash": keyword.replace(" ", "_")
                            }]
                        }
                        trending_topics.append(topic_data)
            else:
                logger.error(f"Pinterest Trends API Error: {response.text}")
        except Exception as e:
            logger.error(f"Failed to fetch Pinterest Trends: {e}")

    # Remove duplicates based on keyword
    unique_topics = []
    seen = set()
    for t in trending_topics:
        if t["matched_keyword"] not in seen:
            seen.add(t["matched_keyword"])
            unique_topics.append(t)
            
    # Sort by score descending to get the absolute top trends
    unique_topics.sort(key=lambda x: x["score"], reverse=True)
    return unique_topics
