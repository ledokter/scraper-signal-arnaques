# 03 — Commandes CLI
#hermes #cli #commandes #référence

← [[00 - Hermes MOC]]

---

## Commandes principales

### Chat & Sessions

```bash
hermes                          # Lance une session interactive
hermes chat -q "ta question"    # One-shot (une question → répond → quitte)
hermes --continue               # Reprend la dernière session
hermes -c                       # Raccourci de --continue
hermes --resume <session-id>    # Reprend une session spécifique
hermes -s skill1,skill2         # Précharge des skills au démarrage
```

**Exemples concrets :**
```bash
# Analyser rapidement un fichier CSV
hermes chat -q "Combien de signalements uniques dans arnaques_paypal.csv ?"

# Reprendre là où on s'était arrêté hier
hermes --continue

# Lancer avec le skill de scraping préchargé
hermes -s web-scraper,python-helper
```

---

### Gestion des sessions

```bash
hermes sessions list            # Lister toutes les sessions passées
hermes sessions rename <id> "Mon scraper session"   # Renommer une session
```

---

### Configuration & Setup

```bash
hermes setup                    # Wizard de configuration complet
hermes model                    # Choisir provider + modèle interactif
hermes tools                    # Configurer les outils activés
hermes config set KEY value     # Modifier un paramètre directement
hermes doctor                   # Diagnostiquer les problèmes
hermes version                  # Version installée
hermes update                   # Mettre à jour Hermes
```

---

### Gateway & Services

```bash
hermes gateway run              # Démarrer le gateway (port 8642)
hermes gateway install          # Installer comme service systemd
hermes gateway start            # Démarrer le service
hermes gateway stop             # Arrêter le service
hermes gateway restart          # Redémarrer
hermes gateway status           # État + plateformes connectées
hermes gateway setup            # Configurer plateformes de messagerie
```

---

### Dashboard

```bash
hermes dashboard                # Lance le dashboard web (port 9119)
```

> [!note] WSL2
> Le terminal intégré du dashboard est fonctionnel uniquement en WSL2 sur Windows.

---

### Skills

```bash
hermes skills search <terme>           # Chercher un skill
hermes skills install <org/skills/nom> # Installer un skill
hermes skills browse                   # Navigateur interactif
hermes skills list                     # Lister tes skills installés
hermes skills update                   # Mettre à jour tous les skills
```

---

### Cron & Automatisations

```bash
hermes cron install             # Activer le cron Hermes
hermes cron status              # Voir les jobs planifiés
hermes cron logs                # Logs des exécutions
```

---

## Slash commands (dans une session)

Une fois dans `hermes`, utilise ces commandes :

### Modèle & Comportement
```
/model                    → Changer de modèle en live
/reasoning high           → Augmenter l'effort de raisonnement
/reasoning low            → Mode rapide/économique
/personality pirate       → Changer le ton (pirate, kawaii, concise, helpful…)
/verbose                  → Cycle affichage outils : off → new → all → verbose
```

### Session
```
/title Ma session scraper → Nommer la session courante
/compress                 → Forcer la compression du contexte
/usage                    → Voir les tokens utilisés et coût estimé
/help                     → Afficher toutes les commandes disponibles
```

### Skills (depuis une session)
```
/skills browse            → Naviguer dans le hub de skills
/nom-du-skill [args]      → Utiliser un skill installé directement
```

**Exemples :**
```
/github-pr-workflow crée une PR pour les corrections du scraper
/translate-fr Ce texte en anglais s'il te plaît
/summarize ~/scraper-signal-arnaques/arnaques_leboncoin.json
```

### Outils & Contexte
```
/tools                    → Lister les outils disponibles maintenant
/background "ta tâche"   → Lancer une tâche en arrière-plan (non-bloquant)
/delegate "ta tâche"     → Déléguer à un sous-agent isolé
```

### Voice
```
/voice on                 → Activer l'enregistrement vocal (Ctrl+B pour parler)
/voice tts                → Activer les réponses vocales (text-to-speech)
/voice off                → Désactiver
```

### Mode busy (pendant que l'agent travaille)
```
/busy interrupt           → Interrompre l'agent si tu tapes
/busy queue               → Mettre en file d'attente
/busy steer               → Réorienter l'agent en live
```

---

## Syntaxe @-mention (fichiers inline)

Dans n'importe quelle session, tu peux référencer du contenu :

```
@~/scraper-signal-arnaques/arnaques_vinted.csv analyse ce fichier
@./scraper_signal_arnaques.py explique ce code
@https://signal-arnaques.fr/arnaque/123 scrape cette page
@~/scraper-signal-arnaques/ regarde tous les fichiers CSV
```

---

## Variables d'environnement utiles

```bash
# Lancer hermes en mode debug
HERMES_DEBUG=1 hermes

# Forcer un modèle pour une session
HERMES_MODEL=gpt-4o hermes chat -q "test"

# Lancer Ollama en parallèle
OLLAMA_ORIGINS=* ollama serve &
```

---

## Quick commands personnalisées

Dans `config.yaml`, tu peux définir des raccourcis :

```yaml
quick_commands:
  analyse:
    type: exec
    command: python ~/scraper-signal-arnaques/scraper_signal_arnaques.py
  ids:
    type: exec
    command: python ~/scraper-signal-arnaques/collecter_ids.py
  proxies:
    type: exec
    command: python ~/scraper-signal-arnaques/proxy_finder.py
```

→ [[04 - Mémoire & Profil]] pour comprendre comment Hermes te retient
