import os
import json
import base64
import requests
import textwrap
import random
import datetime
import shutil
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv
from pathlib import Path
import argparse
import urllib.parse
from google import genai
from huggingface_hub import InferenceClient

VERSION = "1.2.1"
print(f"--- PIN GENERATOR v{VERSION} START ---", flush=True)

# Load environment
root_dir = Path(__file__).parent.parent
env_path = root_dir / ".env"
load_dotenv(dotenv_path=env_path, override=True)

# API Configurations
SILICONFLOW_API_URL = "https://api.siliconflow.cn/v1/images/generations"
SILICONFLOW_MODEL = os.getenv("SILICONFLOW_MODEL", "Kwai-Kolors/Kolors")
PINTEREST_API_BASE = "https://api.pinterest.com/v5"

# Priority: Load token from dashboard OAuth first
PINTEREST_ACCESS_TOKEN = os.getenv("PINTEREST_ACCESS_TOKEN", "").strip()
token_file = root_dir / "pinterest_token.json"
if token_file.exists():
    try:
        with open(token_file, "r") as f:
            token_data = json.load(f)
            PINTEREST_ACCESS_TOKEN = token_data.get("access_token", PINTEREST_ACCESS_TOKEN)
    except: pass

hf_keys = os.getenv("HUGGINGFACE_API_KEY", "").split(",")
hf_keys = [k.strip() for k in hf_keys if k.strip()]
HUGGINGFACE_MODEL = "black-forest-labs/FLUX.1-schnell" 

GEMINI_API_KEYS = os.getenv("GEMINI_API_KEYS", "").split(",")
current_gemini_key_index = 0

def get_gemini_client():
    global current_gemini_key_index
    if not GEMINI_API_KEYS: return None
    key = GEMINI_API_KEYS[current_gemini_key_index].strip()
    return genai.Client(api_key=key)

client = get_gemini_client()

BRIDGE_PAGE_ROOT = Path("bridge_page")
BRIDGE_PAGE_URL_BASE = os.getenv("BRIDGE_PAGE_URL", "https://drshahidislam.github.io/Food-Trends-Blog/")
MOCK_MODE = os.getenv("MOCK_MODE", "false").lower() == "true"

WEEKLY_MAGAZINE_CSS = """
    :root { --primary: #f8f5f2; --accent: #8b2b2b; --text: #1a1a1a; --surface: #ffffff; }
    body { font-family: 'Georgia', serif; background-color: var(--primary); color: var(--text); margin: 0; padding: 0; scroll-behavior: smooth; }
    .header { background: var(--surface); padding: 60px 20px; text-align: center; border-bottom: 2px solid var(--accent); }
    .header h1 { margin: 0; font-size: 3rem; color: var(--accent); letter-spacing: 4px; text-transform: uppercase; font-weight: 900; }
    .header p { color: #666; font-family: 'Montserrat', sans-serif; letter-spacing: 2px; margin-top: 15px; text-transform: uppercase; font-size: 0.9rem; }
    .gallery-container { max-width: 900px; margin: 40px auto; padding: 0 20px; display: flex; flex-direction: column; gap: 60px; }
    .card { background: var(--surface); border-radius: 12px; overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.08); transition: transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); display: flex; flex-direction: column; border: 1px solid #eee; }
    .card:target { border: 3px solid var(--accent); transform: scale(1.02); box-shadow: 0 30px 60px rgba(139,43,43,0.2); }
    .card:hover { transform: translateY(-10px); }
    .card-img-wrapper { position: relative; width: 100%; padding-top: 65%; overflow: hidden; }
    .card-img { position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover; transition: transform 0.6s ease; }
    .card:hover .card-img { transform: scale(1.05); }
    .card-body { padding: 40px; text-align: center; }
    .card-title { font-size: 2.2rem; color: var(--text); margin: 0 0 20px 0; line-height: 1.2; font-weight: bold; }
    .card-excerpt { color: #444; font-family: 'Open Sans', sans-serif; font-size: 1.1rem; line-height: 1.8; margin-bottom: 30px; }
    .card-btn { display: block; background-color: var(--accent); color: white; text-align: center; padding: 20px 40px; text-decoration: none; border-radius: 50px; font-family: sans-serif; font-weight: 900; letter-spacing: 2px; transition: all 0.3s ease; text-transform: uppercase; font-size: 1.1rem; box-shadow: 0 10px 20px rgba(139,43,43,0.3); }
    .card-btn:hover { background-color: #1a1a1a; transform: scale(1.05); box-shadow: 0 15px 30px rgba(0,0,0,0.4); }
"""

