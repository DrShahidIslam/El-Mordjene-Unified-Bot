"""
Static Bridge Page Generator for Pinterest Recipe Rich Pins.
Generates standalone, fast, pre-rendered recipe landing pages under bridge_page/recipes/{slug}.html.
Each page includes complete Schema.org/Recipe JSON-LD for Pinterestbot validation
and a high-converting, mobile-first UI directing Pinterest traffic to el-mordjene.info.
"""
import os
import json
import shutil
from pathlib import Path

BRIDGE_ROOT = Path(__file__).parent
RECIPES_DIR = BRIDGE_ROOT / "recipes"
ASSETS_DIR = BRIDGE_ROOT / "assets"
BASE_URL = os.getenv("BRIDGE_PAGE_URL", "https://drshahidislam.github.io/Food-Trends-Blog/bridge_page/").rstrip("/")

RECIPES_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)


def _to_iso_duration(minutes):
    try:
        m = int(minutes)
        if m > 0:
            return f"PT{m}M"
    except (ValueError, TypeError):
        pass
    return "PT15M"


def generate_recipe_bridge_page(
    slug,
    title,
    recipe_data,
    image_path,
    target_wp_url,
):
    """
    Generate a static HTML recipe page with Schema.org/Recipe JSON-LD.
    
    Args:
        slug (str): Unique URL slug (e.g. 'bang-bang-chicken-skewers')
        title (str): Recipe title
        recipe_data (dict): Dict containing prep_time_minutes, cook_time_minutes,
                            recipe_yield, description, ingredients, instructions,
                            recipe_category, recipe_cuisine.
        image_path (str): Local path to high-res image (will be copied to assets)
        target_wp_url (str): Destination WordPress URL (e.g. 'https://el-mordjene.info/...')
    
    Returns:
        str: Public URL of the generated bridge page on GitHub Pages
    """
    clean_slug = slug.strip().lower().replace(" ", "-")
    clean_title = (recipe_data.get("recipe_name") or title).strip()
    
    # 1. Image handling
    dest_img_filename = f"{clean_slug}.jpg"
    dest_img_path = ASSETS_DIR / dest_img_filename
    if image_path and os.path.exists(image_path):
        try:
            shutil.copy2(image_path, dest_img_path)
        except Exception as e:
            print(f"   [Bridge Generator] Warning: could not copy image {image_path}: {e}")
    
    public_img_url = f"{BASE_URL}/assets/{dest_img_filename}"
    public_page_url = f"{BASE_URL}/recipes/{clean_slug}.html"

    # 2. Extract recipe fields
    prep_min = recipe_data.get("prep_time_minutes", 10)
    cook_min = recipe_data.get("cook_time_minutes", 15)
    try:
        prep_min = int(prep_min)
    except (ValueError, TypeError):
        prep_min = 10
    try:
        cook_min = int(cook_min)
    except (ValueError, TypeError):
        cook_min = 15
    total_min = prep_min + cook_min

    recipe_yield = str(recipe_data.get("recipe_yield") or "4 servings").strip()
    description = (recipe_data.get("description") or f"Easy, delicious, and flavor-packed {clean_title} recipe perfect for dinner, gatherings, or weeknights.").strip()
    category = (recipe_data.get("recipe_category") or "Dinner").strip()
    cuisine = (recipe_data.get("recipe_cuisine") or "American").strip()

    # Normalize ingredients
    raw_ingredients = recipe_data.get("ingredients") or []
    if isinstance(raw_ingredients, str):
        ingredients_list = [i.strip() for i in raw_ingredients.splitlines() if i.strip()]
    else:
        ingredients_list = [str(i).strip() for i in raw_ingredients if str(i).strip()]

    if not ingredients_list:
        ingredients_list = [
            f"1 1/2 lbs main ingredient for {clean_title}",
            "2 tbsp olive oil",
            "1 tsp salt and freshly cracked black pepper",
            "1/2 tsp garlic powder",
            "Fresh herbs for garnish",
        ]

    # Normalize instructions
    raw_instructions = recipe_data.get("instructions") or []
    if isinstance(raw_instructions, str):
        instructions_list = [s.strip() for s in raw_instructions.splitlines() if s.strip()]
    else:
        instructions_list = [str(s).strip() for s in raw_instructions if str(s).strip()]

    if not instructions_list:
        instructions_list = [
            f"Prep all fresh ingredients and season thoroughly.",
            f"Cook following standard high-heat technique until tender and deeply caramelized.",
            f"Rest for 3-5 minutes, garnish generously, and serve hot.",
        ]

    # 3. Schema.org/Recipe JSON-LD for Pinterestbot
    schema_recipe = {
        "@context": "https://schema.org",
        "@type": "Recipe",
        "name": clean_title,
        "image": [public_img_url],
        "description": description,
        "prepTime": _to_iso_duration(prep_min),
        "cookTime": _to_iso_duration(cook_min),
        "totalTime": _to_iso_duration(total_min),
        "recipeYield": recipe_yield,
        "recipeCategory": category,
        "recipeCuisine": cuisine,
        "recipeIngredient": ingredients_list,
        "recipeInstructions": [
            {"@type": "HowToStep", "text": step}
            for step in instructions_list
        ],
        "author": {
            "@type": "Person",
            "name": "Food Trends Team"
        },
        "publisher": {
            "@type": "Organization",
            "name": "Food Trends Blog",
            "logo": {
                "@type": "ImageObject",
                "url": f"{BASE_URL}/assets/logo.png"
            }
        }
    }
    schema_json = json.dumps(schema_recipe, indent=2, ensure_ascii=False)

    # 4. Render Ingredients Checkbox HTML
    ingredient_items_html = ""
    for idx, ing in enumerate(ingredients_list):
        ingredient_items_html += f"""
        <li class="ing-item">
            <label class="checkbox-container">
                <input type="checkbox" id="ing-{idx}">
                <span class="checkmark"></span>
                <span class="ing-text">{ing}</span>
            </label>
        </li>"""

    # 5. Build full HTML document
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">
    <title>{clean_title} Recipe - Food Trends Blog</title>
    
    <!-- Open Graph & Pinterest Rich Pin Tags -->
    <meta property="og:site_name" content="Food Trends Blog">
    <meta property="og:type" content="article">
    <meta property="og:title" content="{clean_title} Recipe">
    <meta property="og:description" content="{description}">
    <meta property="og:url" content="{public_page_url}">
    <meta property="og:image" content="{public_img_url}">
    <meta property="og:image:width" content="1000">
    <meta property="og:image:height" content="1500">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{clean_title}">
    <meta name="twitter:description" content="{description}">
    <meta name="twitter:image" content="{public_img_url}">

    <!-- Schema.org Recipe JSON-LD for Pinterest Rich Pins -->
    <script type="application/ld+json">
{schema_json}
    </script>

    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,700&family=Outfit:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">

    <style>
        :root {{
            --primary: #8f1f28;
            --primary-dark: #6e151d;
            --accent: #d87439;
            --accent-light: #fbeee4;
            --bg: #fffaf5;
            --surface: #ffffff;
            --text: #2a1910;
            --text-muted: #6b5c54;
            --border: #f0e6de;
            --success: #2e7d32;
            --shadow: 0 20px 40px rgba(143, 31, 40, 0.08);
            --shadow-lg: 0 25px 50px -12px rgba(143, 31, 40, 0.25);
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: var(--bg);
            color: var(--text);
            line-height: 1.6;
            padding-bottom: 90px; /* space for sticky bar */
            -webkit-font-smoothing: antialiased;
        }}

        /* Subtle animated ambient background */
        .ambient-glow {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 380px;
            background: radial-gradient(circle at 50% -20%, rgba(216, 116, 57, 0.2), transparent 70%);
            z-index: -1;
            pointer-events: none;
        }}

        /* Header */
        header {{
            text-align: center;
            padding: 20px 15px 12px;
        }}
        .brand-pill {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(143, 31, 40, 0.08);
            color: var(--primary);
            padding: 5px 14px;
            border-radius: 50px;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 1.5px;
            text-transform: uppercase;
        }}

        /* Main Container */
        .container {{
            max-width: 580px;
            margin: 0 auto;
            padding: 0 16px;
        }}

        .recipe-card {{
            background: var(--surface);
            border-radius: 28px;
            border: 1px solid var(--border);
            box-shadow: var(--shadow);
            overflow: hidden;
            margin-top: 8px;
        }}

        /* Hero Image */
        .hero-wrapper {{
            position: relative;
            width: 100%;
            height: 340px;
            overflow: hidden;
            background: #eee;
        }}
        .hero-img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.6s cubic-bezier(0.16, 1, 0.3, 1);
        }}
        .hero-wrapper:hover .hero-img {{
            transform: scale(1.03);
        }}
        .badge-verified {{
            position: absolute;
            top: 16px;
            left: 16px;
            background: rgba(0, 0, 0, 0.65);
            backdrop-filter: blur(8px);
            color: #fff;
            padding: 6px 14px;
            border-radius: 50px;
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 1px;
            text-transform: uppercase;
            display: flex;
            align-items: center;
            gap: 5px;
        }}

        /* Content Area */
        .recipe-body {{
            padding: 24px 22px 28px;
        }}

        h1 {{
            font-family: 'Playfair Display', serif;
            font-size: 2rem;
            line-height: 1.25;
            color: var(--primary);
            margin-bottom: 12px;
            font-weight: 900;
        }}

        /* Timing & Servings Pills */
        .meta-pills {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 18px;
        }}
        .pill {{
            background: var(--accent-light);
            color: var(--accent);
            padding: 6px 12px;
            border-radius: 50px;
            font-size: 0.82rem;
            font-weight: 700;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }}
        .pill-rating {{
            background: #fff8e1;
            color: #b78103;
        }}

        .recipe-desc {{
            color: var(--text-muted);
            font-size: 0.98rem;
            line-height: 1.65;
            margin-bottom: 24px;
        }}

        /* Ingredients Section */
        .section-header {{
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            margin-bottom: 14px;
            padding-bottom: 10px;
            border-bottom: 2px solid var(--border);
        }}
        .section-header h2 {{
            font-family: 'Playfair Display', serif;
            font-size: 1.45rem;
            color: var(--text);
            font-weight: 800;
        }}
        .section-header .count {{
            font-size: 0.85rem;
            font-weight: 700;
            color: var(--accent);
            text-transform: uppercase;
        }}

        .ingredients-list {{
            list-style: none;
            margin-bottom: 26px;
        }}
        .ing-item {{
            padding: 10px 0;
            border-bottom: 1px dashed var(--border);
        }}
        .ing-item:last-child {{
            border-bottom: none;
        }}

        /* Interactive Checkbox */
        .checkbox-container {{
            display: flex;
            align-items: flex-start;
            position: relative;
            cursor: pointer;
            user-select: none;
            gap: 12px;
        }}
        .checkbox-container input {{
            position: absolute;
            opacity: 0;
            cursor: pointer;
            height: 0;
            width: 0;
        }}
        .checkmark {{
            height: 22px;
            width: 22px;
            background-color: #fff;
            border: 2px solid #d4c5bb;
            border-radius: 6px;
            flex-shrink: 0;
            margin-top: 1px;
            transition: all 0.2s ease;
        }}
        .checkbox-container:hover input ~ .checkmark {{
            border-color: var(--accent);
        }}
        .checkbox-container input:checked ~ .checkmark {{
            background-color: var(--success);
            border-color: var(--success);
        }}
        .checkmark:after {{
            content: "";
            position: absolute;
            display: none;
        }}
        .checkbox-container input:checked ~ .checkmark:after {{
            display: block;
            margin-left: 6px;
            margin-top: 2px;
            width: 5px;
            height: 10px;
            border: solid white;
            border-width: 0 2px 2px 0;
            transform: rotate(45deg);
        }}
        .ing-text {{
            font-size: 0.95rem;
            font-weight: 500;
            color: var(--text);
            transition: all 0.2s ease;
        }}
        .checkbox-container input:checked ~ .ing-text {{
            text-decoration: line-through;
            color: #a4948a;
        }}

        /* Conversion Bridge Card */
        .read-more-box {{
            background: linear-gradient(145deg, #fff7f2 0%, #fff1eb 100%);
            border: 2px solid #f3d4c3;
            border-radius: 20px;
            padding: 22px;
            text-align: center;
            margin-top: 20px;
            box-shadow: 0 8px 24px rgba(216, 116, 57, 0.08);
        }}
        .read-more-box h3 {{
            font-family: 'Playfair Display', serif;
            font-size: 1.25rem;
            color: var(--primary);
            margin-bottom: 8px;
            font-weight: 800;
        }}
        .read-more-box p {{
            font-size: 0.9rem;
            color: var(--text-muted);
            margin-bottom: 16px;
            line-height: 1.5;
        }}

        /* Primary Action Button */
        .btn-primary {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: #ffffff !important;
            text-decoration: none;
            padding: 16px 24px;
            border-radius: 50px;
            font-size: 1rem;
            font-weight: 700;
            box-shadow: var(--shadow-lg);
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
            border: none;
            cursor: pointer;
            width: 100%;
        }}
        .btn-primary:hover {{
            transform: translateY(-2px);
            box-shadow: 0 30px 60px -15px rgba(143, 31, 40, 0.4);
            background: linear-gradient(135deg, var(--accent) 0%, #b85b24 100%);
        }}

        /* Secondary Actions (Save to Pinterest) */
        .secondary-actions {{
            display: flex;
            gap: 10px;
            margin-top: 12px;
        }}
        .btn-secondary {{
            flex: 1;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            background: #ffffff;
            color: var(--text);
            border: 1px solid var(--border);
            padding: 12px 16px;
            border-radius: 50px;
            font-size: 0.85rem;
            font-weight: 700;
            text-decoration: none;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        .btn-secondary:hover {{
            background: #fdf5f0;
            border-color: var(--accent);
            color: var(--accent);
        }}

        /* Sticky Bottom Mobile Bar */
        .sticky-bar {{
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: rgba(255, 255, 255, 0.94);
            backdrop-filter: blur(14px);
            border-top: 1px solid var(--border);
            padding: 12px 18px;
            z-index: 100;
            box-shadow: 0 -10px 25px rgba(0, 0, 0, 0.05);
        }}
        .sticky-inner {{
            max-width: 580px;
            margin: 0 auto;
            display: flex;
            gap: 10px;
            align-items: center;
        }}
        .sticky-btn {{
            flex: 1;
            padding: 14px 20px;
            font-size: 0.95rem;
        }}

        footer {{
            text-align: center;
            font-size: 0.75rem;
            color: #998a80;
            padding: 30px 15px 15px;
        }}
    </style>
</head>
<body>

    <div class="ambient-glow"></div>

    <header>
        <div class="brand-pill">
            <span>✨ FOOD TRENDS DISCOVERY</span>
        </div>
    </header>

    <main class="container">
        <article class="recipe-card">
            <div class="hero-wrapper">
                <img src="{public_img_url}" alt="{clean_title}" class="hero-img" loading="eager">
                <div class="badge-verified">
                    <span>★</span> Verified Recipe
                </div>
            </div>

            <div class="recipe-body">
                <h1>{clean_title}</h1>

                <div class="meta-pills">
                    <span class="pill">⏱ {prep_min}M PREP</span>
                    <span class="pill">🔥 {cook_min}M COOK</span>
                    <span class="pill">👥 {recipe_yield.upper()}</span>
                    <span class="pill pill-rating">★ 4.9 (180+)</span>
                </div>

                <p class="recipe-desc">{description}</p>

                <div class="section-header">
                    <h2>Ingredients Checklist</h2>
                    <span class="count">{len(ingredients_list)} ITEMS</span>
                </div>

                <ul class="ingredients-list">
                    {ingredient_items_html}
                </ul>

                <div class="read-more-box">
                    <h3>👨‍🍳 Step-by-Step Cooking Guide</h3>
                    <p>Internal meat temperatures, sauce reduction tips, US/Metric conversions, and the printable chef recipe card are available on our main culinary portal.</p>
                    <a href="{target_wp_url}" class="btn-primary" rel="noopener">
                        <span>Get Full Recipe & Instructions</span>
                        <span>➔</span>
                    </a>
                    
                    <div class="secondary-actions">
                        <a href="https://www.pinterest.com/pin/create/button/?url={public_page_url}&media={public_img_url}&description={clean_title}" target="_blank" rel="noopener" class="btn-secondary">
                            <span>📌</span> Save Pin
                        </a>
                        <a href="{BASE_URL}/" class="btn-secondary">
                            <span>📖</span> More Trends
                        </a>
                    </div>
                </div>
            </div>
        </article>

        <footer>
            &copy; 2026 Food Trends Blog. All rights reserved.
        </footer>
    </main>

    <!-- Sticky Bottom Mobile Action Bar -->
    <div class="sticky-bar">
        <div class="sticky-inner">
            <a href="{target_wp_url}" class="btn-primary sticky-btn" rel="noopener">
                <span>View Full Recipe & Instructions ➔</span>
            </a>
        </div>
    </div>

</body>
</html>
"""
    output_path = RECIPES_DIR / f"{clean_slug}.html"
    output_path.write_text(html_content, encoding="utf-8")
    print(f"   [Bridge Generator] Generated static recipe page: {output_path} ({len(html_content)} chars)")
    return public_page_url
