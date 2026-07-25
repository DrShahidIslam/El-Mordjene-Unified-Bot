import os
import json
import requests
import base64
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("gsc_indexer")

# Configuration
LOCAL_KEY_PATH = Path(__file__).parent / "food-trends-blog-e2b06405bfe0.json"
STATE_FILE_PATH = Path(__file__).parent / "indexed_state.json"
INDEXING_API_ENDPOINT = "https://indexing.googleapis.com/v3/urlNotifications:publish"
SCOPES = ["https://www.googleapis.com/auth/indexing"]
BATCH_SIZE = 10

def get_service_account_credentials():
    """Retrieve service account credentials from env variable or local JSON file."""
    env_key = os.getenv("GSC_SERVICE_ACCOUNT_KEY")
    if env_key:
        try:
            if env_key.strip().startswith("{"):
                info = json.loads(env_key)
            else:
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

def fetch_all_live_wordpress_urls():
    """Fetch ALL published post URLs from WordPress REST API using pagination."""
    wp_url = os.getenv("WP_BASE_URL", "https://el-mordjene.info").rstrip("/")
    all_urls = []
    page = 1
    logger.info("Fetching complete list of live site URLs from WordPress REST API...")
    
    while True:
        try:
            res = requests.get(
                f"{wp_url}/wp-json/wp/v2/posts",
                params={"per_page": 100, "page": page, "status": "publish"},
                timeout=15
            )
            if res.status_code == 200:
                posts = res.json()
                if not posts:
                    break
                for p in posts:
                    link = p.get("link")
                    if link and link not in all_urls:
                        all_urls.append(link)
                page += 1
            else:
                break
        except Exception as e:
            logger.warning(f"Error fetching page {page} from WordPress: {e}")
            break

    # Supplement from local published_posts.json if available
    published_json_path = Path(__file__).parent / "published_posts.json"
    if published_json_path.exists():
        try:
            with open(published_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    if isinstance(item, str) and item.startswith("http"):
                        url = item
                    elif isinstance(item, dict):
                        url = item.get("post_url") or item.get("url")
                    else:
                        url = None
                    if url and url not in all_urls:
                        all_urls.append(url)
        except Exception as e:
            logger.warning(f"Could not read published_posts.json: {e}")

    logger.info(f"Total live post URLs discovered: {len(all_urls)}")
    return all_urls

def load_indexer_state():
    """Load indexing progress state from JSON file."""
    if STATE_FILE_PATH.exists():
        try:
            with open(STATE_FILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not read state file: {e}")

    return {
        "submitted_urls": [],
        "current_cycle": 1,
        "total_submissions_all_time": 0,
        "last_run": None
    }

def save_indexer_state(state):
    """Save indexing progress state to JSON file."""
    try:
        with open(STATE_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        logger.info(f"State saved to {STATE_FILE_PATH.name}")
    except Exception as e:
        logger.error(f"Failed to save state file: {e}")

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

def select_next_batch(all_urls, state, batch_size=BATCH_SIZE):
    """Select the next batch of unsubmitted URLs for the current cycle."""
    submitted_set = set(state.get("submitted_urls", []))
    unsubmitted = [u for u in all_urls if u not in submitted_set]

    # If all URLs in current cycle have been submitted, reset cycle!
    if not unsubmitted and all_urls:
        logger.info(f"🎉 CYCLE {state.get('current_cycle', 1)} COMPLETE! All {len(all_urls)} live site URLs have been submitted.")
        logger.info("Starting fresh Cycle for recrawl pings...")
        state["current_cycle"] = state.get("current_cycle", 1) + 1
        state["submitted_urls"] = []
        submitted_set = set()
        unsubmitted = all_urls

    batch = unsubmitted[:batch_size]

    # If batch is smaller than requested batch_size and more URLs exist, roll over
    if len(batch) < batch_size and len(all_urls) > len(batch):
        logger.info("Reached end of current URL set. Rolling over to start a new cycle...")
        state["current_cycle"] = state.get("current_cycle", 1) + 1
        state["submitted_urls"] = []
        needed = batch_size - len(batch)
        remainder = [u for u in all_urls if u not in set(batch)][:needed]
        batch.extend(remainder)

    return batch

def main():
    logger.info("=== GOOGLE INDEXING API ROLLING CAROUSEL INDEXER ===")
    creds = get_service_account_credentials()
    if not creds:
        logger.error("Aborting: Missing credentials.")
        return

    all_urls = fetch_all_live_wordpress_urls()
    if not all_urls:
        logger.warning("No URLs found on live site.")
        return

    state = load_indexer_state()
    batch = select_next_batch(all_urls, state, BATCH_SIZE)

    logger.info(f"Cycle {state.get('current_cycle', 1)} Progress: {len(state.get('submitted_urls', []))}/{len(all_urls)} URLs submitted.")
    logger.info(f"Submitting batch of {len(batch)} URLs to Google Indexing API:")

    success_count = 0
    for idx, target_url in enumerate(batch, 1):
        try:
            status_code, resp_text = submit_url_to_google(creds, target_url)
            if status_code == 200:
                logger.info(f"  [{idx}/{len(batch)}] SUCCESS (200 OK): {target_url}")
                if target_url not in state["submitted_urls"]:
                    state["submitted_urls"].append(target_url)
                state["total_submissions_all_time"] = state.get("total_submissions_all_time", 0) + 1
                success_count += 1
            else:
                logger.warning(f"  [{idx}/{len(batch)}] FAILED ({status_code}): {target_url} -> {resp_text[:150]}")
        except Exception as e:
            logger.error(f"  [{idx}/{len(batch)}] ERROR for {target_url}: {e}")

    state["last_run"] = datetime.utcnow().isoformat()
    save_indexer_state(state)

    logger.info(f"=== SUBMISSION COMPLETE: {success_count}/{len(batch)} URLs sent to Google Indexing API (Cycle {state.get('current_cycle')}) ===")

if __name__ == "__main__":
    main()
