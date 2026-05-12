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

VERSION = "1.2.2"
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

def generate_pin_content_with_gemini(topic):
    """Generate high-CTR title and description using Pinterest Annotated Keywords strategy via Raw HTTP."""
    if not GEMINI_API_KEYS: return None
    
    prompt = f"""
    You are a viral Pinterest marketing expert specializing in high-CTR food photography. Your task is to generate high-performance content for a pin about: "{topic}".
    
    1. Identify 3 highly specific 'Pinterest Annotated Keywords' that people search for in the food/recipe niche.
    2. Create a high-CTR 'Click-Gap' Title (max 100 chars). It MUST start with the primary annotated keyword.
    3. Create an SEO-optimized Description (200-400 chars) that naturally weaves in the keywords and hashtags.
    4. Create an urgent, massive 3-6 word CLICK-BAIT hook for the image overlay.
    5. Create a HYPER-REALISTIC Image Prompt (400-600 chars). Focus on Pinterest-viral aesthetics: macro close-ups, vibrant high-contrast colors, and dramatic professional lighting (softbox, rim light, volumetric shadows). Specify professional camera gear (Sony A7R IV, 90mm f/2.8 Macro lens), intricate textures (glistening glazes, crispy caramelized edges, creamy interiors), and an artfully styled composition with scattered garnishes. DO NOT mention people, hands, text, or graphics. The food must be the absolute hero, looking irresistible and professional.
    
    Return ONLY valid JSON:
    {{
      "annotated_keywords": ["keyword1", "keyword2", "keyword3"],
      "title": "Annotated Keyword: The Curiosity Gap Hook",
      "description": "Natural SEO description with keywords...",
      "overlay_text": "HOOK FOR IMAGE",
      "image_prompt": "Masterpiece, hyper-realistic photography prompt here...",
      "hashtags": "#viral #recipe #food..."
    }}
    """
    
    # Model from config
    try:
        from alerts_engine import config as wp_config
        model_name = getattr(wp_config, "GEMINI_MODEL", "gemini-3.1-flash-lite-preview")
    except:
        model_name = "gemini-3.1-flash-lite-preview"

    for key in GEMINI_API_KEYS:
        clean_key = key.strip().strip("'").strip('"')
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={clean_key}"
        try:
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            res = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=30)
            if res.status_code == 200:
                text = res.json()['candidates'][0]['content']['parts'][0]['text']
                text = text.strip().replace("```json", "").replace("```", "")
                return json.loads(text)
            else:
                print(f"   [Gemini] Key fail (status {res.status_code})")
        except Exception as e:
            print(f"   [Gemini] Request error: {e}")
            continue
    return None

BRIDGE_PAGE_ROOT = Path("bridge_page")
BRIDGE_PAGE_URL_BASE = os.getenv("BRIDGE_PAGE_URL", "https://drshahidislam.github.io/Food-Trends-Blog/")
MOCK_MODE = os.getenv("MOCK_MODE", "false").lower() == "true"

