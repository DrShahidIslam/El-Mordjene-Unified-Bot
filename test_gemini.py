import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_gemini():
    keys = os.getenv("GEMINI_API_KEYS", "").split(",")
    model = os.getenv("GEMINI_TEXT_MODEL", "gemini-1.5-flash") # Fallback to 1.5 if 3.1 is invalid
    
    print(f"Testing Gemini with model: {model}")
    
    for i, key in enumerate(keys):
        clean_key = key.strip().strip("'").strip('"')
        if not clean_key: continue
        
        print(f"Testing Key {i+1} (starts with {clean_key[:5]})...")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={clean_key}"
        payload = {"contents": [{"parts": [{"text": "Hello, are you working?"}]}]}
        
        try:
            res = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=15)
            if res.status_code == 200:
                print(f"SUCCESS: Key {i+1} is working!")
            else:
                print(f"FAIL: Key {i+1} failed: {res.status_code} - {res.text}")
        except Exception as e:
            print(f"ERROR: Key {i+1} error: {e}")

if __name__ == "__main__":
    test_gemini()