# --- Core Functions ---

def _try_kolors(prompt, output_path):
    api_key = os.getenv("SILICONFLOW_API_KEY")
    if not api_key: return False
    try:
        print(f"DEBUG: Trying Kolors Fallback...", flush=True)
        payload = {
            "model": SILICONFLOW_MODEL,
            "prompt": f"{prompt}, food photography, high quality, realistic, 1024x1024",
            "image_size": "1024x1024"
        }
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        response = requests.post(SILICONFLOW_API_URL, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            resp_json = response.json()
            # Try multiple common SiliconFlow response formats
            img_url = None
            if "images" in resp_json and resp_json["images"]:
                img_url = resp_json["images"][0].get("url")
            elif "data" in resp_json and resp_json["data"]:
                img_url = resp_json["data"][0].get("url")
            
            if img_url:
                img_data = requests.get(img_url).content
                with open(output_path, "wb") as f: f.write(img_data)
                return True
            else:
                print(f"DEBUG: Kolors response missing image URL: {resp_json}")
    except Exception as e:
        print(f"DEBUG: Kolors fallback failed: {e}")
    return False

def _try_pollinations(prompt, output_path):
    try:
        print(f"DEBUG: Trying Pollinations Last Resort...", flush=True)
        encoded = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=768&height=1024&nologo=true&seed={random.randint(1,999999)}"
        res = requests.get(url, timeout=30)
        if res.status_code == 200:
            with open(output_path, "wb") as f: f.write(res.content)
            return True
    except Exception as e:
        print(f"DEBUG: Pollinations failed: {e}")
    return False

def generate_image(prompt, output_path):
    full_prompt = f"{prompt}, food photography, ultra-realistic, macro shot, 8k, professional lighting, editorial beauty photography, 768x1024"
    for i, key in enumerate(hf_keys):
        try:
            print(f"HuggingFace: Key {i+1}/{len(hf_keys)}...", flush=True)
            hf_client = InferenceClient(api_key=key)
            image = hf_client.text_to_image(full_prompt, model=HUGGINGFACE_MODEL)
            image.save(output_path)
            return True
        except Exception as e:
            print(f"HuggingFace Key {i+1} Error: {e}")
            continue
    if _try_kolors(prompt, output_path): return True
    if _try_pollinations(prompt, output_path): return True
    return False

def design_pin(image_path, title, output_path):
    img = Image.open(image_path).convert("RGBA")
    width, height = img.size
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    grad_height = int(height * 0.5)
    for y in range(height - grad_height, height):
        progress = (y - (height - grad_height)) / grad_height
        alpha = int(220 * (progress ** 1.5))
        draw.line([(0, y), (width, y)], fill=(42, 25, 16, alpha))
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)
    font_size = int(width * 0.08)
    font_paths = ["C:/Windows/Fonts/Montserrat-Bold.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", "arialbd.ttf"]
    font = None
    for fp in font_paths:
        try:
            if os.path.exists(fp):
                font = ImageFont.truetype(fp, font_size)
                break
        except: continue
    if not font: font = ImageFont.load_default()
    wrapped_lines = textwrap.wrap(title, width=18)
    line_h = font_size * 1.2
    y_text = height - (len(wrapped_lines) * line_h) - 150
    for line in wrapped_lines:
        w = draw.textlength(line, font=font)
        draw.text(((width-w)/2 + 2, y_text + 2), line, font=font, fill=(0,0,0,100))
        draw.text(((width-w)/2, y_text), line, font=font, fill=(255,255,255,255))
        y_text += line_h
    try:
        brand_font = ImageFont.truetype(font_paths[0], int(width * 0.035)) if font else None
        if brand_font:
            brand_text = "EL MORDJENE"
            bw = draw.textlength(brand_text, font=brand_font)
            draw.text(((width-bw)/2, height - 70), brand_text, font=brand_font, fill=(255,255,255,160))
    except: pass
    img.convert("RGB").save(output_path, "JPEG", quality=95)

