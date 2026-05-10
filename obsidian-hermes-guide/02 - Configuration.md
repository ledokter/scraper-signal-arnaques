# 02 — Configuration
#hermes #configuration #config

← [[00 - Hermes MOC]]

---

## Les deux fichiers clés

| Fichier | Emplacement | Contenu |
|---------|-------------|---------|
| `config.yaml` | `~/.hermes/config.yaml` | Paramètres généraux (modèle, outils, affichage…) |
| `.env` | `~/.hermes/.env` | **Secrets** : clés API, tokens (ne jamais committer) |

---

## `config.yaml` complet annoté

```yaml
# ─── MODÈLE ────────────────────────────────────────────────
model:
  # Endpoint personnalisé (optionnel — pour OpenRouter, Ollama, etc.)
  base_url: "https://openrouter.ai/api/v1"
  # Modèle par défaut
  default: "anthropic/claude-sonnet-4-6"

# ─── OUTILS ────────────────────────────────────────────────
toolsets: ["all"]
# Ou sélectif :
# toolsets: ["terminal", "web", "file-io"]

# ─── TERMINAL ──────────────────────────────────────────────
terminal:
  backend: "local"      # local | docker | ssh
  cwd: "."              # Répertoire de travail par défaut
  timeout: 180          # Timeout en secondes

# ─── MÉMOIRE ───────────────────────────────────────────────
memory:
  memory_enabled: true
  user_profile_enabled: true

# ─── AFFICHAGE ─────────────────────────────────────────────
display:
  compact: false
  personality: "helpful"        # helpful | pirate | kawaii | concise…
  busy_input_mode: "interrupt"  # interrupt | queue | steer
  tool_preview_length: 0        # 0 = illimité

# ─── COMPRESSION DE CONTEXTE ───────────────────────────────
compression:
  enabled: true
  threshold: 0.50    # Compresse à 50% de la limite de contexte

# ─── COMMANDES RAPIDES ─────────────────────────────────────
quick_commands:
  status:
    type: exec
    command: systemctl status hermes-gateway
  scraper:
    type: exec
    command: cd ~/scraper-signal-arnaques && python lanceur.py --status
  gpu:
    type: exec
    command: nvidia-smi --query-gpu=utilization.gpu

# ─── MCP SERVERS ───────────────────────────────────────────
mcp_servers:
  github:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xxx"
  filesystem:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user0"]

# ─── CRON ──────────────────────────────────────────────────
cron:
  - name: "morning-briefing"
    schedule: "0 9 * * 1-5"
    prompt: "Donne-moi un bref résumé de ce que j'ai à faire aujourd'hui"
  - name: "scraper-check"
    schedule: "0 */6 * * *"
    prompt: "Vérifie que le scraper arnaques a bien tourné, signale les erreurs"
```

---

## `.env` — Clés API

```bash
# ~/.hermes/.env
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
OPENROUTER_API_KEY=sk-or-v1-...
GOOGLE_API_KEY=AIza...

# Optionnel — protection par mot de passe de l'UI web
HERMES_PASSWORD=monmotdepasse
```

> [!warning] Sécurité
> Ne jamais mettre `.env` dans git. Il contient tes clés API.

---

## Modifier la config en ligne de commande

```bash
# Changer le modèle
hermes config set model.default "anthropic/claude-opus-4-7"

# Changer le backend terminal
hermes config set terminal.backend docker

# Ajouter une clé API (va dans .env automatiquement)
hermes config set ANTHROPIC_API_KEY sk-ant-...

# Désactiver la mémoire
hermes config set memory.memory_enabled false
```

---

## Configuration de Hermes Workspace

Le fichier `.env` du workspace (`~/hermes-workspace/.env`) :

```bash
# URLs des services Hermes
HERMES_API_URL=http://127.0.0.1:8642
HERMES_DASHBOARD_URL=http://127.0.0.1:9119

# Auth si gateway sécurisé
HERMES_API_TOKEN=...

# Protection UI
HERMES_PASSWORD=...

# Déploiement derrière proxy
COOKIE_SECURE=1
TRUST_PROXY=1
```

---

## Providers LLM supportés

| Provider | Variable `.env` | Exemple de modèle |
|----------|-----------------|-------------------|
| Anthropic | `ANTHROPIC_API_KEY` | `claude-sonnet-4-6` |
| OpenAI | `OPENAI_API_KEY` | `gpt-4o` |
| OpenRouter | `OPENROUTER_API_KEY` | `google/gemini-flash-1.5` |
| Google | `GOOGLE_API_KEY` | `gemini-2.0-flash` |
| Ollama (local) | *(pas de clé)* | `llama3.2` |

### Utiliser Ollama (modèle local, gratuit)

```bash
# Lancer Ollama avec CORS activé
OLLAMA_ORIGINS=* ollama serve

# Dans config.yaml
model:
  base_url: "http://127.0.0.1:11434/v1"
  default: "llama3.2"
```

---

## Configuration des outils

```bash
hermes tools
```

Interface interactive pour activer/désactiver :
- `terminal` — Exécution de commandes shell
- `web` — Recherche + navigation web
- `file-io` — Lecture/écriture de fichiers
- `git` — Opérations git
- `image` — Analyse d'images

---

## Fichiers de contexte de projet

Hermes lit automatiquement ces fichiers dans le répertoire courant :

| Fichier | Rôle |
|---------|------|
| `.hermes.md` | Instructions spécifiques au projet |
| `AGENTS.md` | Instructions pour agents dans ce repo |
| `CLAUDE.md` | Compatible Claude Code |
| `SOUL.md` | Personnalité custom de l'agent |

> [!tip] Pour ton projet scraper
> Crée un `.hermes.md` dans `~/scraper-signal-arnaques/` :
> ```markdown
> # Contexte projet
> Ce projet scrape les signalements d'arnaques sur signal-arnaques.fr.
> Stack : Python, BeautifulSoup, CSV/JSON.
> Respecte la structure existante des fichiers arnaques_*.csv
> ```

→ [[03 - Commandes CLI]] pour la liste complète des commandes