WEEKLY_MAGAZINE_CSS = """
    :root { 
        --primary: #8f1f28; 
        --accent: #d87439; 
        --bg: #fffaf5; 
        --text: #2a1910; 
        --glass: rgba(255, 255, 255, 0.9);
        --surface: #ffffff;
    }
    
    body { 
        font-family: 'Outfit', sans-serif; 
        background-color: var(--bg); 
        background-image: 
            radial-gradient(at 0% 0%, hsla(11,100%,94%,1) 0, transparent 50%), 
            radial-gradient(at 50% 0%, hsla(35,100%,92%,1) 0, transparent 50%), 
            radial-gradient(at 100% 0%, hsla(11,100%,94%,1) 0, transparent 50%);
        color: var(--text); 
        margin: 0; 
        padding: 0; 
        scroll-behavior: smooth;
        min-height: 100vh;
    }
    
    .header { 
        padding: 60px 20px; 
        text-align: center; 
        animation: fadeInDown 0.8s ease-out;
    }
    
    .header h1 { 
        font-family: 'Playfair Display', serif;
        margin: 0; 
        font-size: 3.5rem; 
        color: var(--primary); 
        letter-spacing: -1px; 
        text-transform: uppercase; 
        font-weight: 900; 
    }
    
    .header p { 
        color: var(--accent); 
        font-weight: 600;
        letter-spacing: 4px; 
        margin-top: 15px; 
        text-transform: uppercase; 
        font-size: 0.9rem; 
    }
    
    .gallery-container { 
        max-width: 1100px; 
        margin: 0 auto 80px auto; 
        padding: 0 20px; 
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
        gap: 40px; 
    }
    
    .card { 
        background: var(--glass); 
        backdrop-filter: blur(10px);
        border-radius: 24px; 
        overflow: hidden; 
        box-shadow: 0 20px 40px rgba(143, 31, 40, 0.05); 
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); 
        display: flex; 
        flex-direction: column; 
        border: 1px solid rgba(255, 255, 255, 0.5); 
    }
    
    .card:hover { 
        transform: translateY(-12px) scale(1.02); 
        box-shadow: 0 30px 60px rgba(143, 31, 40, 0.15);
    }
    
    .card-img-wrapper { 
        position: relative; 
        width: 100%; 
        padding-top: 130%; 
        overflow: hidden; 
    }
    
    .card-img { 
        position: absolute; 
        top: 0; 
        left: 0; 
        width: 100%; 
        height: 100%; 
        object-fit: cover; 
        transition: transform 0.8s ease; 
    }
    
    .card:hover .card-img { transform: scale(1.1); }
    
    .card-body { 
        padding: 30px; 
        text-align: center; 
        display: flex;
        flex-direction: column;
        flex-grow: 1;
    }
    
    .card-title { 
        font-family: 'Playfair Display', serif;
        font-size: 1.8rem; 
        color: var(--text); 
        margin: 0 0 15px 0; 
        line-height: 1.2; 
        font-weight: 700; 
    }
    
    .card-excerpt { 
        color: #554a44; 
        font-size: 1rem; 
        line-height: 1.6; 
        margin-bottom: 25px; 
        flex-grow: 1;
    }
    
    .card-btn { 
        display: block; 
        background: linear-gradient(135deg, var(--primary) 0%, #b32a35 100%);
        color: white; 
        text-align: center; 
        padding: 18px 30px; 
        text-decoration: none; 
        border-radius: 100px; 
        font-weight: 700; 
        letter-spacing: 1px; 
        transition: all 0.3s ease; 
        text-transform: uppercase; 
        font-size: 0.9rem; 
        box-shadow: 0 10px 20px rgba(143, 31, 40, 0.2); 
    }
    
    .card-btn:hover { 
        background: linear-gradient(135deg, var(--accent) 0%, #e68a4d 100%);
        transform: scale(1.05); 
        box-shadow: 0 15px 30px rgba(216, 116, 57, 0.4); 
    }

    /* Deep Link Focus Styles */
    .hero-focus {
        grid-column: 1 / -1;
        background: var(--glass);
        padding: 40px;
        border-radius: 32px;
        text-align: center;
        margin-bottom: 20px;
        border: 2px solid var(--primary);
        animation: fadeInUp 0.8s ease-out;
    }
    
    .glass-tag {
        display: inline-block;
        background: #fff0f0;
        color: var(--primary);
        padding: 8px 16px;
        border-radius: 50px;
        font-size: 0.75rem;
        font-weight: 800;
        margin-bottom: 20px;
        letter-spacing: 2px;
        text-transform: uppercase;
    }

    .show-all-btn {
        background: none;
        border: 2px solid var(--primary);
        color: var(--primary);
        padding: 12px 25px;
        border-radius: 50px;
        font-weight: 700;
        cursor: pointer;
        transition: all 0.3s;
        margin-top: 20px;
    }

    .show-all-btn:hover {
        background: var(--primary);
        color: white;
    }

    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(30px); }
        to { opacity: 1; transform: translateY(0); }
    }

    @keyframes fadeInDown {
        from { opacity: 0; transform: translateY(-20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .focused-card {
        max-width: 500px;
        margin: 0 auto;
        border: 2px solid var(--primary);
        box-shadow: 0 30px 60px rgba(143, 31, 40, 0.3);
    }
"""