def update_weekly_magazine(slug, title, target_url, excerpt, image_file_name):
    now = datetime.datetime.now()
    week_num = now.isocalendar()[1]
    year = now.year
    week_slug = f"edition-{week_num}-{year}"
    discovery_dir = BRIDGE_PAGE_ROOT / "discovery"
    assets_dir = discovery_dir / "assets"
    discovery_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    dest_img_path = assets_dir / f"{slug}.jpg"
    shutil.copy(image_file_name, dest_img_path)
    html_file = discovery_dir / f"{week_slug}.html"
    card_html = f"""
        <!-- POST: {slug} -->
        <div class="card" id="{slug}">
            <div class="card-img-wrapper">
                <img src="assets/{slug}.jpg" alt="{title}" class="card-img">
            </div>
            <div class="card-body">
                <h2 class="card-title">{title}</h2>
                <p class="card-excerpt">{excerpt}</p>
                <a href="{target_url}" class="card-btn">READ FULL RECIPE</a>
            </div>
        </div>
    """
    if not html_file.exists():
        base_html = f"<!DOCTYPE html><html lang='en'><head><meta charset='UTF-8'><title>Weekly Finds</title><style>{WEEKLY_MAGAZINE_CSS}</style></head><body><div class='header'><h1>Weekly Edition</h1><p>Week {week_num}</p></div><div class='gallery-container'><!-- CARDS BEGIN -->{card_html}<!-- CARDS END --></div></body></html>"
        html_file.write_text(base_html, encoding="utf-8")
    else:
        content = html_file.read_text(encoding="utf-8")
        marker = "<!-- CARDS BEGIN -->"
        if marker in content:
            html_file.write_text(content.replace(marker, f"{marker}\n{card_html}"), encoding="utf-8")
    return f"{BRIDGE_PAGE_URL_BASE.strip('/')}/discovery/{week_slug}.html#{slug}"

pin_session = requests.Session()
def pin_request(method, endpoint, **kwargs):
    url = f"https://api.pinterest.com/v5{endpoint}"
    try:
        if method == "GET": return pin_session.get(url, **kwargs)
        return pin_session.post(url, **kwargs)
    except: return None

def publish_pin(image_path, title, description, bridge_url, board_id):
    if MOCK_MODE: return True
    if not PINTEREST_ACCESS_TOKEN: return False
    with open(image_path, "rb") as f: img_b64 = base64.b64encode(f.read()).decode()
    payload = {
        "board_id": board_id, "title": title[:100], "description": description[:500],
        "link": bridge_url,
        "media_source": {"source_type": "image_base64", "content_type": "image/jpeg", "data": img_b64}
    }
    headers = {"Authorization": f"Bearer {PINTEREST_ACCESS_TOKEN}", "Content-Type": "application/json"}
    res = pin_request("POST", "/pins", headers=headers, json=payload, timeout=60)
    return res and res.status_code in (200, 201)

def get_board_id(board_name):
    if not PINTEREST_ACCESS_TOKEN: return None
    headers = {"Authorization": f"Bearer {PINTEREST_ACCESS_TOKEN}"}
    res = pin_request("GET", "/boards", headers=headers)
    if res and res.status_code == 200:
        for b in res.json().get("items", []):
            if b.get("name", "").lower().strip() == board_name.lower().strip():
                return b.get("id")
    return None

def process_new_pin(title, slug, url, description, board_id):
    print(f"--- Pinterest Flow: {title} ---")
    angles = ["A luxury close-up editorial shot, macro", "A beautiful overhead flat-lay photography"]
    success = 0
    for i, angle in enumerate(angles):
        iter_slug = f"{slug}-pin-{i+1}"
        raw_img = f"temp_raw_{iter_slug}.jpg"
        final_img = f"final_pin_{iter_slug}.jpg"
        if generate_image(f"{angle} of {title}", raw_img):
            design_pin(raw_img, title, final_img)
            b_url = update_weekly_magazine(iter_slug, title, url, description, raw_img)
            if publish_pin(final_img, title, description, b_url, board_id): success += 1
            if os.path.exists(raw_img): os.remove(raw_img)
            if os.path.exists(final_img): os.remove(final_img)
    print(f"--- Finished: {success} Pins Published ---")
    return success > 0

