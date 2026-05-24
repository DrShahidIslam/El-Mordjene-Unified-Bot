import os
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

def get_pinterest_stats():
    token = os.getenv("PINTEREST_ACCESS_TOKEN")
    if not token:
        # Check for token file as in pin_generator.py
        root_dir = Path(__file__).parent
        token_file = root_dir / "pinterest_token.json"
        if token_file.exists():
            try:
                with open(token_file, "r") as f:
                    token_data = json.load(f)
                    token = token_data.get("access_token")
            except:
                pass
        
        if not token:
            print("Error: PINTEREST_ACCESS_TOKEN not found in .env or pinterest_token.json")
            return

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # 1. Get user account info
    print("==================================================")
    print("          PINTEREST ACCOUNT DETAILS               ")
    print("==================================================")
    res = requests.get("https://api.pinterest.com/v5/user_account", headers=headers)
    if res.status_code == 200:
        user_info = res.json()
        print(f"Account Username:  {user_info.get('username')}")
        print(f"Account Type:      {user_info.get('account_type')}")
        print(f"Website URL:       {user_info.get('website_url')}")
        print(f"Profile Image:     {user_info.get('profile_image')}")
    else:
        print(f"Error fetching account info: {res.status_code} - {res.text}")
        return

    # 2. Get user analytics (past 30 days with 2 days latency buffer)
    end_date = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=32)).strftime("%Y-%m-%d")
    
    print("\n==================================================")
    print(f"   USER ANALYTICS ({start_date} to {end_date})")
    print("==================================================")
    
    params = {
        "start_date": start_date,
        "end_date": end_date,
        "statistics": "IMPRESSION,PIN_CLICK,OUTBOUND_CLICK,SAVE"
    }
    
    res = requests.get("https://api.pinterest.com/v5/user_account/analytics", headers=headers, params=params)
    if res.status_code == 200:
        analytics = res.json()
        daily_data = analytics.get("all", {}).get("daily_metrics", [])
        
        total_impressions = 0
        total_pin_clicks = 0
        total_outbound_clicks = 0
        total_saves = 0
        active_days = 0
        
        for day in daily_data:
            metrics = day.get("metrics", {})
            imp = metrics.get("IMPRESSION", 0)
            p_click = metrics.get("PIN_CLICK", 0)
            out_click = metrics.get("OUTBOUND_CLICK", 0)
            save = metrics.get("SAVE", 0)
            
            total_impressions += imp
            total_pin_clicks += p_click
            total_outbound_clicks += out_click
            total_saves += save
            
            if imp > 0 or p_click > 0 or out_click > 0 or save > 0:
                active_days += 1
                
        print(f"Total Impressions:     {total_impressions}")
        print(f"Total Pin Clicks:      {total_pin_clicks}")
        print(f"Total Outbound Clicks: {total_outbound_clicks}")
        print(f"Total Saves:           {total_saves}")
        
        # Calculate CTRs
        pin_ctr = (total_pin_clicks / total_impressions * 100) if total_impressions > 0 else 0.0
        out_ctr = (total_outbound_clicks / total_impressions * 100) if total_impressions > 0 else 0.0
        print(f"Pin Click CTR:         {pin_ctr:.2f}%")
        print(f"Outbound Click CTR:    {out_ctr:.2f}%")
        print(f"Active Days with Activity: {active_days} / {len(daily_data)}")
    else:
        print(f"Error fetching user analytics: {res.status_code} - {res.text}")

    # 3. Local Automation Queue Status
    print("\n==================================================")
    print("          LOCAL AUTOMATION QUEUE STATUS           ")
    print("==================================================")
    queue_path = Path(__file__).parent / "topic_queue.json"
    if queue_path.exists():
        try:
            with open(queue_path, "r") as f:
                queue = json.load(f)
            
            total_topics = len(queue)
            completed_wp = sum(1 for t in queue if t.get("wp_status") == "done")
            pending_wp = sum(1 for t in queue if t.get("wp_status") == "pending")
            
            topics_with_pins = [t for t in queue if t.get("pin_count", 0) > 0]
            total_pins = sum(t.get("pin_count", 0) for t in queue)
            
            print(f"Total Topics in Queue:        {total_topics}")
            print(f"WordPress Published:          {completed_wp}")
            print(f"WordPress Pending:            {pending_wp}")
            print(f"Topics with Generated Pins:   {len(topics_with_pins)}")
            print(f"Total Pins Created:           {total_pins}")
            
            if topics_with_pins:
                print("\nMost Recent Pinned Topics:")
                # Sort by published_at or list the last few
                pinned_sorted = sorted(
                    [t for t in topics_with_pins if "published_at" in t], 
                    key=lambda x: x["published_at"], 
                    reverse=True
                )
                for t in pinned_sorted[:5]:
                    print(f" - {t['topic']} ({t.get('pin_count')} pins, published {t.get('published_at')[:10]})")
        except Exception as e:
            print(f"Error reading topic_queue.json: {e}")
    else:
        print("topic_queue.json not found in root directory.")

    # 4. Get boards list
    print("\n==================================================")
    print("              PINTEREST BOARDS                    ")
    print("==================================================")
    res = requests.get("https://api.pinterest.com/v5/boards", headers=headers)
    if res.status_code == 200:
        boards = res.json().get("items", [])
        for board in boards:
            print(f"Board: {board['name']} (ID: {board['id']})")
    else:
        print(f"Error fetching boards: {res.status_code} - {res.text}")
    print("==================================================")

if __name__ == "__main__":
    get_pinterest_stats()
