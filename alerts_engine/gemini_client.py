"""
Gemini Client Helper — Uses Raw HTTP to bypass library-specific 400/401 errors.
Handles API key rotation and retries when rate limits are exhausted.
"""
import logging
import time
import re
import requests
import json
import config

logger = logging.getLogger(__name__)

def generate_content_with_fallback(
    model,
    contents,
    generation_config=None,
    max_retries_per_key=3,
    base_delay=5
):
    """
    Call Gemini API via Raw HTTP with exponential backoff on 429 errors.
    Cycles through available API keys in config.GEMINI_API_KEYS.
    """
    keys = config.GEMINI_API_KEYS
    if not keys:
        raise ValueError("No Gemini API keys configured.")

    logger.info(f"🔑 Gemini Client: Loaded {len(keys)} keys. First key starts with: {keys[0][:10]}...")

    # Convert library-style contents to raw JSON if needed
    if not isinstance(contents, list):
        # Basic prompt to parts conversion
        if isinstance(contents, str):
            payload_contents = [{"parts": [{"text": contents}]}]
        else:
            payload_contents = contents
    else:
        payload_contents = contents

    for key_idx, current_key in enumerate(keys):
        clean_key = str(current_key).strip().strip("'").strip('"')
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={clean_key}"
        
        for attempt in range(max_retries_per_key + 1):
            try:
                headers = {'Content-Type': 'application/json'}
                payload = {
                    "contents": payload_contents
                }
                if generation_config:
                    # Note: We'd need to map generation_config to the HTTP schema if used
                    pass

                response = requests.post(url, headers=headers, json=payload, timeout=60)
                
                if response.status_code == 200:
                    # Mocking a response object that looks like the library response
                    res_data = response.json()
                    class MockResponse:
                        def __init__(self, data):
                            self.data = data
                            try:
                                self.text = data['candidates'][0]['content']['parts'][0]['text']
                            except:
                                self.text = ""
                    return MockResponse(res_data)

                error_data = response.json().get('error', {})
                error_msg = error_data.get('message', 'Unknown error')
                error_code = response.status_code

                if error_code == 429:
                    if attempt >= max_retries_per_key:
                        break
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"  ⏳ Gemini rate limited on key {key_idx + 1} (429). Waiting {delay}s...")
                    time.sleep(delay)
                    continue
                
                # If it's a 400/401, try the next key immediately
                logger.warning(f"  ⚠️ Error from key {key_idx + 1} ({error_code}): {error_msg}. Trying next key...")
                break

            except Exception as e:
                logger.warning(f"  ⚠️ Request error on key {key_idx + 1}: {e}")
                break

    raise Exception("All Gemini API keys failed or exhausted quota via Raw HTTP.")

def generate_image_with_gemini_flash(prompt, **kwargs):
    # Fallback to text for now as image gen via HTTP is more complex
    return None

def generate_image_with_fallback(model, prompt, **kwargs):
    # Logic for image gen via HTTP could be added here if needed
    raise NotImplementedError("Image generation via raw HTTP not implemented yet.")
