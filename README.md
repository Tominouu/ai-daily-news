# Bilan IA

**Newsletter quotidienne sur l'actualité de l'IA — automatique, gratuite, open source.**

Chaque matin à 8h, ce pipeline GitHub Actions récupère les articles des meilleures sources IA, les résume avec Mistral et t'envoie le tout par email avec un fichier audio MP3.

## Fonctionnalités

- **15+ sources RSS** — TechCrunch, OpenAI, Anthropic, arXiv, Le Monde, Hugging Face…
- **Résumé IA** — Chaque article est synthétisé en 2-3 phrases par Mistral (free tier)
- **Email quotidien** — Envoi automatisé à 6h UTC (8h Paris) via Gmail SMTP
- **Version audio** — Un fichier MP3 est joint à l'email, lu par synthèse vocale (gTTS)
- **100% gratuit** — GitHub Actions + APIs gratuites, rien à payer

## Prérequis

- Un compte [GitHub](https://github.com)
- Une clé API [Mistral](https://console.mistral.ai) (gratuite, ~500 tokens/jour consommés)
- Un compte Gmail / Google Workspace avec un **mot de passe d'application**

## Installation

### 1. Crée le dépôt GitHub

```bash
gh repo create ai-daily-news --public --clone
cd ai-daily-news
```

### 2. Copie les fichiers du projet

Place tous les fichiers de ce dépôt dans le dossier du projet.

### 3. Ajoute les secrets GitHub

```bash
gh secret set MISTRAL_API_KEY          # https://console.mistral.ai
gh secret set GMAIL_USER               # ton adresse Gmail
gh secret set GMAIL_APP_PASSWORD       # https://myaccount.google.com/apppasswords
```

### 4. Pousse et teste

```bash
git push
gh workflow run "Bilan IA Quotidien"
```

Le workflow s'exécute aussi automatiquement chaque jour à 6h UTC.

## 📁 Structure du projet

```
├── .github/workflows/
│   └── daily-news.yml       # Workflow GitHub Actions (cron 6h UTC)
├── scripts/
│   └── main.py              # Script principal : fetch RSS → résumé → email
├── config/
│   └── sources.json         # Configuration des flux RSS
├── requirements.txt         # Dépendances Python
└── README.md
```

## 📡 Sources RSS incluses

| Source | Description |
|---|---|
| [TechCrunch AI](https://techcrunch.com/category/artificial-intelligence/) | Startups & actu IA |
| [The Verge AI](https://www.theverge.com/ai-artificial-intelligence) | Tech & culture |
| [VentureBeat AI](https://venturebeat.com/category/ai/) | Business & IA |
| [Ars Technica AI](https://arstechnica.com/category/ai/) | Analyse technique |
| [MIT Tech Review](https://www.technologyreview.com/topic/artificial-intelligence/) | Recherche de pointe |
| [Google AI](https://blog.google/technology/ai/) | Blog Google Research |
| [Meta AI](https://ai.meta.com/blog/) | Blog Meta Research |
| [OpenAI](https://openai.com/blog/) | Blog OpenAI |
| [Anthropic](https://www.anthropic.com/) | Blog Anthropic |
| [DeepMind](https://deepmind.google/blog/) | Blog DeepMind |
| [Hugging Face](https://huggingface.co/blog) | Communauté open-source ML |
| [arXiv IA](http://export.arxiv.org/rss/cs.AI) | Prépublications académiques |
| [Le Monde IA](https://www.lemonde.fr/intelligence-artificielle/) | Actu française |
| [France-Info IA](https://www.francetvinfo.fr/intelligence-artificielle/) | Actu française |
| [Papers With Code](https://paperswithcode.com) | Recherche & code |

## 📧 Ce que tu reçois

L'email HTML contient :
- Un en-tête avec la date du jour
- Les articles regroupés par source avec un résumé de 2-3 phrases chacun
- Une section ** Tendances du jour** qui dégage les grandes tendances
- Tous les liens vers les articles originaux
- Un fichier **MP3** en pièce jointe avec la version audio

## 🔧 Personnalisation

### Ajouter / retirer des sources

Édite `config/sources.json` :

```json
[
  {"name": "Ma Source", "url": "https://example.com/rss"}
]
```

### Changer l'heure d'envoi

Modifie l'expression cron dans `.github/workflows/daily-news.yml` :

```yaml
on:
  schedule:
    - cron: "0 6 * * *"   # 6h UTC = 8h Paris
```

### Changer le modèle Mistral

Dans `scripts/main.py`, modifie le paramètre `model` :

```python
model="mistral-small-latest"   # rapide, économique
model="mistral-medium-latest"  # bon équilibre
model="mistral-large-latest"   # meilleure qualité
```

### Changer la voix TTS

Dans `scripts/main.py`, remplace `generate_audio_gtts` par une autre implémentation (ElevenLabs, Google Cloud TTS…).

## Consommation

| Service | Usage quotidien | Limite gratuite |
|---|---|---|
| Mistral API | ~500 tokens | 500 000 tokens/jour |
| Gmail SMTP | 1 email | 500 emails/jour |
| GitHub Actions | ~2 min d'exécution | 2000 min/mois |
| gTTS | 1 fichier audio | Illimité |

## Licence

MIT — fais ce que tu veux du projet.
