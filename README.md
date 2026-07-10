# Bilan IA

Newsletter quotidienne sur l'actualite de l'IA -- automatique, gratuite, open source.

Chaque matin a 8h, un pipeline GitHub Actions recupere les articles des meilleures sources IA, les resume avec Mistral et envoie le tout par email a tous les abonnes, avec un fichier audio MP3.

Une page d'inscription est disponible a l'adresse du projet sur GitHub Pages.

## Fonctionnalites

- **15+ sources RSS** -- TechCrunch, OpenAI, Anthropic, arXiv, Le Monde, Hugging Face...
- **Resume IA** -- Chaque article est synthetise en 2-3 phrases par Mistral (free tier)
- **Page d'inscription** -- Formulaire public sur GitHub Pages, les emails sont stockes dans un Google Sheet
- **Envoi multi-destinataires** -- Le bilan est envoye chaque matin a tous les abonnes (BCC)
- **Version audio** -- Un fichier MP3 est joint a l'email (gTTS)
- **100% gratuit** -- GitHub Actions + APIs gratuites, rien a payer

## Architecture

```
Abonne → Page d'inscription (GitHub Pages)
              ↓ POST
         Google Apps Script
              ↓
         Google Sheet (stockage emails)
              ↓ (lecture CSV)
         GitHub Actions (cron 6h UTC)
              ↓
         Fetch 15 flux RSS  →  Resume Mistral  →  Email + MP3 a tous les abonnes
```

## Pre-requis

- Un compte [GitHub](https://github.com)
- Une cle API [Mistral](https://console.mistral.ai) (gratuite, ~500 tokens/jour)
- Un compte Gmail / Google Workspace avec un mot de passe d'application
- Un compte Google (pour le Sheet et Apps Script)

## Installation

### 1. Creer le depot

```bash
gh repo create ai-daily-news --public --clone
cd ai-daily-news
```

### 2. Copier les fichiers

Place tous les fichiers de ce depot dans le dossier du projet.

### 3. Configurer Google Sheet + Apps Script

a) Cree un Google Sheet avec 3 colonnes : `email` | `date` | `active`
b) **Extensions > Apps Script**, colle le code suivant :

```javascript
function doPost(e) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const email = e.parameter.email;
  if (!email) return ContentService.createTextOutput('{"ok":false}');
  sheet.appendRow([email.trim().toLowerCase(), new Date(), "oui"]);
  return ContentService.createTextOutput('{"ok":true}');
}
```

c) **Deployer > Nouveau deploiement** -- Type: Application Web
   - Executer en tant que : Moi
   - Acces : Tout le monde
   - Copie l'URL genere

d) Remplace l'URL dans `index.html` :

```javascript
const SCRIPT_URL = "https://script.google.com/macros/s/VOTRE_ID/exec";
```

e) **File > Share > Publish to web** -- Format CSV, copie l'URL

### 4. Ajouter les secrets GitHub

```bash
gh secret set MISTRAL_API_KEY           # https://console.mistral.ai
gh secret set GMAIL_USER                # ton adresse Gmail
gh secret set GMAIL_APP_PASSWORD        # https://myaccount.google.com/apppasswords
gh secret set GOOGLE_SHEET_CSV_URL      # l'URL CSV du Google Sheet
```

### 5. Activer GitHub Pages

Settings > Pages > Source: Deploy from branch > master > / (root) > Save.

### 6. Pousser et tester

```bash
git push
gh workflow run "Bilan IA Quotidien"
```

Le workflow s'execute aussi automatiquement chaque jour a 6h UTC (8h Paris).

## Structure du projet

```
├── .github/workflows/
│   └── daily-news.yml       # Workflow GitHub Actions (cron 6h UTC)
├── scripts/
│   └── main.py              # Script principal : fetch RSS, resume, email
├── config/
│   └── sources.json         # Configuration des flux RSS
├── index.html               # Page d'inscription GitHub Pages
├── requirements.txt         # Dependances Python
└── README.md
```

## Sources RSS incluses

TechCrunch AI, The Verge AI, VentureBeat AI, Ars Technica, MIT Tech Review, Google AI, Meta AI, OpenAI, Anthropic, DeepMind, Hugging Face, arXiv, Papers With Code, Le Monde, France Info.

## Ce que tu recois

L'email HTML contient :
- Les articles regroupes par source avec un resume de 2-3 phrases chacun
- Une section Tendances du jour en fin de bilan
- Tous les liens vers les articles originaux
- Un fichier MP3 en piece jointe avec la version audio

## Personnalisation

### Ajouter / retirer des sources

Edite `config/sources.json` :

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
    - cron: "0 6 * * *"
```

### Changer le modele Mistral

Dans `scripts/main.py`, modifie le parametre `model` :

```python
model="mistral-small-latest"   # rapide, economique
model="mistral-medium-latest"  # bon equilibre
model="mistral-large-latest"   # meilleure qualite
```

## Consommation

| Service | Usage quotidien | Limite gratuite |
|---|---|---|
| Mistral API | ~500 tokens | 500 000 tokens/jour |
| Gmail SMTP | 1 email (+ BCC) | 500 emails/jour |
| GitHub Actions | ~2 min d'execution | 2000 min/mois |
| gTTS | 1 fichier audio | Illimite |
| Google Sheets | quelques lignes/jour | Illimite |

## Licence

MIT