DEEP_LINK_JS = """
    function initDeepLink() {
        const hash = window.location.hash.substring(1);
        if (hash) {
            const targetCard = document.getElementById(hash);
            if (targetCard) {
                // Hide all cards initially
                const allCards = document.querySelectorAll('.card');
                allCards.forEach(c => c.style.display = 'none');
                
                // Show target card with focus
                targetCard.style.display = 'flex';
                targetCard.classList.add('focused-card');
                
                // Add Focus Header
                const container = document.querySelector('.gallery-container');
                const hero = document.createElement('div');
                hero.className = 'hero-focus';
                hero.id = 'focus-header';
                hero.innerHTML = `
                    <div class="glass-tag">EXCLUSIVELY CURATED FOR YOU</div>
                    <h2 style="font-family: 'Playfair Display', serif; margin-bottom: 10px;">Found Your Trend!</h2>
                    <p style="color: #666; margin-bottom: 20px;">We've matched your interest with our latest discovery.</p>
                    <button class="show-all-btn" onclick="showAllTrends()">EXPLORE MORE TRENDS</button>
                `;
                container.prepend(hero);
                
                // Scroll to top to see the focused card
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
        }
    }

    function showAllTrends() {
        document.querySelectorAll('.card').forEach(c => {
            c.style.display = 'flex';
            c.classList.remove('focused-card');
        });
        const header = document.getElementById('focus-header');
        if (header) header.remove();

        window.location.hash = '';
    }

    window.addEventListener('DOMContentLoaded', initDeepLink);
"""

# --- Niche CTA Options ---

CTA_OPTIONS = {
    "viral": ["Click For The Secret ➔", "Tap To See The Trend", "Get The Full Guide Now", "Find Out How Here"],
    "healthy": ["Get The Healthy Recipe ➔", "Eat Better Today", "Clean Eating Guide", "Healthy & Delicious"],
    "dinner": ["What's For Dinner? ➔", "Easy Weeknight Meal", "Family Favorite Recipe", "Cook This Tonight"],
    "dessert": ["Sweet Tooth Heaven ➔", "Decadent & Delicious", "The Best Dessert Ever", "Try This Treat"],
    "recipe": ["Click For Full Recipe ➔", "Step-By-Step Guide", "Master This Dish", "The Only Recipe You Need"]
}

# --- Multi-Backend Generation ---

def _try_huggingface(prompt, output_path):
    if not hf_keys: return False
    # Use a highly realistic static photography string
    full_prompt = f"{prompt}, high-end food photography, award-winning, ultra-realistic, 8k resolution, shot on 100mm macro lens, f/2.8, cinematic soft lighting, detailed textures, professional food styling, bokeh background, 768x1024"
    
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
    return False

