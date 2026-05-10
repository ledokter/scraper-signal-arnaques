# 09 — Cas d'usage : Scraping & Projet Arnaques
#hermes #scraping #arnaques #python #exemples

← [[00 - Hermes MOC]]

---

> [!abstract] Contexte
> Ces exemples sont calibrés pour ton projet `scraper-signal-arnaques` dans WSL2 Kali Linux. Le scraper collecte les signalements d'arnaques sur signal-arnaques.fr par plateforme (PayPal, Vinted, Leboncoin, etc.).

---

## Workflow quotidien avec Hermes

```bash
# 1. Démarrer Hermes dans le projet
cd ~/scraper-signal-arnaques
hermes

# 2. Hermes lit automatiquement .hermes.md et comprend le contexte
# 3. Tu travailles en langage naturel
```

---

## Cas 1 — Analyser les données d'arnaques

### Analyse rapide d'une plateforme

```
@./arnaques_paypal.json
Analyse ces signalements PayPal :
- Combien au total ?
- Quels sont les 3 types d'arnaques les plus fréquents ?
- Y a-t-il des pics temporels ?
- Donne-moi les 5 signalements les plus récents
```

### Comparaison multi-plateformes

```
@./arnaques_vinted.csv @./arnaques_leboncoin.csv @./arnaques_facebook-marketplace.csv
Compare ces trois plateformes de vente entre particuliers :
- Laquelle a le plus d'arnaques ?
- Quels types d'arnaques sont communs aux trois ?
- Quelles arnaques sont spécifiques à chaque plateforme ?
Fais un tableau comparatif.
```

### Détection de tendances

```
Analyse tous les fichiers arnaques_*.json dans ce répertoire.
Identifie :
1. Les plateformes avec le plus fort volume (top 5)
2. Les types d'arnaques émergentes (apparus il y a moins de 3 mois)
3. Les corrélations entre plateformes
Génère un rapport markdown dans ./rapports/tendances-$(date +%Y-%m).md
```

---

## Cas 2 — Déboguer et améliorer le scraper

### Déboguer une erreur

```
@./scraper_signal_arnaques.py
J'ai cette erreur quand je lance le scraper :
```
ConnectionError: HTTPSConnectionPool(host='signal-arnaques.fr', port=443): Max retries exceeded
```
Le proxy_finder.py ne trouve plus de proxies valides.
Aide-moi à diagnostiquer et corriger.
```

### Optimiser le code

```
@./scraper_signal_arnaques.py @./proxy_finder.py @./ua_rotation.py
Le scraper est lent (environ 2h pour toutes les plateformes).
Propose des optimisations :
- Scraping parallèle des plateformes
- Meilleure gestion du cache
- Optimisation de la rotation de proxies
Implémente les changements directement.
```

### Ajouter une nouvelle plateforme

```
Je veux ajouter le scraping de "signal-arnaques.fr/arnaques/tiktok".
@./scraper_signal_arnaques.py
Regarde la structure du code existant pour leboncoin et crée une fonction similaire pour TikTok.
Les données devront être exportées dans arnaques_tiktok.csv et arnaques_tiktok.json
```

---

## Cas 3 — Automatisation avec cron

### Configurer le monitoring automatique

```yaml
# Ajouter dans ~/.hermes/config.yaml
cron:
  - name: "scraper-nightly"
    schedule: "0 3 * * *"
    prompt: |
      Lance le scraper : python /home/user0/scraper-signal-arnaques/lanceur.py
      Attends la fin. Si erreur → log dans /home/user0/logs/scraper-errors.log
      Si succès → compte les nouveaux signalements par rapport à hier
      Si >100 nouveaux → envoie un message Telegram avec le résumé
```

### Monitoring des proxies

```yaml
  - name: "proxy-refresh"
    schedule: "0 */4 * * *"
    prompt: |
      Lance python /home/user0/scraper-signal-arnaques/proxy_finder.py
      Vérifie que la liste de proxies contient au moins 10 proxies valides.
      Si <10 : tente de trouver de nouvelles sources de proxies et mettre à jour.
```

