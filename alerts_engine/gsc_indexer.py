import os
import json
import requests
import base64
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("gsc_indexer")

# Configuration
LOCAL_KEY_PATH = Path(__file__).parent / "food-trends-blog-e2b06405bfe0.json"
INDEXING_API_ENDPOINT = "https://indexing.googleapis.com/v3/urlNotifications:publish"
SCOPES = ["https://www.googleapis.com/auth/indexing"]

def get_service_account_credentials():
    """Retrieve service account credentials from env variable or local JSON file."""
    env_key = os.getenv("GSC_SERVICE_ACCOUNT_KEY")
    if env_key:
        try:
            # Try raw JSON
            if env_key.strip().startswith("{"):
                info = json.loads(env_key)
            else:
                # Try base64
                decoded = base64.b64decode(env_key).decode("utf-8")
                info = json.loads(decoded)
            from google.oauth2 import service_account
            return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
        except Exception as e:
            logger.error(f"Failed to parse GSC_SERVICE_ACCOUNT_KEY from env: {e}")

    if LOCAL_KEY_PATH.exists():
        from google.oauth2 import service_account
        logger.info(f"Using local key file: {LOCAL_KEY_PATH.name}")
        return service_account.Credentials.from_service_account_file(str(LOCAL_KEY_PATH), scopes=SCOPES)

    logger.error("No valid Google Service Account credentials found!")
    return None

def fetch_latest_wordpress_urls(limit=10):
    """Fetch the most recent published post URLs from WordPress REST API."""
    wp_url = os.getenv("WP_BASE_URL", "https://el-mordjene.info").rstrip("/")
    urls = []
    try:
        res = requests.get(f"{wp_url}/wp-json/wp/v2/posts?per_page={limit}&status=publish", timeout=15)
        if res.status_code == 200:
            posts = res.json()
            for p in posts:
                link = p.get("link")
                if link and link not in urls:
                    urls.append(link)
    except Exception as e:
        logger.warning(f"Could not fetch URLs from WordPress REST API: {e}")

    # Fallback / Supplement from local published_posts.json
    published_json_path = Path(__file__).parent / "published_posts.json"
    if published_json_path.exists():
        try:
            with open(published_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in reversed(data):
                    if isinstance(item, str) and item.startswith("http"):
                        url = item
                    elif isinstance(item, dict):
                        url = item.get("post_url") or item.get("url")
                    else:
                        url = None
                    if url and url not in urls:
                        urls.append(url)
                    if len(urls) >= limit: break
        except Exception as e:
            logger.warning(f"Could not read published_posts.json: {e}")

    return urls[:limit]

def submit_url_to_google(credentials, url, action="URL_UPDATED"):
    """Submit a single URL to Google Indexing API."""
    from google.auth.transport.requests import Request
    credentials.refresh(Request())
    headers = {
        "Authorization": f"Bearer {credentials.token}",
        "Content-Type": "application/json"
    }
    payload = {
        "url": url,
        "type": action
    }
    res = requests.post(INDEXING_API_ENDPOINT, headers=headers, json=payload, timeout=15)
    return res.status_code, res.text

def main():
    logger.info("=== GOOGLE INDEXING API AUTOMATED SUBMITTER ===")
    creds = get_service_account_credentials()
    if not creds:
        logger.error("Aborting: Missing credentials.")
        return

    urls = fetch_latest_wordpress_urls(limit=10)
    if not urls:
        logger.warning("No URLs found to submit.")
        return

    logger.info(f"Found {len(urls)} target URLs for Google Indexing submission:")
    success_count = 0

    for idx, target_url in enumerate(urls, 1):
        try:
            status_code, resp_text = submit_url_to_google(creds, target_url)
            if status_code == 200:
                logger.info(f" [{idx}/{len(urls)}] SUCCESS (200 OK): {target_url}")
                success_count += 1
            else:
                logger.warning(f" [{idx}/{len(urls)}] FAILED ({status_code}): {target_url} -> {resp_text[:150]}")
        except Exception as e:
            logger.error(f" [{idx}/{len(urls)}] ERROR for {target_url}: {e}")

    logger.info(f"=== SUBMISSION COMPLETE: {success_count}/{len(urls)} URLs successfully sent to Google Indexing API ===")

if __name__ == "__main__":
    main()
