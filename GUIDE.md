# Guide d'installation et d'utilisation — Scraper signal-arnaques.com

## Prérequis

- Python 3.10+ installé dans Kali WSL2
- Accès au dossier via `/mnt/c/Users/user0/Documents/###MEGOBSI/MegaObs/Obsidian-Drop/Formation-anti-arnaques seniors/`

---

## 1. Se placer dans le dossier

```bash
cd "/mnt/c/Users/user0/Documents/###MEGOBSI/MegaObs/Obsidian-Drop/Formation-anti-arnaques seniors"
```

---

## 2. Créer le venv (une seule fois)

```bash
python3 -m venv .venv
```

---

## 3. Activer le venv

```bash
source .venv/bin/activate
```

Le prompt devient : `(.venv) user@kali:...$`

Pour désactiver plus tard :
```bash
deactivate
```

---

## 4. Installer les dépendances

```bash
pip install -r requirements.txt
```

Puis installer le navigateur Chromium pour Playwright :
```bash
playwright install chromium
```

> Ces deux commandes ne sont à lancer **qu'une seule fois** après la création du venv.

---

## 5. Utilisation

### Interface graphique (recommandé)

```bash
python lanceur.py
```

Ouvre une fenêtre GUI avec sélection de tag, boutons ① et ②, et console de suivi.

> Nécessite un affichage (WSLg, VcXsrv, ou X11 forwarding).  
> Sans affichage, utilisez les commandes en ligne ci-dessous.

---

### Mode rapide — top 10 arnaques du tag

```bash
python scraper_signal_arnaques.py --tag vinted
python scraper_signal_arnaques.py --tag leboncoin
python scraper_signal_arnaques.py --tag paypal
python scraper_signal_arnaques.py --tag amazon
```

Produit : `arnaques_<tag>_listing.json` et `.csv`

---

### Mode complet — toutes les arnaques (2 étapes)

**Étape 1 — Collecter les IDs** (nécessite un navigateur visible)

Depuis **PowerShell Windows** (pas WSL2, car Playwright a besoin d'un vrai affichage).

Si Playwright n'est pas encore installé sur Windows, lancez d'abord :
```powershell
cd "C:\Users\user0\Documents\###MEGOBSI\MegaObs\Obsidian-Drop\Formation-anti-arnaques seniors"
python install_windows.py
```

Puis collectez les IDs :
```powershell
.venv_win\Scripts\python.exe collecter_ids.py --tag vinted
```

Produit : `ids_vinted.json`

**Étape 2 — Scraper les détails** (depuis WSL2, venv activé)

```bash
python scraper_signal_arnaques.py --detail --tag vinted
```

Produit : `arnaques_vinted.json` et `.csv`

---

### Autres options

```bash
# Limiter à 50 arnaques
python scraper_signal_arnaques.py --detail --tag vinted --max 50

# Sans fenêtre navigateur (moins fiable avec Cloudflare)
python scraper_signal_arnaques.py --detail --tag vinted --headless
```

---

## 6. Tags disponibles

### Sites d'annonces
`vinted` `leboncoin` `facebook-marketplace` `seloger` `pap` `vivastreet` `lacentrale`

### E-commerce
`amazon` `cdiscount` `fnac` `darty` `ebay` `aliexpress` `shein` `temu` `wish`

### Paiement / Banque
`paypal` `paylib` `lydia` `sumeria` `credit-agricole` `bnp` `societe-generale`
`caisse-epargne` `lcl` `boursorama` `orange-bank` `revolut` `wise`

### Livraison / Colis
`chronopost` `colissimo` `laposte` `mondial-relay` `ups` `dhl` `fedex` `dpd` `gls`

### Réseaux sociaux
`facebook` `instagram` `whatsapp` `telegram` `snapchat` `twitter` `tiktok` `linkedin`

### Streaming / Abonnements
`netflix` `spotify` `disney` `canal` `prime` `deezer` `molotov`

### Administrations / Services publics
`impots` `ameli` `cpam` `caf` `urssaf` `retraite` `assurance-maladie` `antai` `prefecture`

### Énergie / Télécom
`edf` `enedis` `engie` `sfr` `orange` `free` `bouygues` `sosh`

### Divers
`sms` `email` `telephone` `phishing` `arnaque` `escroquerie`
`crypto` `bitcoin` `investissement` `emploi` `loterie` `cagnotte`

---

## 7. Fichiers de sortie

| Fichier | Contenu |
|---|---|
| `arnaques_<tag>_listing.json/csv` | Top 10 — mode rapide |
| `arnaques_<tag>.json/csv` | Toutes les arnaques — mode complet |
| `ids_<tag>.json` | IDs collectés par `collecter_ids.py` |

---

## 8. Résumé des commandes (copier-coller)

```bash
# Installation complète (une seule fois)
cd "/mnt/c/Users/user0/Documents/###MEGOBSI/MegaObs/Obsidian-Drop/Formation-anti-arnaques seniors"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

# Utilisation quotidienne
source .venv/bin/activate
python lanceur.py                                      # interface graphique
python scraper_signal_arnaques.py --tag vinted         # ligne de commande
```
