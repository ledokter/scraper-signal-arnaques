# Scraper signal-arnaques.com

Outil de collecte et d'analyse des arnaques signalées sur [signal-arnaques.com](https://www.signal-arnaques.com), développé dans le cadre de la **Formation anti-arnaques seniors**.

## Fonctionnalités

- Scraping par tag : `vinted`, `leboncoin`, `paypal`, `amazon`, et 60+ autres
- Interface graphique (lanceur.py) avec console de suivi
- Statistiques de mots et recherche par mot-clé sur toutes les données
- Scraping de tout le site en séquence (tous les tags)
- Contournement Cloudflare via `curl_cffi` (impersonation TLS)
- Collecte des IDs via Google CSE avec Playwright (navigateur visible)
- Reprise automatique après interruption (checkpoint)
- Détection du rate-limit Cloudflare (Error 1015) avec retry automatique
- Logs de debug horodatés dans `logs/`

## Installation

### Depuis WSL2 / Linux

```bash
cd "/mnt/c/Users/.../Formation-anti-arnaques seniors"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### Depuis Windows (pour Playwright GUI)

```powershell
python install_windows.py
```

## Utilisation

### Interface graphique

```bash
source .venv/bin/activate
python lanceur.py
```

### Ligne de commande

```bash
# Mode rapide — top 10 arnaques
python scraper_signal_arnaques.py --tag vinted

# Mode complet — toutes les arnaques
python scraper_signal_arnaques.py --detail --tag vinted

# Reprendre après interruption ou ban
python scraper_signal_arnaques.py --detail --tag vinted --resume

# Délai personnalisé (recommandé si erreur 1015)
python scraper_signal_arnaques.py --detail --tag vinted --delay 30 60
```

### Workflow complet (mode detail)

**Étape 1** — Collecter les IDs (depuis PowerShell Windows) :
```powershell
.venv_win\Scripts\python.exe collecter_ids.py --tag vinted
```

**Étape 2** — Scraper les détails (depuis WSL2) :
```bash
python scraper_signal_arnaques.py --detail --tag vinted
```

## Fichiers

| Fichier | Description |
|---|---|
| `lanceur.py` | Interface graphique |
| `scraper_signal_arnaques.py` | Scraper principal |
| `collecter_ids.py` | Collecte des IDs via navigateur (PowerShell) |
| `install_windows.py` | Installation Playwright Windows |
| `requirements.txt` | Dépendances Python |
| `GUIDE.md` | Guide complet d'utilisation |

## Dépendances

- [curl-cffi](https://github.com/yifeikong/curl_cffi) — contournement Cloudflare
- [playwright](https://playwright.dev/python/) — navigateur automatisé
- [beautifulsoup4](https://www.crummy.com/software/BeautifulSoup/) — parsing HTML
- [playwright-stealth](https://github.com/AtuboDad/playwright_stealth) — anti-détection

## Notes légales

Cet outil est destiné à un usage éducatif dans le cadre de la formation anti-arnaques pour les seniors. Les données collectées ne doivent pas être redistribuées. Respectez les conditions d'utilisation de signal-arnaques.com.
