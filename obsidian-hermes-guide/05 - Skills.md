# 05 — Skills
#hermes #skills #plugins #compétences

← [[00 - Hermes MOC]]

---

## C'est quoi un skill ?

Un **skill** est un plugin réutilisable qui ajoute des capacités à Hermes. L'agent peut :
- Installer des skills existants depuis le hub officiel (~684 disponibles)
- **Créer automatiquement ses propres skills** à partir de tâches répétées
- Utiliser tes skills via commandes `/nom-du-skill`

C'est la **mémoire procédurale** de Hermes : il apprend comment faire des choses et s'en souvient.

---

## Naviguer dans le hub de skills

```bash
hermes skills browse          # Interface interactive
hermes skills search python   # Rechercher par mot-clé
hermes skills search scraping
hermes skills search security
```

**Dans l'UI Workspace** : onglet **Skills** → parcourir les 684 skills avec filtres par catégorie.

---

## Catégories disponibles

| Catégorie | Nb | Exemples |
|-----------|----|---------|
| Développement | 74 | python-helper, code-review, git-workflow |
| Créativité | 69 | image-gen, diagram-maker, ascii-art |
| MLOps | 40 | model-eval, dataset-prep |
| Recherche | 39 | web-research, summarize |
| Sécurité | ~20 | osint, nmap-helper, vuln-scan |
| GitHub | ~15 | github-pr-workflow, issue-manager |
| DevOps | ~20 | docker-helper, k8s |
| Traduction | 24 | translate-fr, translate-multi |

---

## Installer un skill

```bash
# Chercher
hermes skills search web-scraping

# Installer (format: org/skills/nom)
hermes skills install nousresearch/skills/web-scraper
hermes skills install community/skills/python-debugger
hermes skills install nousresearch/skills/github-pr-workflow
```

---

## Utiliser un skill dans une session

Chaque skill installé devient une commande `/` :

```bash
# Lancer hermes avec skill préchargé
hermes -s web-scraper
hermes -s python-helper,github-pr-workflow

# Dans une session
/web-scraper scrape https://signal-arnaques.fr/arnaques?page=1
/github-pr-workflow crée une PR pour les nouvelles plateformes scraper
/translate-fr translate this error message to French
/summarize @~/scraper-signal-arnaques/arnaques_vinted.json
```

---

## Précharger des skills au démarrage

```bash
# One-shot avec skills
hermes chat -s python-helper -q "débogue ce code @./scraper_signal_arnaques.py"

# Session interactive avec skills
hermes -s web-scraper,python-helper
```

---

## Création automatique de skills

Hermes **crée des skills tout seul** quand il répète une tâche complexe. Par exemple :

1. Tu lui demandes plusieurs fois d'analyser tes CSV d'arnaques
2. Il crée automatiquement un skill `/analyse-arnaques`
3. La prochaine fois tu peux faire `/analyse-arnaques paypal`

Les skills créés sont dans : `~/.hermes/skills/`

---

## Créer manuellement un skill

Structure d'un skill (Python package) :

```
~/.hermes/skills/mon-skill/
├── SKILL.md          # Metadata et documentation
├── __init__.py       # Code du skill
└── tools.py          # Outils exposés à l'agent
```

**SKILL.md** :
```markdown
# mon-skill
description: Analyse les fichiers d'arnaques Signal-Arnaques
author: moi
version: 1.0.0

## Usage
/mon-skill <plateforme>

## Examples
/mon-skill paypal
/mon-skill vinted --format=rapport
```

**__init__.py** :
```python
def analyse_arnaques(plateforme: str, format: str = "summary") -> str:
    """Analyse les arnaques pour une plateforme donnée."""
    import json, os
    
    fichier = f"/home/user0/scraper-signal-arnaques/arnaques_{plateforme}.json"
    if not os.path.exists(fichier):
        return f"Fichier non trouvé : {fichier}"
    
    with open(fichier) as f:
        data = json.load(f)
    
    total = len(data)
    # ... analyse ...
    return f"Plateforme {plateforme}: {total} signalements"
```

---

## Lister et gérer tes skills

```bash
hermes skills list            # Voir tous les skills installés
hermes skills update          # Mettre à jour tous les skills
hermes skills remove nom      # Désinstaller un skill
```

---

## Skills recommandés pour ton usage

| Skill | Utilité pour toi |
|-------|-----------------|
| `python-helper` | Déboguer/améliorer tes scripts scraper |
| `web-scraper` | Aide pour le scraping avec BeautifulSoup/requests |
| `github-pr-workflow` | Gérer ton repo Git facilement |
| `translate-fr` | Traduire des erreurs/docs anglaises |
| `summarize` | Résumer rapidement tes fichiers JSON/CSV |
| `osint` | Enrichir les données d'arnaques |
| `code-review` | Review automatique de tes scripts |

→ [[06 - Hermes Workspace]] pour l'interface web complète
