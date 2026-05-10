import argparse
import hashlib
import json
import logging
import os
import sys
import time
from datetime import datetime
from publisher.wordpress_client import test_wordpress_connection

# Prevent UnicodeEncodeError when printing emojis to standard Windows consoles
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import config
from database.db import (
    get_connection, cleanup_old_data, save_topic_to_cache,
    record_published_topic, get_recent_published_topics,
    is_topic_already_covered
)
from sources.pinterest_trends_monitor import fetch_pinterest_trends
from writer.article_generator import generate_article
from publisher.wordpress_client import (
    create_post, test_wordpress_connection
)
from publisher.image_handler import generate_featured_image

# --- Unified Pinterest Integration ---
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "pinterest_engine"))
try:
    from pin_generator import process_new_pin
except ImportError:
    process_new_pin = None

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    handlers=[logging.StreamHandler(), logging.FileHandler(config.LOG_FILE, encoding='utf-8')]
)
logger = logging.getLogger("agent")

STATE_FILE = "agent_state.json"

def _load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f: return json.load(f)
        except: pass
    return {"last_scan": None, "scan_count": 0, "published_today": []}

def _save_state(state):
    with open(STATE_FILE, "w") as f: json.dump(state, f, indent=2)

def _load_published_posts():
    path = os.path.join(os.path.dirname(__file__), "published_posts.json")
    if os.path.exists(path):
        try:
            with open(path, "r") as f: return json.load(f)
        except: return {}
    return {}

def _finish_publication(article, post_id, post_url, state):
    logger.info(f"   Published: {article['title']}")
    logger.info(f"   URL: {post_url}")
    state["last_published_url"] = post_url
    state["published_today"].append({
        "title": article["title"],
        "url": post_url,
        "time": datetime.utcnow().isoformat()
    })

def auto_pilot_process(topic, state):
    """Zero-click automation: Generate, Image, and Publish."""
    topic_title = topic.get("topic", "Unknown")
    logger.info(f"🚀 AUTO-PILOT: Processing '{topic_title}'...")
    
    # 1. Generate Article
    try:
        article = generate_article(topic)
        if not article: return False
    except Exception as e:
        logger.error(f"Auto-Pilot generation error: {e}")
        return False

    # 2. Generate Image
    image_path = None
    try:
        source_url = topic.get("top_url", "")
        webp_path, jpg_path = generate_featured_image(article["title"], source_url=source_url)
        image_path = jpg_path or webp_path
    except Exception as e:
        logger.warning(f"Auto-Pilot Image failure: {e}")

    # 3. Publish to WordPress
    try:
        status = config.WP_DEFAULT_STATUS
        result = create_post(article, featured_image_path=image_path, status=status)
        if result:
            post_url = result.get("post_url", "")
            post_id = result.get("post_id")
            
            # Record in DB
            conn = get_connection()
            record_published_topic(conn, article["title"], article["slug"], ",".join(article.get("tags", [])))
            conn.close()
            
            # The Pinterest Flow is now handled by the dedicated Pin Worker (GitHub Action)
            # which reads from topic_queue.json once wp_status is 'done'.
            
            _finish_publication(article, post_id, post_url, state)
            return True
    except Exception as e:
        logger.error(f"Auto-Pilot Publish error: {e}")
        
    return False

def _load_queue():
    queue_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "topic_queue.json")
    if os.path.exists(queue_path):
        try:
            with open(queue_path, "r") as f: return json.load(f)
        except: return []
    return []

def _save_queue(queue):
    queue_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "topic_queue.json")
    with open(queue_path, "w") as f: json.dump(queue, f, indent=2)

