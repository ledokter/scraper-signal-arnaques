# 08 — Automatisations : Cron, Délégation & Swarm
#hermes #automatisation #cron #swarm #délégation

← [[00 - Hermes MOC]]

---

## 1. Cron — Tâches planifiées

Hermes peut exécuter des prompts automatiquement selon un planning.

### Configuration dans `config.yaml`

```yaml
cron:
  # Briefing quotidien en semaine à 9h
  - name: "morning-briefing"
    schedule: "0 9 * * 1-5"
    prompt: "Bonjour ! Résume ce que j'ai fait hier sur le projet scraper et propose 3 tâches prioritaires pour aujourd'hui."

  # Vérification du scraper toutes les 6h
  - name: "scraper-check"
    schedule: "0 */6 * * *"
    prompt: |
      Vérifie que les fichiers arnaques_*.csv ont été mis à jour récemment.
      Si des fichiers n'ont pas été modifiés depuis 12h, génère une alerte.
      Chemin: /home/user0/scraper-signal-arnaques/

  # Rapport hebdomadaire le dimanche soir
  - name: "weekly-rapport"
    schedule: "0 20 * * 0"
    prompt: |
      Génère un rapport hebdomadaire des arnaques détectées cette semaine :
      - Nombre de signalements par plateforme
      - Nouvelles arnaques détectées
      - Tendances notables
      Sauvegarde dans /home/user0/rapports/semaine-$(date +%Y-%W).md

  # Nettoyage mensuel des vieilles données
  - name: "monthly-cleanup"
    schedule: "0 2 1 * *"
    prompt: "Archive les fichiers arnaques datant de plus de 6 mois."
```

### Activer le cron

```bash
hermes cron install     # Active et installe le service
hermes cron status      # Voir les jobs et leur état
hermes cron logs        # Voir les logs d'exécution
```

> [!note]
> Les jobs cron héritent du modèle, des outils et de la mémoire de ta session.

---

## 2. Délégation — Sous-agents parallèles

Spawn des **agents isolés** pour des tâches en parallèle.

### Dans une session

```
/delegate "Analyse arnaques_amazon.csv et identifie le type d'arnaque le plus fréquent" --model "google/gemini-flash-1.5"

/delegate "Scrape les 50 derniers signalements vinted et compare avec notre base" --toolsets "terminal,web"

/background "Cherche si 'arnaque livraison DHL 2024' apparaît dans les nouveaux signalements"
```

### Comment ça marche

```
Agent principal (toi)
    │
    ├── /delegate "tâche A" → Sous-agent A (isolé, propre historique)
    ├── /delegate "tâche B" → Sous-agent B (isolé, propre historique)
    └── /background "tâche C" → Tâche C (non-bloquante)
         │
         └── Résultats remontent dans l'agent principal
```

### Cas d'usage pratiques

```bash
# Analyser plusieurs plateformes en parallèle
hermes
> /delegate "Analyse arnaques_paypal.csv : top 5 types d'arnaques"
> /delegate "Analyse arnaques_vinted.csv : top 5 types d'arnaques"
> /delegate "Analyse arnaques_leboncoin.csv : top 5 types d'arnaques"
# Tous tournent en même temps, résultats agrégés
```

---

## 3. Swarm Mode — Pool d'agents persistants

Le Swarm Mode maintient un **pool de workers tmux** qui tourne en permanence.

### Activer le Swarm

Dans Hermes Workspace → onglet **Operations** → **Swarm Mode**

Ou en CLI :
```bash
hermes swarm start --workers 4    # 4 agents en parallèle
hermes swarm status
hermes swarm stop
```

### Rôles disponibles

| Lane | Persona | Idéal pour |
|------|---------|-----------|
| builder | 🔨 Builder | Coder, déboguer, refactorer |
| researcher | 🔭 Sage | Analyser, rechercher, synthétiser |
| reviewer | 🔍 Reviewer | Vérifier le code, tester |
| scribe | ✍️ Scribe | Rédiger, documenter |
| ops | ⚙️ Ops | Déployer, monitorer, gérer l'infra |
| qa | 🧪 QA | Tests, validation de données |
| triage | 📋 Triage | Prioriser, organiser |

### Dispatch par rôle

```
# Dans le Workspace → Operations Dashboard
Envoyer au Builder : "Optimise proxy_finder.py pour réduire les timeouts"
Envoyer au Researcher : "Trouve les nouvelles techniques d'arnaques au colis de 2025"
Envoyer au QA : "Vérifie que tous les CSV ont le bon format et signale les anomalies"
```

Les workers rotent automatiquement sans perdre le contexte entre les tâches.

---

## 4. Goals persistants

Hermes peut maintenir des **objectifs à long terme** entre les sessions :

```
# Dans une session
Définis comme objectif persistant : 
"Maintenir une base de données complète et à jour des arnaques françaises.
Alerter si une plateforme n'a pas de nouveaux signalements depuis 48h."
```

Hermes enregistre cet objectif dans sa mémoire et le consulte à chaque démarrage.

---

## 5. Batch Processing

Pour traiter de grands volumes de données :

```
Traite en batch tous les fichiers arnaques_*.json :
- Pour chaque fichier : extraire les 10 derniers signalements
- Identifier les mots-clés communs
- Créer un fichier résumé par plateforme dans /home/user0/rapports/
```

---

## Exemple d'automatisation complète pour ton projet

```yaml
# ~/.hermes/config.yaml — section cron

cron:
  # Chaque nuit : lancer le scraper et analyser
  - name: "nightly-scrape"
    schedule: "0 2 * * *"
    prompt: |
      1. Exécute /home/user0/scraper-signal-arnaques/lanceur.py
      2. Attends la fin de l'exécution
      3. Compare les nouveaux signalements avec la veille
      4. Si >50 nouveaux signalements : notifie via Telegram
      5. Sauvegarde les stats dans /home/user0/stats/$(date +%Y-%m-%d).json

  # Chaque lundi : rapport hebdomadaire
  - name: "weekly-recap"
    schedule: "0 8 * * 1"
    prompt: |
      Génère un rapport hebdomadaire des arnaques :
      - Top 3 plateformes avec le plus d'arnaques
      - Nouvelles tendances détectées
      - Recommandations pour améliorer la couverture du scraper
      Envoie le résumé sur Telegram.
```

→ [[09 - Cas d'usage — Scraping & Arnaques]] pour des exemples concrets