---

## Cas 4 — Swarm multi-agents pour analyse massive

Dans Hermes Workspace → Operations :

```
Builder lane:
→ "Optimise le scraper pour supporter 5 requêtes parallèles. 
   Utilise asyncio/aiohttp. @./scraper_signal_arnaques.py"

Researcher lane:
→ "Recherche les nouvelles techniques d'arnaques en ligne en France 
   en 2025. Résume en bullet points les patterns non couverts par notre scraper."

QA lane:
→ "Vérifie l'intégrité de tous les fichiers arnaques_*.json :
   - JSON valide
   - Champs obligatoires présents
   - Pas de doublons
   Génère un rapport des anomalies."

Scribe lane:
→ "Écris une documentation technique pour chaque script Python du projet.
   Basé sur @./scraper_signal_arnaques.py @./lanceur.py etc."
```

---

## Cas 5 — Analyse OSINT enrichie

```
Pour les 10 derniers signalements arnaques_paypal.json :
- Récupère les URLs mentionnées dans les signalements
- Vérifie si ces URLs sont dans des listes noires publiques (VirusTotal, PhishTank…)
- Identifie les éventuels noms de domaine communs
- Crée un rapport d'investigation
```

---

## Cas 6 — Gestion Git et code

```
@./scraper_signal_arnaques.py
Fais une review de ce fichier :
- Sécurité : y a-t-il des risques ?
- Qualité du code : PEP8, docstrings
- Performance : goulots d'étranglement
Corrige les problèmes critiques directement.
```

```
Le scraper a de nouveaux changements.
Crée un commit git avec un message descriptif et pousse sur la branche main.
/github-pr-workflow
```

---

## Cas 7 — Rapport automatique pour Obsidian

```
Génère un rapport hebdomadaire des arnaques au format Obsidian markdown.
Utilise les callouts Obsidian (> [!warning], > [!info]).
Sauvegarde dans /mnt/c/Users/user0/Documents/###MEGOBSI/MegaObs/Obsidian-Drop/Rapports/arnaques-$(date +%Y-W%W).md
```

---

## Commandes one-shot utiles

```bash
# Compte rapide des signalements par plateforme
hermes chat -q "Compte le nombre de lignes dans chaque fichier arnaques_*.csv et trie par volume décroissant" 

# Vérification rapide avant un push
hermes chat -q "@./scraper_signal_arnaques.py Vérifie que le code ne contient pas de credentials en clair ou de données sensibles"

# Générer un .gitignore adapté
hermes chat -q "Génère un .gitignore Python adapté à ce projet @./requirements.txt"

# Résumer un gros fichier JSON
hermes chat -q "@./arnaques_leboncoin.json Donne-moi les 5 premières et 5 dernières entrées, et les statistiques de base"
```

---

## Workflow de développement recommandé

```
1. cd ~/scraper-signal-arnaques
2. hermes                          ← Démarre dans le contexte projet
3. Demande en langage naturel      ← "Ajoute la gestion des timeouts dans proxy_finder.py"
4. Hermes code + teste             ← Il exécute les tests lui-même
5. /github-pr-workflow             ← Crée la PR si tout est bon
6. Continue la conversation        ← Itère si besoin
```

---

## Tips & astuces

> [!tip] Référencer plusieurs fichiers d'un coup
> ```
> @./scraper_signal_arnaques.py @./proxy_finder.py @./ua_rotation.py
> Comment ces trois fichiers interagissent-ils ? Documente leurs interfaces.
> ```

> [!tip] Mode one-shot pour les scripts CI
> ```bash
> # Dans un cron système ou script bash
> hermes chat -q "Vérifie la santé du scraper et retourne OK ou ERREUR" --exit-on-error
> ```

> [!tip] Utiliser /background pour les longues tâches
> ```
> /background "Scrape et analyse les 500 derniers signalements leboncoin, génère un rapport"
> # Continue à travailler pendant que l'analyse tourne
> ```
