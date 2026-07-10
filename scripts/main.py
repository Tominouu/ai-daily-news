#!/usr/bin/env python3
"""AI News Daily Briefing — fetch RSS, summarize with Mistral, send via Gmail SMTP."""

import os
import re
import sys
import json
import tempfile
import smtplib
import logging
from datetime import date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

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


def md_to_html(text: str) -> str:
    lines = text.split("\n")
    html = ""
    in_list = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            if in_list:
                html += "</ul>\n"
                in_list = False
            html += f"<h2>{stripped[3:]}</h2>\n"
        elif stripped.startswith("### "):
            if in_list:
                html += "</ul>\n"
                in_list = False
            html += f"<h3>{stripped[4:]}</h3>\n"
        elif stripped.startswith("- "):
            if not in_list:
                html += "<ul>\n"
                in_list = True
            item = stripped[2:]
            item = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", item)
            html += f"  <li>{item}</li>\n"
        elif stripped.startswith("🔗"):
            link = stripped[2:].strip()
            html += f'<p><a href="{link}">{link}</a></p>\n'
        elif stripped.startswith("📡"):
            html += f'<p class="meta">{stripped}</p>\n'
        elif stripped.startswith("---"):
            if in_list:
                html += "</ul>\n"
                in_list = False
            html += "<hr>\n"
        else:
            if in_list:
                html += "</ul>\n"
                in_list = False
            if stripped:
                processed = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", stripped)
                processed = re.sub(r"(https?://\S+)", r'<a href="\1">\1</a>', processed)
                html += f"<p>{processed}</p>\n"
    if in_list:
        html += "</ul>\n"
    return html


HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
</head>
<body style="margin:0;padding:0;background:#f4f6f9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0">
<tr><td align="center" style="padding:24px 16px">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#ffffff;border-radius:12px;box-shadow:0 2px 12px rgba(0,0,0,.06)">
<tr><td style="padding:32px 32px 16px;background:linear-gradient(135deg,#667eea,#764ba2);border-radius:12px 12px 0 0;text-align:center">
<h1 style="margin:0;color:#fff;font-size:24px;font-weight:700">🤖 Bilan IA</h1>
<p style="margin:6px 0 0;color:rgba(255,255,255,.8);font-size:14px">{date}</p>
</td></tr>
<tr><td style="padding:28px 32px;font-size:15px;line-height:1.6;color:#1a1a2e">
{body}
</td></tr>
<tr><td style="padding:16px 32px 24px;border-top:1px solid #eee;text-align:center;font-size:12px;color:#999">
Généré automatiquement chaque matin — <a href="https://github.com/tom/ai-daily-news" style="color:#667eea">ai-daily-news</a>
</td></tr>
</table>
</td></tr>
</table>
</body>
</html>"""


def clean_for_audio(text: str) -> str:
    lines = text.split("\n")
    out = []
    for line in lines:
        s = line.strip()
        s = re.sub(r"🔗\s*\S+", "", s)
        s = re.sub(r"https?://\S+", "", s)
        s = re.sub(r"\*\*|\*|__", "", s)
        s = re.sub(r"_ _", "", s)
        s = re.sub(r"##+\s*", "", s)
        s = re.sub(r"---", "", s)
        s = re.sub(r"\s+", " ", s).strip()
        if s:
            out.append(s)
    return "\n".join(out)


def generate_audio_gtts(text: str, output_path: str):
    from gtts import gTTS

    today = date.today().strftime("%d %B %Y")
    intro = f"Bonjour. Voici le bilan intelligence artificielle du {today}."
    outro = "Merci d'avoir écouté ce bilan. À demain pour de nouvelles actualités."
    full = f"{intro}\n\n{clean_for_audio(text)}\n\n{outro}"

    logger.info("Generating audio (gTTS)...")
    tts = gTTS(text=full, lang="fr", slow=False)
    tts.save(output_path)
    logger.info("Audio saved: %s (size: %.1f MB)", output_path, os.path.getsize(output_path) / 1_000_000)


def generate_audio_elevenlabs(text: str, output_path: str, api_key: str):
    today = date.today().strftime("%d %B %Y")
    intro = f"Bonjour. Voici le bilan intelligence artificielle du {today}."
    outro = "Merci d'avoir écouté ce bilan. À demain pour de nouvelles actualités."
    full = f"{intro}\n\n{clean_for_audio(text)}\n\n{outro}"

    if len(full) > 9000:
        logger.warning("Text too long for ElevenLabs free tier (%d chars), truncating…", len(full))
        full = full[:9000]

    logger.info("Generating audio (ElevenLabs)...")
    resp = requests.post(
        "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM",
        headers={
            "xi-api-key": api_key,
            "Content-Type": "application/json",
        },
        json={
            "text": full,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.4, "similarity_boost": 0.7},
        },
        timeout=120,
    )
    resp.raise_for_status()
    with open(output_path, "wb") as f:
        f.write(resp.content)
    logger.info("Audio saved: %s (size: %.1f MB)", output_path, os.path.getsize(output_path) / 1_000_000)


def generate_audio(text: str, output_path: str, elevenlabs_key: str | None = None):
    if elevenlabs_key:
        generate_audio_elevenlabs(text, output_path, elevenlabs_key)
    else:
        generate_audio_gtts(text, output_path)


def send_email(
    content: str,
    gmail_user: str,
    gmail_password: str,
    to_email: str,
    audio_path: str | None = None,
):
    today = date.today().strftime("%d/%m/%Y")
    body_html = md_to_html(content)
    html = HTML_TEMPLATE.replace("{date}", today).replace("{body}", body_html)

    msg = MIMEMultipart("mixed")
    msg["Subject"] = f"🤖 Bilan IA — {today}"
    msg["From"] = gmail_user
    msg["To"] = to_email

    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(content, "plain", "utf-8"))
    alt.attach(MIMEText(html, "html", "utf-8"))
    msg.attach(alt)

    if audio_path and os.path.exists(audio_path):
        with open(audio_path, "rb") as f:
            audio = MIMEBase("audio", "mp3")
            audio.set_payload(f.read())
            encoders.encode_base64(audio)
            audio.add_header("Content-Disposition", "attachment", filename="bilan-ia.mp3")
            msg.attach(audio)

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
    elevenlabs_key = os.environ.get("ELEVENLABS_API_KEY")

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

    audio_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            audio_path = tmp.name
        generate_audio(summary, audio_path, elevenlabs_key)
    except Exception as exc:
        logger.warning("Audio generation failed: %s — sending text only", exc)

    send_email(full, gmail_user, gmail_pass, to_email, audio_path)

    if audio_path and os.path.exists(audio_path):
        os.unlink(audio_path)


if __name__ == "__main__":
    main()
