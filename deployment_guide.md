# 🚀 Food Trends Bot - Deployment Guide

This guide explains how to set up your GitHub repository for fully autonomous content and pin generation.

## 1. GitHub Secrets Checklist
Go to **Settings > Secrets and variables > Actions** and add the following **Repository Secrets**:

### 🛡️ Core Secrets
- `WP_URL`: `https://el-mordjene.info/`
- `WP_USERNAME`: Your WordPress username
- `WP_PASSWORD`: Your WordPress Application Password
- `PINTEREST_ACCESS_TOKEN`: Your Pinterest API Token
- `PINTEREST_BOARD_ID`: Your target Board ID
- `GEMINI_API_KEYS`: Key1,Key2,Key3 (Comma-separated)
- `HUGGINGFACE_API_KEY`: Key1,Key2 (Comma-separated)
- `SILICONFLOW_API_KEY`: Your SiliconFlow Key

## 2. GitHub Actions Logic
The system is split into two automated workflows (YAML files in `.github/workflows/`):

### ✍️ WordPress Publisher (2x Daily)
- **Command**: `python alerts_engine/main.py --once`
- **Behavior**: Picks 2 pending topics, checks for duplicates, generates content (AI-only if needed), and publishes to WordPress.

### 📌 Pinterest Pin Worker (8x Daily)
- **Command**: `python pinterest_engine/pin_generator.py --worker`
- **Behavior**: Picks a published article, generates a unique "Angle" image (Hero, Process, or Detail), and posts to Pinterest via the Bridge Page.

## 3. The Bridge Site (GitHub Pages)
Your bridge site is live at: `https://drshahidislam.github.io/Food-Trends-Blog/`
- The `index.html` at the root automatically links to the latest editions.
- Individual "Discovery" pages are stored in `bridge_page/discovery/`.

## 4. Topic Management
- Edit `topic_queue.json` directly on GitHub to add new topics or change priorities.
- The bot will automatically update `wp_status` and `pin_count` after each run.

## 💡 Pro Tips
- **Deduplication**: The bot will NEVER double-post. If you add a topic that already exists on your site, it will simply find the old URL and start pinning it.
- **Image Fallback**: If Hugging Face is down, the bot automatically switches to Kolors. If both fail, it uses a high-quality "Pollinations" last-resort.