def _load_queue():
    queue_path = root_dir / "topic_queue.json"
    if queue_path.exists():
        try:
            with open(queue_path, "r") as f: return json.load(f)
        except: return []
    return []

def _save_queue(queue):
    queue_path = root_dir / "topic_queue.json"
    with open(queue_path, "w") as f: json.dump(queue, f, indent=2)

def run_pin_worker():
    """Pick a topic from queue that needs pins (1:3 ratio) and publish 1 pin."""
    queue = _load_queue()
    # Filter: WP is done and needs more pins
    target = next((t for t in queue if t.get("wp_status") == "done" and t.get("pin_count", 0) < 3), None)
    
    if not target:
        print("No topics in queue waiting for pins. Trying 'pending' topics as fallback...")
        # Optional: as a fallback, we could pick a pending one if it was just published elsewhere
        return

    title = target["topic"]
    slug = target.get("topic", "").lower().replace(" ", "-")
    url = target.get("wp_url")
    description = f"Check out this amazing {title} recipe and guide on el-mordjene.info!"
    pin_index = target.get("pin_count", 0)
    
    print(f"--- PIN WORKER: Processing '{title}' (Pin {pin_index + 1}/3) ---")
    
    # Rotate angles based on which pin we are on
    angles = [
        "A luxury editorial food photography hero shot, professional lighting",
        "A beautiful overhead flat-lay of ingredients and preparation",
        "A close-up macro shot showing texture and delicious details"
    ]
    angle = angles[pin_index % len(angles)]
    
    iter_slug = f"{slug}-pin-{pin_index + 1}"
    raw_img = f"temp_raw_{iter_slug}.jpg"
    final_img = f"final_pin_{iter_slug}.jpg"
    
    # BOARD SELECTION LOGIC (Specialized)
    board_mapping = {
        "dessert": os.getenv("PINTEREST_BOARD_DESSERTS") or "1033083670713095411",
        "dinner": os.getenv("PINTEREST_BOARD_DINNER") or "1033083670713095410",
        "trend": os.getenv("PINTEREST_BOARD_TRENDS") or "1033083670713095408",
        "salad": os.getenv("PINTEREST_BOARD_SALADS") or "1033083670713095409",
        "recipe": os.getenv("PINTEREST_BOARD_RECIPES") or "1033083670713095221"
    }
    
    # Simple keyword matching
    t_lower = title.lower()
    selected_board = board_mapping["recipe"] # Default
    if any(k in t_lower for k in ["cake", "cookie", "dessert", "sweet", "chocolate", "crepe", "bake"]):
        selected_board = board_mapping["dessert"]
    elif any(k in t_lower for k in ["dinner", "wrap", "pasta", "chicken", "meat", "main"]):
        selected_board = board_mapping["dinner"]
    elif any(k in t_lower for k in ["salad", "healthy", "bowl", "chickpea", "vegan"]):
        selected_board = board_mapping["salad"]
    elif any(k in t_lower for k in ["viral", "trending", "trend", "new"]):
        selected_board = board_mapping["trend"]
    
    if generate_image(f"{angle} of {title}", raw_img):
        design_pin(raw_img, title, final_img)
        b_url = update_weekly_magazine(iter_slug, title, url, description, raw_img)
        if publish_pin(final_img, title, description, b_url, selected_board):
            target["pin_count"] = pin_index + 1
            _save_queue(queue)
            print(f"SUCCESS: Pin {pin_index + 1} published for {title}")
        
        if os.path.exists(raw_img): os.remove(raw_img)
        if os.path.exists(final_img): os.remove(final_img)
    else:
        print(f"FAILURE: Could not generate image for {title}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--trend")
    parser.add_argument("--worker", action="store_true", help="Run as a queue worker")
    args = parser.parse_args()
    
    if args.worker:
        run_pin_worker()
    elif args.trend:
        process_new_pin(args.trend, "cli-test", "https://google.com", "CLI Description", os.getenv("PINTEREST_BOARD_ID"))
