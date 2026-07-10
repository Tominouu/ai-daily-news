#!/usr/bin/env python3
"""AI News Daily Briefing — fetch RSS, summarize with Mistral, send via Gmail SMTP."""

import os
import sys
import json
import smtplib
import logging
from datetime import date
from email.mime.text import MIMEText

import feedparser
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("daily-news")


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_sources(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def fetch_articles(sources: list[dict], max_per_source: int = 3) -> list[dict]:
    articles: list[dict] = []
    seen_urls: set[str] = set()

    for src in sources:
        logger.info("Fetching: %s (%s)", src["name"], src["url"])
        try:
            feed = feedparser.parse(src["url"])
        except Exception as exc:
            logger.warning("Failed to fetch %s: %s", src["name"], exc)
            continue

        for entry in feed.entries[:max_per_source]:
            url = entry.get("link", "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            summary = entry.get("summary") or entry.get("description") or ""
            articles.append({
                "title": entry.get("title", "Sans titre"),
                "url": url,
                "description": summary[:400].replace("\n", " ").strip(),
                "source": src["name"],
                "published": entry.get("published", ""),
            })
    return articles


def build_prompt(articles: list[dict]) -> str:
    today = date.today().strftime("%d/%m/%Y")
    parts = [
        f"Tu es un assistant spécialisé dans le suivi de l'actualité IA.",
        f"Aujourd'hui nous sommes le {today}.",
        "",
        "Rédige un bilan structuré en français avec CES RÈGLES :",
        "- Pour chaque article : un résumé de 2-3 phrases qui dégage l'essentiel",
        "- Termine chaque résumé par le lien 🔗",
        "- Regroupe les articles par source avec un titre ## Source",
        "- Ajoute une section ## 📌 Tendances du jour à la fin (2-3 tendances clés)",
        "- Sois concret et précis, pas de bla-bla",
        "",
        "--- ARTICLES ---",
        "",
    ]

    current_source = None
    for a in articles:
        if a["source"] != current_source:
            current_source = a["source"]
            parts.append(f"\n## {current_source}")
        parts.append(f"\n### {a['title']}")
        parts.append(f"   {a['description'][:300]}…")
        parts.append(f"   🔗 {a['url']}")

    return "\n".join(parts)


def summarize(api_key: str, prompt: str, model: str = "mistral-small-latest") -> str:
    logger.info("Calling Mistral API (%s)...", model)
    resp = requests.post(
        "https://api.mistral.ai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 8192,
            "temperature": 0.3,
        },
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def send_email(
    content: str,
    gmail_user: str,
    gmail_password: str,
    to_email: str,
):
    today = date.today().strftime("%d/%m/%Y")
    msg = MIMEText(content, "plain", "utf-8")
    msg["Subject"] = f"🤖 Bilan IA — {today}"
    msg["From"] = gmail_user
    msg["To"] = to_email

    logger.info("Sending email to %s…", to_email)
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(gmail_user, gmail_password)
        server.send_message(msg)
    logger.info("Email sent ✅")


def main():
    sources_path = os.path.join(BASE_DIR, "config", "sources.json")

    mistral_key = os.environ.get("MISTRAL_API_KEY")
    gmail_user = os.environ.get("GMAIL_USER")
    gmail_pass = os.environ.get("GMAIL_APP_PASSWORD")
    to_email = os.environ.get("TO_EMAIL", gmail_user)

    if not all([mistral_key, gmail_user, gmail_pass]):
        logger.error(
            "Missing env vars: need MISTRAL_API_KEY, GMAIL_USER, GMAIL_APP_PASSWORD"
        )
        sys.exit(1)

    sources = load_sources(sources_path)
    logger.info("Loaded %d sources", len(sources))

    articles = fetch_articles(sources)
    logger.info("Fetched %d unique articles", len(articles))

    if not articles:
        logger.warning("No articles — sending alert email")
        send_email("⚠️ Aucun article trouvé aujourd'hui.", gmail_user, gmail_pass, to_email)
        return

    prompt = build_prompt(articles)
    summary = summarize(mistral_key, prompt)

    sources_list = ", ".join(s["name"] for s in sources)
    full = f"{summary}\n\n---\n📡 *BILAN IA — {date.today().strftime('%d/%m/%Y')}*\n_Sources: {sources_list}_"

    send_email(full, gmail_user, gmail_pass, to_email)


if __name__ == "__main__":
    main()
