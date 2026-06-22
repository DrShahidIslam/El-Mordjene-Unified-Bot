import json
import os
from datetime import datetime

queue_path = "topic_queue.json"
published_path = "alerts_engine/published_posts.json"

with open(queue_path, "r", encoding="utf-8") as f:
    queue = json.load(f)

print(f"Loaded {len(queue)} topics from queue.")

target = next((t for t in queue if t.get("wp_status") == "done" and t.get("pin_count", 0) < 3), None)
print(f"Next target: {target}")

with open(published_path, "r", encoding="utf-8") as f:
    published = json.load(f)

# Collect existing topic titles or URLs to avoid duplicates
existing_titles = {t["topic"].lower() for t in queue}
existing_urls = {t.get("wp_url", "").lower() for t in queue}

added = 0
for slug, info in published.items():
    title = info["anchor"]
    url = info["url"]
    
    if title.lower() not in existing_titles and url.lower() not in existing_urls:
        new_entry = {
            "topic": title,
            "intent": "trend",
            "wp_status": "done",
            "wp_url": url,
            "pin_count": 0,
            "priority": 20,
            "source": "manual_recovery",
            "published_at": datetime.utcnow().isoformat()
        }
        queue.append(new_entry)
        added += 1

if added > 0:
    with open(queue_path, "w", encoding="utf-8") as f:
        json.dump(queue, f, indent=2)
    print(f"Added {added} missing topics to queue.")
else:
    print("No missing topics found.")
