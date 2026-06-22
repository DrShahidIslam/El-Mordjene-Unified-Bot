import fs from "node:fs/promises";
import path from "node:path";
import sharp from "sharp";
import { escapeHtml, wrapText } from "../templates/svg-text.js";

const THEMES = {
  recipe: {
    background: ["#fff0e1", "#ffc98f", "#d87439"],
    hero: "#6c2f12",
    panel: "#fff3e2",
    panelText: "#5d2f15",
    accent: "#9b471d",
    badge: "EASY RECIPE"
  },
  spread: {
    background: ["#f7ead8", "#d8b07b", "#7f4a22"],
    hero: "#4a2817",
    panel: "#f4e4d1",
    panelText: "#4a2c1c",
    accent: "#74401f",
    badge: "SPREAD INSPO"
  },
  trend: {
    background: ["#fff3e8", "#f0c29d", "#cb6e45"],
    hero: "#6a2d1d",
    panel: "#fff0e4",
    panelText: "#5c3426",
    accent: "#aa4b2c",
    badge: "TRENDING SWEET"
  }
};

const VARIANT_LABELS = {
  hero: "Hero Pin",
  list: "Saveable Summary",
  guide: "Quick Guide"
};

export async function renderAsset(asset, config) {
  const theme = THEMES[asset.contentType] || THEMES.trend;
  const fileName = `${asset.postSlug || asset.postId}-${asset.variant}.jpg`;
  const hasFeaturedImage = Boolean(asset.imageSourceUrl || asset.featuredImage);
  const quality = hasFeaturedImage ? 85 : 88;
  const effort = 6;
  const outputPath = path.join(config.assetsDir, "pinterest", fileName);
  const base = sharp({
    create: {
      width: 1000,
      height: 1500,
      channels: 4,
      background: theme.background[0]
    }
  });

  const composites = [];
  const visualBuffer = await loadImageBuffer(asset.imageSourceUrl || asset.featuredImage);

  if (visualBuffer) {
    composites.push({
      input: await sharp(visualBuffer)
        .resize(1000, 1500, { fit: "cover", position: "attention" })
        .blur(2)
        .modulate({ saturation: 1.05, brightness: 0.95 })
        .jpeg({ quality: 82, mozjpeg: true })
        .toBuffer(),
      top: 0,
      left: 0
    });

    composites.push({
      input: Buffer.from(`<svg width="1000" height="1500" xmlns="http://www.w3.org/2000/svg"><rect width="1000" height="1500" fill="rgba(42,25,16,0.04)"/></svg>`),
      top: 0,
      left: 0
    });

    composites.push({
      input: await sharp(visualBuffer)
        .resize(740, 520, { fit: "cover", position: "attention" })
        .modulate({ saturation: 1.08, brightness: 1.02 })
        .jpeg({ quality: 84, mozjpeg: true })
        .toBuffer(),
      top: 180,
      left: 130
    });
  } else {
    composites.push({
      input: Buffer.from(`<svg width="1000" height="1500" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="${theme.background[0]}"/><stop offset="45%" stop-color="${theme.background[1]}"/><stop offset="100%" stop-color="${theme.background[2]}"/></linearGradient></defs><rect width="1000" height="1500" fill="url(#bg)"/></svg>`),
      top: 0,
      left: 0
    });
  }

  const svg = buildOverlaySvg(asset, theme, Boolean(visualBuffer));
  composites.push({ input: Buffer.from(svg), top: 0, left: 0 });

  await fs.mkdir(path.join(config.assetsDir, "pinterest"), { recursive: true });
  await base.composite(composites).jpeg({ quality, mozjpeg: true }).toFile(outputPath);
  return outputPath;
}

function buildOverlaySvg(asset, theme, hasPhoto) {
  if (asset.variant === "list") {
    return buildListOverlay(asset, theme, hasPhoto);
  }

  if (asset.variant === "guide") {
    return buildGuideOverlay(asset, theme, hasPhoto);
  }

  return buildHeroOverlay(asset, theme, hasPhoto);
}

