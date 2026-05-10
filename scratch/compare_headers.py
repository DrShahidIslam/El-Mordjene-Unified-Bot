import requests
import os
import base64
from dotenv import load_dotenv

# Replicate config.py behavior roughly
load_dotenv()
wp_url = os.getenv("WP_BASE_URL", "https://el-mordjene.info").rstrip('/')
username = os.getenv("WP_USERNAME")
password = os.getenv("WP_APP_PASSWORD")

def _get_headers_bad():
    creds = f"{username}:{password}"
    token = base64.b64encode(creds.encode()).decode()
    h = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Authorization": f"Basic {token}",
        "Referer": f"{wp_url}/",
        "Accept": "application/json, text/plain, */*",
    }
    return h

def _get_headers_good():
    creds = f"{username}:{password}"
    token = base64.b64encode(creds.encode()).decode()
    return {
        "Authorization": f"Basic {token}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

print("Testing 'BAD' headers (from wordpress_client.py)...")
h_bad = _get_headers_bad()
r_bad = requests.get(f"{wp_url}/wp-json/wp/v2/users/me", headers=h_bad)
print(f"Status: {r_bad.status_code}")
if r_bad.status_code != 200:
    print(f"Error: {r_bad.text}")

print("\nTesting 'GOOD' headers (from test_wp.py)...")
h_good = _get_headers_good()
r_good = requests.get(f"{wp_url}/wp-json/wp/v2/users/me", headers=h_good)
print(f"Status: {r_good.status_code}")
if r_good.status_code != 200:
    print(f"Error: {r_good.text}")
