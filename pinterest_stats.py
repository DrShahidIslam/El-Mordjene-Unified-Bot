import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def get_pinterest_stats():
    token = os.getenv("PINTEREST_ACCESS_TOKEN")
    if not token:
        print("Error: PINTEREST_ACCESS_TOKEN not found in .env")
        return

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # 1. Get user account info
    print("Fetching account info...")
    res = requests.get("https://api.pinterest.com/v5/user_account", headers=headers)
    if res.status_code == 200:
        user_info = res.json()
        print(f"Account: {user_info.get('username')}")
        print(f"Account Type: {user_info.get('account_type')}")
    else:
        print(f"Error fetching account info: {res.status_code} - {res.text}")
        return

    # 2. Get user analytics (last 30 days)
    print("\nFetching user analytics (last 30 days)...")
    params = {
        "start_date": "2026-04-15",
        "end_date": "2026-05-15",
        "statistics": "IMPRESSION,PIN_CLICK,OUTBOUND_CLICK,SAVE"
    }
    res = requests.get("https://api.pinterest.com/v5/user_account/analytics", headers=headers, params=params)
    if res.status_code == 200:
        analytics = res.json()
        print("Raw Analytics Data:", json.dumps(analytics, indent=2))
    else:
        print(f"Error fetching user analytics: {res.status_code} - {res.text}")

    # 3. Get boards and their analytics
    print("\nFetching boards and top pins...")
    res = requests.get("https://api.pinterest.com/v5/boards", headers=headers)
    if res.status_code == 200:
        boards = res.json().get("items", [])
        for board in boards:
            print(f"Board: {board['name']} (ID: {board['id']})")
            # Fetch board analytics
            b_params = {
                "start_date": "2026-04-15",
                "end_date": "2026-05-15",
                "statistics": "IMPRESSION,PIN_CLICK,OUTBOUND_CLICK,SAVE"
            }
            b_res = requests.get(f"https://api.pinterest.com/v5/boards/{board['id']}/analytics", headers=headers, params=b_params)
            if b_res.status_code == 200:
                b_analytics = b_res.json()
                summary = b_analytics.get("all", {}).get("summary", {})
                print(f"  Analytics: {summary}")
            else:
                print(f"  Error fetching board analytics: {b_res.status_code}")
    else:
        print(f"Error fetching boards: {res.status_code} - {res.text}")

if __name__ == "__main__":
    get_pinterest_stats()