function buildHeroOverlay(asset, theme, hasPhoto) {
  const titleLines = wrapText(asset.overlayTitle, 22, 3);
  const subtitleLines = wrapText(asset.overlaySubtitle, 28, 2);
  const keywordLabel = wrapText(toDisplayCase(asset.primaryKeyword || asset.overlayTitle), 16, 1);

  const titleSvg = titleLines
    .map((line, index) => {
      const y = hasPhoto ? 740 + index * 60 : 330 + index * 90;
      const fill = hasPhoto ? theme.hero : "#fff8f1";
      return `<text x="170" y="${y}" font-size="56" font-family="system-ui, -apple-system, sans-serif" fill="${fill}" font-weight="800" letter-spacing="-1">${escapeHtml(line)}</text>`;
    })
    .join("");

  const subtitleSvg = subtitleLines
    .map((line, index) => {
      const y = 920 + index * 30;
      return `<text x="170" y="${y}" font-size="26" font-family="system-ui, -apple-system, sans-serif" fill="${theme.panelText}" font-weight="500">${escapeHtml(line)}</text>`;
    })
    .join("");

  const keywordSvg = keywordLabel
    .map((line, index) => `<text x="170" y="${206 + index * 26}" font-size="20" font-family="system-ui, -apple-system, sans-serif" fill="#fff7ef" font-weight="700" letter-spacing="1">${escapeHtml(line)}</text>`)
    .join("");

  return `
    <svg width="1000" height="1500" viewBox="0 0 1000 1500" xmlns="http://www.w3.org/2000/svg">
      <rect x="100" y="140" width="800" height="1040" rx="40" fill="rgba(255, 255, 255, 0.85)" opacity="0.9"/>
      <rect x="130" y="180" width="740" height="520" rx="30" fill="${hasPhoto ? "rgba(255,250,245,0.01)" : theme.hero}"/>
      <rect x="140" y="170" width="280" height="58" rx="29" fill="${theme.accent}" opacity="0.95"/>
      ${keywordSvg}
      ${titleSvg}
      ${subtitleSvg}
      <rect x="170" y="1060" width="660" height="56" rx="28" fill="${theme.hero}"/>
      <text x="500" y="1098" text-anchor="middle" font-size="24" font-family="system-ui, -apple-system, sans-serif" fill="#ffffff" font-weight="700" letter-spacing="2">READ MORE ON EL-MORDJENE.INFO</text>
    </svg>
  `;
}

function buildListOverlay(asset, theme, hasPhoto) {
  const subtitleLine = wrapText(asset.overlaySubtitle, 26, 1);
  const titleLines = wrapText(asset.overlayTitle, 20, 4);

  const subtitleSvg = subtitleLine
    .map((line) => `<text x="500" y="120" text-anchor="middle" font-size="28" font-family="system-ui, -apple-system, sans-serif" fill="#2b1a12" font-weight="700" letter-spacing="3">${escapeHtml(line)}</text>`)
    .join("");

  const boxHeight = titleLines.length * 70 + 60;
  const startY = 440 - ((titleLines.length - 1) * 70) / 2 + 20;

  const titleSvg = titleLines
    .map((line, index) => `<text x="500" y="${startY + index * 70}" text-anchor="middle" font-size="64" font-family="system-ui, -apple-system, sans-serif" fill="#111" font-weight="900" letter-spacing="-2">${escapeHtml(line)}</text>`)
    .join("");

  return `
    <svg width="1000" height="1500" viewBox="0 0 1000 1500" xmlns="http://www.w3.org/2000/svg">
      <rect width="1000" height="1500" fill="rgba(255,255,255,0.05)"/>
      <rect x="180" y="85" width="160" height="3" fill="${theme.accent}" opacity="0.8"/>
      <rect x="660" y="85" width="160" height="3" fill="${theme.accent}" opacity="0.8"/>
      ${subtitleSvg}
      <rect x="140" y="${440 - boxHeight / 2 - 10}" width="720" height="${boxHeight + 20}" rx="32" fill="rgba(255, 255, 255, 0.95)" stroke="${theme.hero}" stroke-width="4"/>
      ${titleSvg}
    </svg>
  `;
}
function buildGuideOverlay(asset, theme, hasPhoto) {
  const titleLines = wrapText(asset.overlayTitle, 18, 2);
  const subtitleLines = wrapText(asset.overlaySubtitle, 26, 1);

  const titleSvg = titleLines
    .map((line, index) => `<text x="500" y="${770 + index * 70}" text-anchor="middle" font-size="64" font-family="system-ui, -apple-system, sans-serif" fill="#ffffff" font-weight="800" letter-spacing="-1">${escapeHtml(line)}</text>`)
    .join("");

  const subtitleSvg = subtitleLines
    .map((line) => `<text x="500" y="${920}" text-anchor="middle" font-size="30" font-family="system-ui, -apple-system, sans-serif" fill="#fff6ef" font-weight="600" letter-spacing="1">${escapeHtml(line)}</text>`)
    .join("");

  return `
    <svg width="1000" height="1500" viewBox="0 0 1000 1500" xmlns="http://www.w3.org/2000/svg">
      <rect x="0" y="680" width="1000" height="820" fill="url(#grad)" opacity="0.95"/>
      <defs>
        <linearGradient id="grad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="transparent" />
          <stop offset="10%" stop-color="${theme.hero}" />
          <stop offset="100%" stop-color="#1a0b06" />
        </linearGradient>
      </defs>
      ${titleSvg}
      ${subtitleSvg}
      <rect x="300" y="1030" width="400" height="50" rx="25" fill="${theme.accent}"/>
      <text x="500" y="1063" text-anchor="middle" font-size="22" font-family="system-ui, -apple-system, sans-serif" fill="#ffffff" font-weight="700" letter-spacing="2">VISIT EL-MORDJENE.INFO</text>
    </svg>
  `;
}
async function loadImageBuffer(url) {
  if (!url) {
    return null;
  }

  try {
    const response = await fetch(url, {
      headers: {
        Accept: "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
      }
    });

    if (!response.ok) {
      return null;
    }

    const arrayBuffer = await response.arrayBuffer();
    return Buffer.from(arrayBuffer);
  } catch {
    return null;
  }
}

function toDisplayCase(value) {
  return String(value || "")
    .split(" ")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}






























