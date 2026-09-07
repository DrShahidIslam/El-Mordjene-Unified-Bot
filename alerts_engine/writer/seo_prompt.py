"""
SEO Prompt Template - Master prompt for Gemini article generation.
Tailored for el-mordjene.info: food, recipes, chocolate, desserts, spreads.
"""
import hashlib

import json
import os

# Base directory
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PUBLISHED_POSTS_PATH = os.path.join(BASE_DIR, "published_posts.json")

def _load_internal_links():
    try:
        with open(PUBLISHED_POSTS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

INTERNAL_LINKS = _load_internal_links()

def _pick_layout_variant(topic_title, matched_keyword):
    variants = [
        {
            "name": "Explainer and Practical Steps",
            "outline": [
                "Start with the key question users ask now",
                "Explain what changed and why the topic matters",
                "Give practical steps readers can follow",
                "Add common mistakes and fixes",
                "Close with a concise FAQ section",
            ],
        },
        {
            "name": "Myth vs Fact and Action Plan",
            "outline": [
                "Summarize what is confirmed vs uncertain",
                "Add a myth-vs-fact evidence section",
                "Provide a do-this-next checklist",
                "Cover substitutions and alternatives",
                "Close with transactional FAQ questions",
            ],
        },
        {
            "name": "Chooser Guide",
            "outline": [
                "Define user intent and decision criteria",
                "Compare options by quality, price, and availability",
                "Highlight warning signs and authenticity checks",
                "Explain who should choose which option",
                "Close with FAQ answers to buying concerns",
            ],
        },
        {
            "name": "Trend Analysis and Regional Context",
            "outline": [
                "Describe why this trend accelerated",
                "Compare US, EU, FR, or DZ angles when relevant",
                "Explain social media influence",
                "Add likely 30-90 day outlook",
                "Close with short direct FAQ answers",
            ],
        },
    ]

    seed = f"{topic_title}|{matched_keyword}".strip().lower()
    idx = int(hashlib.sha256(seed.encode("utf-8")).hexdigest(), 16) % len(variants)
    return variants[idx]


def _intent_guidance(intent):
    intent_map = {
        "recipe": "Write a real recipe with clear ingredients, steps, timings, serving yield, and practical tips. Keep claims concrete.",
        "news": "Focus on what changed, why it matters now, and cite source-backed facts with caution language.",
        "buyer": "Focus on availability, authenticity checks, pricing caveats, and decision criteria.",
        "explainer": "Focus on definitions, context, misconceptions, and concise answers.",
        "refresh": "Treat this as an update to an existing page. Emphasize what changed and refresh stale sections.",
        "trend": "Focus on evidence of momentum, drivers of growth, and likely short-term direction.",
    }
    return intent_map.get((intent or "").strip().lower(), intent_map["explainer"])


def build_article_prompt(topic_title, source_texts, matched_keyword="", intent="general", min_words=1800):
    """
    Build the master SEO prompt for Gemini article generation with high-retention structure.
    """
    is_recipe = (intent or "").strip().lower() == "recipe"
    sources_block = ""
    for i, src in enumerate(source_texts[:5], 1):
        sources_block += f"""
--- SOURCE {i} ({src.get('source_domain', 'Unknown')}) ---
{src.get('text', '')[:2000]}
"""

    primary_keyword = (matched_keyword or topic_title).strip()
    keyword_pool = []
    for candidate in [primary_keyword, topic_title]:
        if candidate and candidate not in keyword_pool:
            keyword_pool.append(candidate)
    for src in source_texts[:5]:
        for candidate in [src.get("title", ""), src.get("source_domain", "")]:
            candidate = (candidate or "").strip()
            if candidate and candidate not in keyword_pool:
                keyword_pool.append(candidate)
    secondary_keywords = ", ".join(keyword_pool[1:4]) or "Use close topical variations only when naturally supported."
    supporting_keywords = ", ".join(keyword_pool[4:8]) or "Use supporting entities, ingredients, brands, locations, and use-cases only when source-backed."

    # Select most relevant internal links to avoid LLM confusion/hallucination
    import re
    all_links = list(_load_internal_links().values())
    query_terms = set(re.findall(r'\b[a-z]{3,}\b', (topic_title + " " + matched_keyword).lower()))
    
    scored_links = []
    for info in all_links:
        url_lower = info.get("url", "").lower()
        anchor_lower = info.get("anchor", "").lower()
        
        # Avoid linking to the post itself
        post_slug = re.sub(r'[^a-z0-9]+', '-', topic_title.lower()).strip('-')
        if post_slug and post_slug in url_lower:
            continue
        # Also skip main home page URL from suggestions to focus on deep articles
        if url_lower.rstrip("/") == "https://el-mordjene.info":
            continue
            
        score = 0
        for term in query_terms:
            if term in url_lower:
                score += 3  # High weight for URL slug match
            if term in anchor_lower:
                score += 2  # Medium weight for anchor text match
                
        scored_links.append((score, info))
        
    scored_links.sort(key=lambda x: x[0], reverse=True)
    top_links = [item[1] for item in scored_links[:8]]
    
    if len(top_links) < 3:
        existing_urls = {info["url"] for info in top_links}
        for score, info in scored_links:
            if info["url"] not in existing_urls:
                top_links.append(info)
                if len(top_links) >= 8:
                    break
                    
    links_suggestion = "\n".join(
        f"  - [{info['anchor']}]({info['url']})"
        for info in top_links
    )

    variant = _pick_layout_variant(topic_title, matched_keyword)
    outline = "\n".join(f"  - {item}" for item in variant["outline"])
    if is_recipe:
        variant = {
            "name": "Comprehensive High-Retention Recipe Authority Guide",
            "outline": [
                "1. Inspiring Hook & 'Why You'll Love This Recipe' (Audience identity, flavor profile, texture overview)",
                "2. Recipe Snapshot Box & Direct Answer (Yield, prep/cook/chill times, difficulty, calorie estimate)",
                "3. Key Ingredients Deep-Dive & Smart Substitutions (Why each ingredient matters + gluten-free, dairy-free, vegan swaps)",
                "4. Dual Measurements Table (US Customary Cups vs. Metric Grams/ml comparison table)",
                "5. Step-by-Step Culinary Walkthrough (Granular stages: Prep -> Mixing -> Cooking/Baking -> Cooling with sensory & browning indicators)",
                "6. Pro Chef Secrets & Critical Mistakes to Avoid (3-5 highlighted callout boxes for common pitfalls)",
                "7. 4-6 Creative Flavor Variations, Mix-Ins & Dietary Twists (Seasonal, spicy, low-carb, extra decadent)",
                "8. Make-Ahead, Storage, Freezing, Thawing & Reheating Protocols (Shelf life, freezer instructions, optimal reheat methods)",
                "9. What to Serve With This / Menu Builder (Side dishes, sauces, and drink pairings with internal links)",
                "10. Chef's Troubleshooting Guide & Comprehensive FAQs (5-7 questions formatted with FAQPage Schema)",
                "11. Interactive Printable Recipe Card with Checkbox Ingredients & Pinterest Save Banner",
            ],
        }
        outline = "\n".join(f"  - {item}" for item in variant["outline"])

    prompt = f"""You are a world-class culinary authority and expert food journalist for el-mordjene.info.
Write one exhaustive, publish-ready, high-retention article (Target: {min_words} – 2,500+ words). Pinterest and search readers should stay engaged for 3-5+ minutes reading this comprehensive guide.

TASK:
- TRENDING TOPIC: {topic_title}
- PRIMARY KEYWORD: {matched_keyword or topic_title}
- SECONDARY KEYWORDS: {secondary_keywords}
- SUPPORTING KEYWORDS / ENTITIES: {supporting_keywords}
- TARGET LENGTH: At least {min_words} words (aim for 1,800 – 2,500+ words). Provide exhaustive culinary mechanics, food chemistry, techniques, and practical troubleshooting to reach this length naturally without filler.

SOURCE MATERIAL (use these facts as foundation):
{sources_block}

NON-NEGOTIABLE CONTENT & RETENTION RULES:
1. Do not fabricate facts, legal claims, or unsafe food practices.
2. Use one language for the entire article: English OR French, never mixed.
3. Keep primary keyword density under 0.8 percent in paragraph text.
4. No emojis in body copy paragraphs (styled badges and cards can use clean accents).
5. Do not output WordPress block comments like <!-- wp:... -->.
6. Write original synthesis for readers with rich culinary prose, not stitched source passages.
7. Do not talk about search popularity, Google Trends, or "people are searching for" unless specifically relevant.
8. Structure for maximum visual engagement: Use responsive tables, styled tip callout boxes, checklists, and dual measurements.

LAYOUT VARIANT TO USE:
- Variant: {variant['name']}
- Outline (Follow every section thoroughly):
{outline}

INTENT GUIDANCE:
- Intent: {intent}
- {_intent_guidance(intent)}

STYLE & ARCHITECTURE REQUIREMENTS (SEO, AEO, GEO, SILO & PINTEREST):
- Output clean HTML only for the article body.
- Do not use <h1> anywhere in the article body. WordPress title is the only H1.
- Heading Hierarchy: Start visible section headings at <h2> and use <h3> only for subsections.
- AEO (ANSWER ENGINE OPTIMIZATION & DIRECT ANSWER): Right after the first <h2> heading, provide a 40-60 word concise, factual "Direct Answer Paragraph" wrapped in a styled answer box:
  `<div style="background:#fffaf5; border-left:4px solid #8f1f28; padding:18px 22px; border-radius:10px; margin:20px 0;"><strong>Quick Answer:</strong> [Concise 40-60 word answer summary optimized for voice search and AI answer engines]</div>`
- GEO (GENERATIVE ENGINE OPTIMIZATION & COMPARISON TABLES): Include at least TWO responsive HTML tables:
  1. Ingredient Substitution & Dietary Swaps Table
  2. Dual Measurement Conversion Table (US Cups vs Metric Grams/ml)
  Format: `<table style="width:100%; border-collapse:collapse; margin:20px 0;">`
- PINTEREST DWELL-TIME & RETENTION OPTIMIZATION: 
  - Place a prominent 'Jump to Recipe 🍳' top button right under the intro: `<a href="#recipe-card" style="display:inline-block; background:#8f1f28; color:white; padding:12px 24px; border-radius:50px; text-decoration:none; font-weight:bold; margin:15px 0;">Jump to Recipe 🍳</a>`
  - Include an in-content Pinterest Save Banner midway through the article: `<div style="background:#fff0f0; border:1px dashed #8f1f28; padding:16px; border-radius:12px; margin:25px 0; text-align:center;">📌 <strong>Loved this recipe?</strong> <a href="https://www.pinterest.com/FoodTrendsBlog/" target="_blank" style="color:#8f1f28; font-weight:bold; text-decoration:underline;">Save & Follow on Pinterest</a> for daily viral food trends!</div>`
  - PRO CHEF TIP CALLOUT BOXES: Add 2-3 highlighted tip boxes throughout the instructions:
    `<div style="background:#f7fbf8; border-left:4px solid #2e7d32; padding:16px 20px; border-radius:8px; margin:20px 0;"><strong>👨‍🍳 Chef's Secret:</strong> [Specific technique tip on browning, temperature, or ingredient handling]</div>`
  - Wrap the printable recipe box in `<div id="recipe-card" style="background:#fffaf5; border:2px solid #8f1f28; border-radius:16px; padding:25px; margin:30px 0;">`.
  - Format ingredients as a checkbox list `<ul style="list-style:none; padding-left:0;"><li><label><input type="checkbox"> [Ingredient & Quantity]</label></li></ul>` and instructions as a numbered `<ol><li>` list.

RECIPE ARTICLE RULES (ONLY IF THIS IS A RECIPE):
- Provide comprehensive substitutions, variations, and storage guidance supported by sources.
- Do not invent nutrition facts or timings if unsupported by sources.
- Category MUST be "Recipes" (or "Recettes" if language is French).

FAQ AND SCHEMA RULES:
- Add a highly readable visible FAQ section at the end of the article content using a single <h2>Frequently Asked Questions</h2> heading.
- Include 5-7 high-search intent questions, writing each question in an <h3> tag and the answer in a <p> tag. Suffixing answers or removing questions is strictly forbidden.
- The system automatically generates and injects both FAQPage JSON-LD and Recipe JSON-LD (from the RECIPE_DATA block below). Do NOT write any `<script type="application/ld+json">` blocks in the HTML body.

SEARCH AND HELPFULNESS REQUIREMENTS:
- Treat PRIMARY KEYWORD as a guidance signal, not something to force unnaturally.
- Use the focus keyword naturally when it genuinely helps clarity in the TITLE, META_DESCRIPTION, SLUG, and early body copy.
- Use SECONDARY KEYWORDS and SUPPORTING KEYWORDS naturally across subheadings and body text only when they improve topical completeness.
- Keep the title compelling and clear, not vague, clickbait, or artificially optimized.
- Make the meta description specific and benefit-driven while staying within 140-160 characters.
- Structure the article for quick comprehension first, then supporting detail.
- Use clear entities, product names, and context so readers can immediately understand what the page is about.
- Expand into adjacent entities, ingredients, cuisines, product types, and cultural context only when the sources support it.
- Do not force El Mordjene, Dubai chocolate, or angel hair chocolate references unless they are central to this specific topic.
- Avoid keyword stuffing, filler intros, generic conclusions, and near-duplicate template phrasing.
- Build topical depth, not just keyword repetition. The article should feel complete even if a reader never saw the source articles.

INTERNAL LINKING RULES:
- Use exactly 2-3 internal links from the approved list below.
- Never invent URLs.

Allowed internal links:
{links_suggestion}

EXTERNAL LINKING RULES:
- Include exactly ONE high-quality, high-authority external link (e.g., to a reputable news source, official government site, or recognized culinary authority).
- The external link must be highly relevant to the topic.
- Format the external link to open in a new tab: <a href="..." target="_blank" rel="noopener noreferrer">...</a>


RECIPE DATA REQUIREMENTS:
If this is a real recipe article, output a strict JSON object with all recipe fields filled as completely as possible from the article and source material. If not, output {{}}.
**This data feeds the schema.org/Recipe JSON-LD for Pinterest Recipe Rich Pins and Google Recipe Rich Results — fill it completely and accurately.**
For recipe articles, do not leave ingredients or instructions empty.
Required JSON fields:
- recipe_name (string: the clean recipe name, e.g. "Bang Bang Chicken Skewers")
- recipe_description (string: 2-3 sentence sensory description of the dish)
- recipe_yield (string: e.g. "4 servings" or "12 cookies")
- prep_time_minutes (number: preparation time in minutes, e.g. 15)
- cook_time_minutes (number: cooking/baking time in minutes, e.g. 25)
- total_time_minutes (number or empty string: total time in minutes)
- ingredients (string: one ingredient per line INCLUDING quantities, e.g. "1.5 lbs chicken breasts, boneless\n1 tbsp olive oil")
- instructions (string: one numbered step per line as plain text, e.g. "Preheat oven to 400F\nMarinate chicken for 10 minutes")
- recipe_image (string: keep empty, system will fill from featured image)
- nutrition_calories (string: estimated calories per serving, e.g. "320 kcal" — use best estimate from source)
- video_url (string: empty if none)
- author_name (string: "El Mordjene Team" if unknown)
- recipe_keywords (string: comma-separated Pinterest search terms, e.g. "bang bang chicken, skewer recipe, easy chicken dinner")
- recipecuisine (string: e.g. "American", "Mediterranean", "Asian")
- recipecategory (string: e.g. "Dinner", "Dessert", "Appetizer", "Breakfast")
- video_upload_date (YYYY-MM-DD or empty)

OUTPUT FORMAT (STRICT):
TITLE: [under 60 chars]
META_DESCRIPTION: [140-160 chars]
SLUG: [lowercase-hyphenated]
TAGS: [tag1, tag2, tag3]
CATEGORY: [Recipes OR Food News OR Trends OR Sweets]
LANGUAGE: [en or fr]

---CONTENT_START---
[Raw HTML article body only]
---CONTENT_END---

---RECIPE_DATA_START---
[Raw JSON object only, no markdown fences]
---RECIPE_DATA_END---
"""

    return prompt


def build_image_prompt(topic_title, article_content_snippet=""):
    """Build a highly optimized, hyper-realistic prompt for a food photography featured image."""
    prompt = f"""Masterpiece, hyper-realistic food photography of: {topic_title}.
Style: High-end editorial culinary magazine (Bon Appetit / Michelin Guide style).
Composition: Professional hero shot, 45-degree angle or elegant overhead flat-lay.
Lighting: Volumetric natural lighting, soft window light with subtle rim highlights to emphasize intricate textures.
Camera: Shot on Sony A7R IV, 90mm f/2.8 Macro G Master lens for tack-sharp detail and creamy, professional bokeh.
Textures: Glistening surfaces, crispy caramelized edges, vibrant natural colors, ultra-high resolution 8k.
Background: Minimalist luxury, neutral marble or weathered rustic wood, artfully styled with scattered garnishes (flaky sea salt, fresh herbs, or crumbs).
CRITICAL: NO TEXT, NO LETTERS, NO NUMBERS, NO WATERMARKS, NO GRAPHICS. Pure professional photography only. 16:9 aspect ratio."""
    return prompt





