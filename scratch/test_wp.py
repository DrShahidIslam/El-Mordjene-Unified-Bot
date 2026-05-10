import requests
import os
import base64
from dotenv import load_dotenv

load_dotenv()

wp_url = os.getenv("WP_BASE_URL", "https://el-mordjene.info").rstrip('/')
username = os.getenv("WP_USERNAME")
password = os.getenv("WP_APP_PASSWORD")

print(f"--- WP AUTH TEST ---")
print(f"URL: {wp_url}")
print(f"User: {username}")

credentials = f"{username}:{password}"
token = base64.b64encode(credentials.encode()).decode()
headers = {
    "Authorization": f"Basic {token}",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

try:
    response = requests.get(f"{wp_url}/wp-json/wp/v2/users/me", headers=headers, timeout=20)
    if response.status_code == 200:
        user = response.json()
        print(f"AUTH SUCCESS: {user.get('name')} (ID: {user.get('id')})")
        
        # Test Media
        print("Testing Media Upload...")
        media_headers = headers.copy()
        media_headers.update({
            "Content-Disposition": 'attachment; filename="test_auth.txt"',
            "Content-Type": "text/plain",
        })
        m_res = requests.post(f"{wp_url}/wp-json/wp/v2/media", headers=media_headers, data=b"test", timeout=20)
        print(f"Media Upload Status: {m_res.status_code}")
        
        # Test Post
        print("Testing Post Creation...")
        p_data = {"title": "Test from Bot", "content": "Test", "status": "draft"}
        p_res = requests.post(f"{wp_url}/wp-json/wp/v2/posts", headers=headers, json=p_data, timeout=20)
        print(f"Post Creation Status: {p_res.status_code}")
        if p_res.status_code in (200, 201):
            print(f"Post ID: {p_res.json().get('id')}")
        else:
            print(f"Error: {p_res.text}")
    else:
        print(f"AUTH FAILED: {response.status_code}")
except Exception as e:
    print(f"ERROR: {e}")
