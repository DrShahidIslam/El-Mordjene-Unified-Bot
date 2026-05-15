import os
import requests
import base64
from dotenv import load_dotenv

load_dotenv()

def test_wp():
    url = os.getenv("WP_BASE_URL")
    user = os.getenv("WP_USERNAME")
    pw = os.getenv("WP_APP_PASSWORD")
    
    if not all([url, user, pw]):
        print("Missing WP credentials in .env")
        return

    print(f"Testing WP connection to {url}...")
    auth = base64.b64encode(f"{user}:{pw}".encode()).decode()
    headers = {"Authorization": f"Basic {auth}"}
    
    try:
        res = requests.get(f"{url}/wp-json/wp/v2/posts", headers=headers, params={"per_page": 1})
        if res.status_code == 200:
            posts = res.json()
            if posts:
                print(f"SUCCESS: Connected! Latest post: {posts[0]['title']['rendered']}")
            else:
                print("SUCCESS: Connected, but no posts found.")
        else:
            print(f"FAIL: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_wp()
