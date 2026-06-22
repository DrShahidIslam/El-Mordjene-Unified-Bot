import sys
import os
import json
from datetime import datetime

# Add the alerts_engine directory to sys.path to import config and modules
sys.path.append(os.path.abspath("alerts_engine"))

from sources.pinterest_trends_monitor import fetch_pinterest_trends
import config

def main():
    if not config.PINTEREST_ACCESS_TOKEN:
        print("Warning: PINTEREST_ACCESS_TOKEN not set in config.")
        
    print("Fetching Pinterest trends...")
    trends = fetch_pinterest_trends()
    
    if not trends:
        print("No trends fetched. Token might be expired or invalid.")
        return
        
    print(f"Fetched {len(trends)} unique trends.")
    
    queue_path = "topic_queue.json"
    with open(queue_path, "r", encoding="utf-8") as f:
        queue = json.load(f)
        
    existing_topics = {t["topic"].lower() for t in queue}
    
    added = 0
    for t in trends:
        title = t["topic"]
        if title.lower() not in existing_topics:
            new_entry = {
                "topic": title,
                "intent": "trend",
                "wp_status": "pending",
                "wp_url": "",
                "pin_count": 0,
                "priority": 10,
                "source": "Pinterest API (Trends)",
                "published_at": ""
            }
            queue.append(new_entry)
            added += 1
            print(f"Added new trend: {title}")
            
    if added > 0:
        with open(queue_path, "w", encoding="utf-8") as f:
            json.dump(queue, f, indent=2)
        print(f"Successfully added {added} new trends to topic_queue.json.")
    else:
        print("No new trends to add (all were already in the queue).")

if __name__ == "__main__":
    main()
