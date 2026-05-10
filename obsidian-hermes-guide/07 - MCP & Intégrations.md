# 07 — MCP & Intégrations
#hermes #mcp #intégrations #extensions

← [[00 - Hermes MOC]]

---

## C'est quoi le MCP ?

**Model Context Protocol** = standard ouvert pour connecter des services externes à un agent IA. Chaque serveur MCP expose des **outils** que Hermes utilise comme s'ils étaient natifs.

Hermes supporte :
- **Stdio** : commande locale (npx, python…)
- **HTTP** : endpoint distant
- **OAuth** : serveurs avec authentification

---

## Configuration dans `config.yaml`

```yaml
mcp_servers:
  # GitHub — Gérer ton repo scraper
  github:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xxx"

  # Filesystem — Accès élargi aux fichiers
  filesystem:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user0"]

  # Fetch web — Récupérer des pages web
  fetch:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-fetch"]

  # Brave Search — Recherche web
  brave:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-brave-search"]
    env:
      BRAVE_API_KEY: "BSA_xxx"

  # SQLite — Pour une future base de données d'arnaques
  sqlite:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-sqlite", "--db-path", "/home/user0/arnaques.db"]

  # Playwright — Scraping avancé avec browser
  playwright:
    command: npx
    args: ["-y", "@executeautomation/playwright-mcp-server"]
```

---

## Installation des serveurs MCP

```bash
# GitHub
npm install -g @modelcontextprotocol/server-github

# Filesystem
npm install -g @modelcontextprotocol/server-filesystem

# Fetch
npm install -g @modelcontextprotocol/server-fetch

# Playwright (browser automation)
npm install -g @executeautomation/playwright-mcp-server
```

---

## Plateformes de messagerie (Gateway)

Hermes peut recevoir et envoyer des messages sur **21+ plateformes** :

```bash
hermes gateway setup
```

### Telegram (recommandé pour usage mobile)

```bash
# 1. Créer un bot via @BotFather sur Telegram
# 2. Récupérer le token
hermes gateway setup
# → Choisir "Telegram"
# → Entrer le token du bot

# Démarrer
hermes gateway run
```

Une fois configuré, tu envoies un message à ton bot Telegram et Hermes répond depuis WSL2.

> [!example] Usage mobile
> Depuis ton téléphone :
> ```
> Toi: analyse arnaques_paypal.csv et dis-moi le top 3 des types d'arnaques
> Hermes: [analyse et répond directement dans Telegram]
> ```

### Discord

```bash
hermes gateway setup
# → Choisir "Discord"
# → Entrer le bot token Discord
# → Choisir le channel autorisé
```

### Email

```bash
hermes gateway setup
# → Choisir "Email"
# → Configurer SMTP/IMAP
```

---

## ACP — Intégration éditeurs

Hermes supporte le protocole **ACP** pour s'intégrer dans :
- **VS Code** — Extension disponible
- **Zed** — Plugin disponible
- **JetBrains** — Plugin disponible (PyCharm, etc.)

Cela permet d'utiliser Hermes directement dans ton éditeur de code, avec accès au contexte du projet ouvert.

---

## Providers LLM avancés

### OpenRouter (recommandé — accès à 200+ modèles)

```bash
hermes config set OPENROUTER_API_KEY sk-or-v1-xxx
hermes config set model.base_url "https://openrouter.ai/api/v1"
hermes config set model.default "google/gemini-flash-1.5"   # Rapide et économique
# ou
hermes config set model.default "anthropic/claude-sonnet-4-6"
```

### AWS Bedrock

```yaml
# config.yaml
model:
  provider: bedrock
  region: eu-west-1
  default: anthropic.claude-sonnet-4-6-v2
```

### Modèle local Ollama (100% gratuit, hors-ligne)

```bash
# Lancer Ollama
OLLAMA_ORIGINS=* ollama serve &
ollama pull llama3.2

# Config Hermes
hermes config set model.base_url "http://127.0.0.1:11434/v1"
hermes config set model.default "llama3.2"
```

---

## Intégration Voice

```bash
# Dans une session Hermes
/voice on       # Active l'écoute (Ctrl+B pour parler)
/voice tts      # Active la synthèse vocale des réponses
/voice off      # Désactiver

# Pré-requis : faster-whisper ou whisper installé
pip install faster-whisper
```

---

## Backends d'exécution

| Backend | Usage |
|---------|-------|
| `local` | Direct sur ta machine WSL2 (défaut) |
| `docker` | Isolation — sandboxe les exécutions |
| `ssh` | Exécuter sur une machine distante |
| `daytona` | Environnements cloud éphémères |
| `modal` | Calcul GPU serverless |

```bash
hermes config set terminal.backend docker    # Isolation
hermes config set terminal.backend local     # Revenir au local
```

→ [[08 - Automatisations]] pour les crons et le Swarm Mode
