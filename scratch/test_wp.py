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
if password:
    print(f"Password: {password[:4]}...{password[-4:]}")
else:
    print("Password: MISSING")

# Test simple 'me' endpoint
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
        print(f"\nSUCCESS! Authenticated as: {user.get('name')} (ID: {user.get('id')})")
        
        # Test Media Upload
        print("\n--- TESTING MEDIA UPLOAD ---")
        dummy_content = b"fake image data"
        media_headers = headers.copy()
        media_headers.update({
            "Content-Disposition": 'attachment; filename="test_auth.txt"',
            "Content-Type": "text/plain",
        })
        
        media_res = requests.post(f"{wp_url}/wp-json/wp/v2/media", headers=media_headers, data=dummy_content, timeout=20)
        if media_res.status_code in (200, 201):
            print(f"✅ MEDIA UPLOAD SUCCESS! (ID: {media_res.json().get('id')})")
        else:
            print(f"❌ MEDIA UPLOAD FAILED: {media_res.status_code}")
            print(f"Response: {media_res.text}")
    else:
        print(f"\nFAILED: {response.status_code}")
        print(f"Response: {response.text}")
except Exception as e:
    print(f"\nCONNECTION ERROR: {e}")