def _try_kolors(prompt, output_path):
    api_key = os.getenv("SILICONFLOW_API_KEY")
    if not api_key: return False
    try:
        print(f"DEBUG: Trying Kolors Fallback...", flush=True)
        enhanced_prompt = f"{prompt}, professional food photography, commercial quality, hyper-realistic, natural lighting, 1024x1024"
            
        payload = {
            "model": SILICONFLOW_MODEL,
            "prompt": enhanced_prompt,
            "image_size": "1024x1024"
        }
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        response = requests.post(SILICONFLOW_API_URL, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            resp_json = response.json()
            img_url = None
            if "images" in resp_json and resp_json["images"]:
                img_url = resp_json["images"][0].get("url")
            elif "data" in resp_json and resp_json["data"]:
                img_url = resp_json["data"][0].get("url")
            
            if img_url:
                img_data = requests.get(img_url).content
                with open(output_path, "wb") as f: f.write(img_data)
                return True
    except Exception as e:
        print(f"DEBUG: Kolors fallback failed: {e}")
    return False

def _try_pollinations(prompt, output_path):
    try:
        print(f"DEBUG: Trying Pollinations Last Resort...", flush=True)
        encoded = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=768&height=1024&model=flux&nologo=true&seed={random.randint(1,999999)}"
        res = requests.get(url, timeout=30)
        if res.status_code == 200:
            with open(output_path, "wb") as f: f.write(res.content)
            return True
    except Exception as e:
        print(f"DEBUG: Pollinations failed: {e}")
    return False

def generate_image_master(prompt, output_path):
    if _try_huggingface(prompt, output_path): return True
    if _try_kolors(prompt, output_path): return True
    if _try_pollinations(prompt, output_path): return True
    return False

# --- Premium Design Engine ---

def design_pin_premium(image_path, title, output_path, board_type="recipe"):
    img = Image.open(image_path).convert("RGBA")
    width, height = img.size
    
    # Selection of Layout
    layouts = ['bottom_fade', 'center_box', 'top_fade', 'solid_block']
    layout_style = random.choice(layouts)
    print(f"   [Layout] Selected layout style: {layout_style}")
    
    # Font setup
    font_size = int(width * 0.08)
    fonts_dir = root_dir / "fonts"
    
    anton_path = str(fonts_dir / "Anton-Regular.ttf")
    montserrat_path = str(fonts_dir / "Montserrat-Bold.ttf")
    
    primary_font_path = anton_path if layout_style == 'center_box' else montserrat_path
    
    font = None
    try:
        if os.path.exists(primary_font_path):
            font = ImageFont.truetype(primary_font_path, font_size)
        else:
            # Fallback to system fonts
            fallbacks = ["C:/Windows/Fonts/arialbd.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", "arialbd.ttf"]
            for f_path in fallbacks:
                if os.path.exists(f_path):
                    font = ImageFont.truetype(f_path, font_size)
                    break
    except: pass
    
    if not font: font = ImageFont.load_default()
    
    # CTA Setup
    ctas = CTA_OPTIONS.get(board_type, CTA_OPTIONS["recipe"])
    cta_text = random.choice(ctas)
    cta_font = None
    try:
        if os.path.exists(montserrat_path):
            cta_font = ImageFont.truetype(montserrat_path, int(width * 0.045))
    except: pass
    if not cta_font: cta_font = font

    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    
    wrapped_lines = textwrap.wrap(title, width=15 if layout_style == 'center_box' else 20)
    line_h = font_size * 1.2
    total_text_h = len(wrapped_lines) * line_h
    
    margin = int(width * 0.08)
    
    if layout_style == 'bottom_fade':
        grad_h = int(height * 0.45)
        for y in range(height - grad_h, height):
            progress = (y - (height - grad_h)) / grad_h
            alpha = int(220 * (progress ** 1.5))
            draw_overlay.rectangle([(0, y), (width, y+1)], fill=(0, 0, 0, alpha))
        text_y = height - total_text_h - int(height * 0.15)
        
    elif layout_style == 'top_fade':
        grad_h = int(height * 0.40)
        for y in range(0, grad_h):
            progress = 1.0 - (y / grad_h)
            alpha = int(220 * (progress ** 1.5))
            draw_overlay.rectangle([(0, y), (width, y+1)], fill=(0, 0, 0, alpha))
        text_y = int(height * 0.10)
        
    elif layout_style == 'center_box':
        box_padding = int(height * 0.05)
        box_h = total_text_h + (box_padding * 2) + int(height * 0.05)
        box_y = (height - box_h) // 2
        draw_overlay.rectangle([(margin//2, box_y), (width - margin//2, box_y + box_h)], fill=(0, 0, 0, 180))
        text_y = box_y + box_padding
        
    elif layout_style == 'solid_block':
        block_h = total_text_h + int(height * 0.18)
        block_y = height - block_h
        draw_overlay.rectangle([(0, block_y), (width, height)], fill=(30, 20, 15, 255))
        text_y = block_y + int(height * 0.04)

    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)
    
    for line in wrapped_lines:
        w = draw.textlength(line, font=font)
        draw.text(((width-w)/2, text_y), line, font=font, fill=(255,255,255,255))
        text_y += line_h
        
    # Draw CTA
    if cta_text:
        cw = draw.textlength(cta_text, font=cta_font)
        cx = (width - cw) // 2
        cy = text_y + int(height * 0.02) if layout_style != 'bottom_fade' else text_y
        if layout_style == 'bottom_fade': cy = height - int(height * 0.08)
        
        draw.text((cx, cy), cta_text, font=cta_font, fill=(255, 255, 255, 200))

    img.convert("RGB").save(output_path, "JPEG", quality=95)



def update_weekly_magazine(slug, title, target_url, excerpt, image_file_name):
    import re
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
        </div>"""

    if not html_file.exists():
        base_html = f"""<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset='UTF-8'>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>El Mordjene Weekly Finds - Week {week_num}</title>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>{WEEKLY_MAGAZINE_CSS}</style>
</head>
<body>
    <div class='header'>
        <h1>Weekly Edition</h1>
        <p>Curated Top Trends & Beautiful Recipes • Week {week_num}</p>
    </div>
    <div class='gallery-container'>
        <!-- CARDS BEGIN -->
        {card_html}
        <!-- CARDS END -->
    </div>
    <script>{DEEP_LINK_JS}</script>
</body>
</html>"""
        html_file.write_text(base_html, encoding="utf-8")
    else:
        content = html_file.read_text(encoding="utf-8")
        
        # Prevent Duplicates: If card with same slug exists, replace it
        pattern = rf"<!-- POST: {re.escape(slug)} -->.*?</div>\s*</div>"
        if re.search(pattern, content, re.DOTALL):
            print(f"   [Gallery] Updating existing card: {slug}")
            content = re.sub(pattern, card_html.strip(), content, flags=re.DOTALL)
            html_file.write_text(content, encoding="utf-8")
        else:
            marker = "<!-- CARDS BEGIN -->"
            if marker in content:
                print(f"   [Gallery] Appending new card: {slug}")
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
    angles = ["A luxury editorial food photography hero shot, professional lighting", "A beautiful overhead flat-lay photography"]
    success = 0
    for i, angle in enumerate(angles):
        iter_slug = f"{slug}-pin-{i+1}"
        raw_img = f"temp_raw_{iter_slug}.jpg"
        final_img = f"final_pin_{iter_slug}.jpg"
        
        # Content Gen (Keep Gemini for Title/Desc but NOT for prompt expansion if it's unstable)
        gemini_data = generate_pin_content_with_gemini(title)
        if gemini_data:
            p_title = gemini_data.get("title", title)
            p_desc = gemini_data.get("description", description) + f" {gemini_data.get('hashtags', '')}"
            overlay_text = gemini_data.get("overlay_text", title)
        else:
            p_title, p_desc, overlay_text = title, description, title

        image_prompt = gemini_data.get("image_prompt") if gemini_data else None
        if not image_prompt:
            image_prompt = f"{angle} of {title}"

        if generate_image_master(image_prompt, raw_img):
            design_pin_premium(raw_img, overlay_text, final_img)
            b_url = update_weekly_magazine(iter_slug, p_title, url, p_desc, raw_img)
            if publish_pin(final_img, p_title, p_desc, b_url, board_id): success += 1
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
        print("No topics in queue waiting for pins.")
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
    
    # --- GENERATE PREMIUM CONTENT ---
    gemini_data = generate_pin_content_with_gemini(title)
    if gemini_data:
        p_title = gemini_data.get("title", title)
        p_desc = gemini_data.get("description", description) + f" {gemini_data.get('hashtags', '')}"
        overlay_text = gemini_data.get("overlay_text", title)
    else:
        p_title, p_desc, overlay_text = title, description, title

    # BOARD SELECTION LOGIC (Specialized - FoodTrendsBlog)
    board_mapping = {
        "dessert": os.getenv("PINTEREST_BOARD_DESSERTS") or "976859044115152346",
        "dinner": os.getenv("PINTEREST_BOARD_DINNER") or "976859044115152345",
        "trend": os.getenv("PINTEREST_BOARD_TRENDS") or "976859044115152343",
        "salad": os.getenv("PINTEREST_BOARD_SALADS") or "976859044115152344",
        "recipe": os.getenv("PINTEREST_BOARD_RECIPES") or "976859044115152343"
    }
    
    # Simple keyword matching
    t_lower = title.lower()
    board_key = "recipe"
    if any(k in t_lower for k in ["cake", "cookie", "dessert", "sweet", "chocolate", "crepe", "bake"]):
        board_key = "dessert"
    elif any(k in t_lower for k in ["dinner", "wrap", "pasta", "chicken", "meat", "main"]):
        board_key = "dinner"
    elif any(k in t_lower for k in ["salad", "healthy", "bowl", "chickpea", "vegan"]):
        board_key = "salad"
    elif any(k in t_lower for k in ["viral", "trending", "trend", "new"]):
        board_key = "trend"
    
    selected_board = board_mapping[board_key]
    
    image_prompt = gemini_data.get("image_prompt") if gemini_data else None
    if not image_prompt:
        image_prompt = f"{angle} of {title}"

    if generate_image_master(image_prompt, raw_img):
        design_pin_premium(raw_img, overlay_text, final_img, board_type=board_key)
        b_url = update_weekly_magazine(iter_slug, p_title, url, p_desc, raw_img)
        if publish_pin(final_img, p_title, p_desc, b_url, selected_board):
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
