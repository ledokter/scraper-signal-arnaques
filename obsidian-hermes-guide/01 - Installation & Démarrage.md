# 01 — Installation & Démarrage
#hermes #installation #wsl2

← [[00 - Hermes MOC]]

---

## Installation de Hermes Agent

### Option 1 — Installation automatique (recommandée, 60 secondes)

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

Fonctionne sur : Linux, macOS, **WSL2**, Windows natif (bêta), Android (Termux)

> [!success] Ce que ça fait
> - Installe `hermes` dans ton PATH
> - Crée `~/.hermes/` avec la structure de base
> - Lance le wizard de configuration interactif

---

### Option 2 — Installation avec Hermes Workspace (UI web)

```bash
curl -fsSL https://raw.githubusercontent.com/outsourc-e/hermes-workspace/main/install.sh | bash
```

Installe **les deux** : Hermes Agent + l'interface web sur `:3000`

---

### Option 3 — Attacher Hermes Workspace à un Hermes déjà installé

Si tu as déjà Hermes Agent installé :

```bash
git clone https://github.com/outsourc-e/hermes-workspace.git ~/hermes-workspace
cd ~/hermes-workspace
pnpm install
cp .env.example .env

# Configurer les URLs dans .env
echo 'HERMES_API_URL=http://127.0.0.1:8642' >> .env
echo 'HERMES_DASHBOARD_URL=http://127.0.0.1:9119' >> .env

pnpm dev
```

> [!warning] Prérequis
> - Node.js 22+
> - pnpm (`npm install -g pnpm`)

---

### Option 4 — Docker (tout-en-un)

```bash
git clone https://github.com/outsourc-e/hermes-workspace.git
cd hermes-workspace
cp .env.example .env
# Ajouter ta clé API dans .env (ex: ANTHROPIC_API_KEY=sk-ant-...)
docker compose up
```

Accès sur `http://localhost:3000`

---

## Configuration initiale

Après installation, lance le wizard :

```bash
hermes setup
```

Il te guide pour :
1. Choisir ton provider LLM (Anthropic, OpenAI, OpenRouter…)
2. Entrer ta clé API
3. Choisir le modèle par défaut
4. Activer/désactiver les outils

### Choisir son modèle

```bash
hermes model
```

Interface interactive pour changer de provider et modèle à tout moment.

**Recommandation pour débuter :**
- Budget : `openrouter` → `google/gemini-flash-1.5` (rapide et pas cher)
- Qualité : `anthropic` → `claude-sonnet-4-6` (optimal équilibre)
- Maximum : `anthropic` → `claude-opus-4-7` (le plus puissant)

---

## Premier lancement

### Mode terminal simple

```bash
hermes
```

Lance une session interactive. Tape ta question, Hermes répond.

```bash
hermes chat -q "Résume les fichiers Python de mon projet"
```

Mode one-shot : une question, une réponse, puis quitte.

### Vérifier que tout fonctionne

```bash
hermes doctor
```

Diagnostique les dépendances manquantes, les clés API, les services.

```bash
hermes version
hermes update      # Mettre à jour
```

---

## Lancer les 3 services

```bash
# Terminal 1
hermes gateway run

# Terminal 2
hermes dashboard

# Terminal 3 (si workspace installé)
cd ~/hermes-workspace && pnpm dev
# → Ouvre http://localhost:3000 dans ton browser
```

### Vérification de santé

```bash
curl http://127.0.0.1:8642/health
# → {"status":"ok"}

curl http://127.0.0.1:9119/api/status
# → Dashboard health
```

---

## Installation en tant que service système

Pour que Hermes démarre automatiquement :

```bash
hermes gateway install    # Installe comme service systemd
hermes gateway start
hermes gateway status
```

---

## Ton installation actuelle

Tes données Hermes sont dans :
```
\\wsl.localhost\kali-linux\home\user0\.hermes
```

Soit en WSL2 :
```bash
ls ~/.hermes/
```

→ [[02 - Configuration]] pour configurer ton `config.yaml`
