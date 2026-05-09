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
print(f"Password: {password[:4]}...{password[-4:]}")

# Test simple 'me' endpoint
credentials = f"{username}:{password}"
token = base64.b64encode(credentials.encode()).decode()
headers = {"Authorization": f"Basic {token}"}

response = requests.get(f"{wp_url}/wp-json/wp/v2/users/me", headers=headers)

if response.status_code == 200:
    user = response.json()
    print(f"\n✅ SUCCESS! Authenticated as: {user['name']} (ID: {user['id']})")
    print(f"Permissions: {user['roles']}")
else:
    print(f"\n❌ FAILED: {response.status_code}")
    print(f"Response: {response.text}")
    print("\nPRO-TIP: Double check that you are using an 'Application Password' (4-character blocks), not your main login password.")