def run_scan(state):
    """Perform one full trend scan (Queue-first) and trigger auto-pilot."""
    # PRE-RUN CONNECTION CHECK
    if not test_wordpress_connection():
        logger.error("🛑 ABORTING SCAN: WordPress connection failed. Saving resources.")
        return

    logger.info("=" * 60)
    logger.info(" Starting scan cycle...")
    logger.info("=" * 60)

    max_per_run = int(config.POSTS_PER_RUN or 2)
    published_count = 0
    
    # 1. Check Topic Queue First
    queue = _load_queue()
    pending = [t for t in queue if t.get("wp_status") == "pending"]
    pending.sort(key=lambda x: x.get("priority", 99))

    if pending:
        logger.info(f"Found {len(pending)} pending topics in queue.")
        conn = get_connection()
        for topic in pending:
            if published_count >= max_per_run: break
            
            # CHECK FOR EXISTING CONTENT FIRST
            is_covered, match_title, score = is_topic_already_covered(conn, topic["topic"], threshold=0.6)
            if is_covered:
                logger.info(f"Topic '{topic['topic']}' already covered by '{match_title}' (Score: {score:.2f}). Skipping generation.")
                topic["wp_status"] = "done"
                # Find the URL for the existing post
                # We'll look in published_posts.json or db
                published_list = _load_published_posts()
                existing_url = next((p["url"] for p in published_list.values() if p.get("anchor") == match_title), "")
                topic["wp_url"] = existing_url
                topic["published_at"] = datetime.utcnow().isoformat()
                topic["note"] = f"Auto-linked to existing: {match_title}"
                _save_queue(queue)
                continue

            # Prepare topic for auto-pilot
            try:
                if auto_pilot_process(topic, state):
                    topic["wp_status"] = "done"
                    topic["wp_url"] = state.get("last_published_url", "")
                    topic["published_at"] = datetime.utcnow().isoformat()
                    published_count += 1
                else:
                    # Increment retry or mark as failed
                    retries = topic.get("retries", 0) + 1
                    topic["retries"] = retries
                    if retries >= 3:
                        topic["wp_status"] = "failed"
                        logger.warning(f"Topic '{topic['topic']}' failed after 3 attempts. Marking as failed.")
            except Exception as e:
                logger.error(f"Critical error processing queue topic: {e}")
            
            _save_queue(queue) # Update queue state
            if published_count >= max_per_run: break
            time.sleep(10)
        conn.close()

    # 2. If we still have capacity, fetch from Pinterest (Fallback)
    if published_count < max_per_run:
        logger.info(f"Queue empty or limit not reached. Fetching Pinterest trends... ({published_count}/{max_per_run})")
        trends = fetch_pinterest_trends()
        if trends:
            conn = get_connection()
            for topic in trends:
                if published_count >= max_per_run: break
                
                # Deduplicate against queue and cache
                if any(q["topic"].lower() == topic["topic"].lower() for q in queue):
                    continue

                story_hash = hashlib.sha256(topic["topic"].encode()).hexdigest()[:16]
                topic["story_hash"] = story_hash
                save_topic_to_cache(conn, story_hash, topic)

                if auto_pilot_process(topic, state):
                    published_count += 1
                    time.sleep(10)
            conn.close()

    cleanup_old_data(get_connection())
    state["last_scan"] = datetime.utcnow().isoformat()
    state["scan_count"] += 1
    _save_state(state)
    logger.info(f"Scan complete. Published {published_count} articles.")

def main():
    parser = argparse.ArgumentParser(description="El-Mordjene News Agent (Headless)")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--test", action="store_true", help="Test connections")
    args = parser.parse_args()

    state = _load_state()

    if args.test:
        print("Testing connections...")
        wp_ok = test_wordpress_connection()
        print(f"WordPress: {'OK' if wp_ok else 'FAILED'}")
        # Test Gemini
        from gemini_client import generate_content_with_fallback
        try:
            res = generate_content_with_fallback(model=config.GEMINI_MODEL, contents="Hi")
            print(f"Gemini: OK ({config.GEMINI_MODEL})")
        except Exception as e:
            print(f"Gemini: FAILED ({e})")
        return

    if args.once:
        run_scan(state)
        return

    # Continuous loop
    logger.info(f"Headless agent starting. Interval: {config.SCAN_INTERVAL_MINUTES}m")
    while True:
        try:
            run_scan(state)
            logger.info(f"Sleeping for {config.SCAN_INTERVAL_MINUTES} minutes...")
            time.sleep(config.SCAN_INTERVAL_MINUTES * 60)
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"Main loop error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
