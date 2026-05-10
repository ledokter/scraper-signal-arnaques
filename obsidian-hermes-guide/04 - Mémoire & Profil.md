# 04 — Mémoire & Profil Utilisateur
#hermes #mémoire #memory #contexte

← [[00 - Hermes MOC]]

---

## Comment fonctionne la mémoire de Hermes

Hermes maintient une **boucle d'apprentissage fermée** : il mémorise tes préférences, ce que tu fais, comment tu travailles, et s'améliore entre les sessions. C'est ce qui le distingue d'un simple chatbot.

```
Session 1 → Hermes apprend tes habitudes
Session 2 → Il applique ce qu'il a retenu
Session 3 → Il affine encore plus son profil de toi
```

---

## Les fichiers de mémoire

### `MEMORY.md` — La mémoire de travail

Emplacement : `~/.hermes/MEMORY.md`

C'est le **journal de bord** de l'agent. Il y écrit :
- Les tâches accomplies
- Les décisions prises
- Les informations importantes à retenir
- Les erreurs rencontrées et solutions trouvées

> [!example] Exemple de contenu MEMORY.md
> ```markdown
> # Mémoire Hermes
> 
> ## Projet scraper arnaques
> - Le projet est dans ~/scraper-signal-arnaques/
> - lanceur.py est le point d'entrée principal
> - Les proxies se renouvellent via proxy_finder.py
> - Les données sont en CSV et JSON par plateforme
> - Signal-arnaques.fr nécessite rotation User-Agent (ua_rotation.py)
> 
> ## Préférences utilisateur
> - Préfère les réponses en français
> - Utilise VSCode + WSL2 Kali Linux
> - Environnement Python avec venv dans le projet
> ```

---

### `USER.md` — Ton profil personnel

Emplacement : `~/.hermes/USER.md`

Hermes construit progressivement un profil de **qui tu es** : tes compétences, ton niveau technique, tes préférences de communication, tes projets habituels.

> [!example] Exemple de USER.md
> ```markdown
> # Profil utilisateur
> 
> ## Identité
> - Développeur Python intermédiaire
> - Utilise WSL2 Kali Linux + Windows
> - Projets : scraping, cybersécurité, automatisation
> 
> ## Style de communication
> - Préfère les explications directes sans trop de rembourrage
> - Aime les exemples de code concrets
> - Répond en français
> 
> ## Outils habituels
> - VSCode, Python 3.11, BeautifulSoup, requests
> - Obsidian pour les notes
> - Git pour la gestion du code
> ```

---

### `SOUL.md` — La personnalité de l'agent

Emplacement : `~/.hermes/SOUL.md`

Définis le **caractère** de ton instance Hermes :

```markdown
# Soul — Mon agent Hermes

Tu es un assistant technique expert en Python, scraping web et cybersécurité.
Tu travailles principalement en français.
Tu es concis, précis, et tu fournis toujours des exemples de code.
Tu connais bien le projet scraper-signal-arnaques et ses contraintes.
Quand tu doutes, tu signales l'incertitude plutôt que d'inventer.
```

---

## Activer la mémoire

Dans `config.yaml` :

```yaml
memory:
  memory_enabled: true          # Active la mémoire globale
  user_profile_enabled: true    # Active le profil USER.md
```

Ou en ligne de commande :
```bash
hermes config set memory.memory_enabled true
hermes config set memory.user_profile_enabled true
```

---

## Providers de mémoire externe

Pour une mémoire plus puissante avec indexation vectorielle :

| Provider | Description |
|----------|-------------|
| **Honcho** | Mémoire long-terme avec recherche sémantique |
| **Mem0** | Stockage structuré de souvenirs |
| **OpenViking** | Mémoire épisodique |
| **Hindsight** | Apprentissage par rétroaction |

Configuration dans `config.yaml` :
```yaml
memory:
  provider: "honcho"
  honcho_api_key: "..."
```

---

## Fichiers de contexte de projet

Ces fichiers sont **lus automatiquement** quand Hermes démarre dans un répertoire :

```bash
~/scraper-signal-arnaques/.hermes.md   # Instructions projet
~/scraper-signal-arnaques/AGENTS.md    # Règles pour agents
~/scraper-signal-arnaques/CLAUDE.md    # Compatible Claude Code
```

> [!tip] Crée ton `.hermes.md` pour le scraper
> ```bash
> cat > ~/scraper-signal-arnaques/.hermes.md << 'EOF'
> # Projet : Scraper Signal-Arnaques
> 
> ## Structure
> - scraper_signal_arnaques.py : scraper principal
> - lanceur.py : point d'entrée avec options CLI
> - collecter_ids.py : collecte les IDs d'arnaques
> - proxy_finder.py : rotation de proxies
> - ua_rotation.py : rotation User-Agent
> - tag_manager.py : gestion des tags
> 
> ## Règles
> - Respecter les délais entre requêtes (rate limiting)
> - Toujours exporter en CSV ET JSON simultanément
> - Ne pas stocker de données personnelles identifiables
> - Fichiers nommés arnaques_<plateforme>.csv/.json
> 
> ## Environnement
> - Python 3.11, WSL2 Kali Linux
> - Toujours activer le venv avant d'exécuter
> EOF
> ```

---

## Voir et éditer la mémoire

### Via CLI
```bash
# Voir le contenu de MEMORY.md
cat ~/.hermes/MEMORY.md

# Éditer directement
nano ~/.hermes/MEMORY.md

# Voir le profil utilisateur
cat ~/.hermes/USER.md
```

### Via Hermes Workspace

Dans l'UI web (`http://localhost:3000`) → onglet **Memory** :
- Parcourir la mémoire avec un éditeur markdown
- Rechercher dans les souvenirs
- Éditer en live avec aperçu

---

## Syntaxe @-mention pour injecter du contexte

Dans une session, tu peux forcer Hermes à lire du contenu :

```
@~/.hermes/MEMORY.md qu'est-ce que tu te rappelles sur mon projet ?
@~/scraper-signal-arnaques/arnaques_paypal.csv analyse les tendances
@~/scraper-signal-arnaques/ parcours tous les fichiers et fais un résumé
```

→ [[05 - Skills]] pour étendre les capacités de Hermes
