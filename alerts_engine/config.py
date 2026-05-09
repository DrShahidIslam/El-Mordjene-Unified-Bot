"""
Central configuration for the El-Mordjene News Agent.
All settings, keywords, RSS feeds, and thresholds are defined here.
"""
import os
import logging
from dotenv import load_dotenv

# Force load .env
load_dotenv(override=True)

def get_env_manual(key, default=""):
    """Manually parse .env file to bypass system environment locks."""
    try:
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                for line in f:
                    clean_line = line.strip()
                    if clean_line.startswith(f"{key}="):
                        return clean_line.split("=", 1)[1].strip().strip("'").strip('"')
    except Exception:
        pass
    return os.getenv(key, default)

# API Keys (Forced from .env)
NEWS_API_KEY = get_env_manual("NEWS_API_KEY")

_gemini_keys_env = get_env_manual("GEMINI_API_KEYS")
GEMINI_API_KEYS = [k.strip() for k in _gemini_keys_env.split(",") if k.strip()]
GEMINI_API_KEY = GEMINI_API_KEYS[0] if GEMINI_API_KEYS else None

WP_URL = get_env_manual("WP_BASE_URL", "https://el-mordjene.info").rstrip("/")
WP_USERNAME = get_env_manual("WP_USERNAME")
WP_APP_PASSWORD = get_env_manual("WP_APP_PASSWORD")
WP_PUBLISH_WEBHOOK_URL = get_env_manual("WP_PUBLISH_WEBHOOK_URL", "").strip()
WP_PUBLISH_SECRET = get_env_manual("WP_PUBLISH_SECRET", "").strip()
WP_RECIPE_CATEGORY_EN = get_env_manual("WP_RECIPE_CATEGORY_EN", "Recipes").strip() or "Recipes"
WP_RECIPE_CATEGORY_FR = get_env_manual("WP_RECIPE_CATEGORY_FR", "Recettes").strip() or "Recettes"
WP_RECIPE_CATEGORY_SLUG_EN = get_env_manual("WP_RECIPE_CATEGORY_SLUG_EN", "recipes-recettes").strip()
WP_RECIPE_CATEGORY_SLUG_FR = get_env_manual("WP_RECIPE_CATEGORY_SLUG_FR", "recipes-recettes-fr").strip()
ACF_RECIPE_SCHEMA_FIELDS = [s.strip() for s in get_env_manual("ACF_RECIPE_SCHEMA_FIELDS", "recipe_schema_json").split(",") if s.strip()]

# Premium APIs
SILICONFLOW_API_KEY = get_env_manual("SILICONFLOW_API_KEY")
SILICONFLOW_MODEL = get_env_manual("SILICONFLOW_MODEL", "Kwai-Kolors/Kolors")

_hf_keys_env = get_env_manual("HUGGINGFACE_API_KEY")
HUGGINGFACE_API_KEYS = [k.strip() for k in _hf_keys_env.split(",") if k.strip()]

# Pinterest (PRODUCTION)
PINTEREST_ACCESS_TOKEN = get_env_manual("PINTEREST_ACCESS_TOKEN")
PINTEREST_REFRESH_TOKEN = get_env_manual("PINTEREST_REFRESH_TOKEN")
PINTEREST_APP_ID = get_env_manual("PINTEREST_APP_ID")
PINTEREST_APP_SECRET = get_env_manual("PINTEREST_APP_SECRET")
PINTEREST_BOARD_ID = get_env_manual("PINTEREST_BOARD_ID")
BRIDGE_PAGE_URL = get_env_manual("BRIDGE_PAGE_URL")

YOUTUBE_API_KEY = get_env_manual("YOUTUBE_API_KEY", "").strip()

# RSS Feeds
RSS_FEEDS = {
    "Google News El Mordjene": "https://news.google.com/rss/search?q=el+mordjene+OR+mordjane+OR+cebon+spread&hl=en-US&gl=US&ceid=US:en",
    "Google News Chocolate Trends": "https://news.google.com/rss/search?q=chocolate+trend+OR+filled+chocolate+bar+OR+pistachio+cream&hl=en-US&gl=US&ceid=US:en",
    "Google News Viral Desserts": "https://news.google.com/rss/search?q=viral+dessert+OR+viral+sweet+OR+tiktok+dessert&hl=en-US&gl=US&ceid=US:en",
    "Google News Confectionery": "https://news.google.com/rss/search?q=confectionery+news+OR+candy+industry+OR+chocolate+launch&hl=en-US&gl=US&ceid=US:en",
}

BRAND_KEYWORDS = ["el mordjene", "cebon"]
CHOCOLATE_PRODUCT_KEYWORDS = ["chocolate spread", "hazelnut spread", "pistachio cream"]
SWEETS_TREND_KEYWORDS = ["viral dessert", "viral sweet", "tiktok dessert"]
FRENCH_CULINARY_KEYWORDS = ["french pastry", "viennoiserie"]
NORTH_AFRICAN_KEYWORDS = ["algerian dessert", "maghreb cuisine"]
FOOD_NEWS_KEYWORDS = ["food recall", "product launch"]

ALL_KEYWORDS = BRAND_KEYWORDS + CHOCOLATE_PRODUCT_KEYWORDS + SWEETS_TREND_KEYWORDS + FRENCH_CULINARY_KEYWORDS + NORTH_AFRICAN_KEYWORDS + FOOD_NEWS_KEYWORDS

SPIKE_THRESHOLD = 1.8
SCAN_INTERVAL_MINUTES = 60
AUTO_PUBLISH = True
MAX_AUTO_ARTICLES_PER_SCAN = 2
ARTICLE_MIN_WORDS = 800
GEMINI_MODEL = "gemini-3.1-flash-lite-preview"
WP_DEFAULT_STATUS = "publish"
WP_DEFAULT_CATEGORY = "Blog"
SKIP_AI_IMAGE = False
USE_GEMINI_IMAGEN = False
DUPLICATE_SIMILARITY_THRESHOLD = 0.4

# Operational Settings
POSTS_PER_RUN = int(get_env_manual("POSTS_PER_RUN", 2))
MAX_PINS_PER_RUN = int(get_env_manual("MAX_PINS_PER_RUN", 8))
LOOKBACK_HOURS = int(get_env_manual("LOOKBACK_HOURS", 96))

LOG_FILE = "agent.log"
LOG_LEVEL = "INFO"
