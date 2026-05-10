# 06 — Hermes Workspace (Interface Web)
#hermes #workspace #ui #interface

← [[00 - Hermes MOC]]

---

## C'est quoi Hermes Workspace ?

**Hermes Workspace** est l'interface web de contrôle de ton agent. C'est un "command center" qui regroupe dans un seul browser :
- Chat avec l'agent
- Terminal intégré
- Explorateur de fichiers avec éditeur Monaco
- Gestion de la mémoire
- Navigateur de skills
- Dashboard multi-agents
- Catalogue MCP

**Accès** : `http://localhost:3000` (après lancement)

---

## Lancement

```bash
# Pré-requis : gateway + dashboard déjà lancés
hermes gateway run    # Terminal 1
hermes dashboard      # Terminal 2

# Lancer le workspace
cd ~/hermes-workspace && pnpm dev    # Terminal 3

# Tout en un
cd ~/hermes-workspace && pnpm start:all
```

---

## Les onglets

### 💬 Chat
- Conversation en temps réel avec streaming SSE
- Rendu des appels d'outils en live (tu vois ce que l'agent fait)
- Support markdown + coloration syntaxique
- Multi-sessions : changer de session sans perdre le contexte
- Syntaxe `@fichier` pour référencer du contenu

> [!example] Usage typique
> ```
> @~/scraper-signal-arnaques/arnaques_leboncoin.json
> Analyse les 20 derniers signalements et identifie les patterns
> ```

---

### 📁 Files (Fichiers)
- Explorateur de fichiers complet (arborescence)
- Éditeur **Monaco** (le même que VSCode)
- Lire, créer, éditer, sauvegarder des fichiers directement
- Pratique pour modifier tes scripts Python sans quitter le browser

> [!tip]
> Ouvre `~/scraper-signal-arnaques/scraper_signal_arnaques.py` directement ici.

---

### 🖥️ Terminal
- Terminal PTY complet dans le browser
- Cross-platform (Linux/macOS/WSL2)
- Exécuter tes commandes Python, git, etc.
- Accès à ton shell WSL2 Kali Linux

> [!note] WSL2
> Sur Windows, le terminal dans le dashboard (`:9119`) fonctionne uniquement en WSL2.

---

### 🧠 Memory (Mémoire)
- Voir le contenu de `MEMORY.md` et `USER.md`
- Éditeur markdown avec aperçu live
- Recherche dans les souvenirs
- Modifier la mémoire directement depuis l'UI

---

### ⚡ Skills
- Parcourir les **684 skills** disponibles
- Filtres par catégorie
- Badges d'origine (officiel, communauté)
- Installer d'un clic
- Marketplace intégré

---

### 📊 Operations Dashboard
- **Multi-agent management** : gérer plusieurs agents simultanément
- **Personas préconfiguréss** :
  - 🔭 Sage — Recherche et analyse
  - 📈 Trader — Finance et données
  - 🔨 Builder — Développement
  - ✍️ Scribe — Rédaction
  - ⚙️ Ops — DevOps et systèmes
- Dispatch de tâches par rôle sans configuration manuelle

> [!example] Pour ton projet
> Lance un **Builder** pour coder et un **Researcher** pour analyser les arnaques en parallèle.

---

### 🐝 Swarm Mode
- Pool de workers **tmux** persistant
- Agents en rotation sans perte de contexte
- Dispatch par rôle automatique
- Idéal pour traiter plusieurs plateformes d'arnaques en parallèle

```
Builder lane   → Améliore le code du scraper
Researcher lane → Analyse les nouvelles arnaques détectées
QA lane        → Vérifie la qualité des données exportées
```

---

### 🔌 MCP Catalog
- Liste de tous tes serveurs MCP connectés
- Marketplace de serveurs MCP
- Gérer les connexions (ajouter, supprimer, tester)

---

## Thèmes disponibles

| Thème | Description |
|-------|-------------|
| Hermes (défaut) | Orange/sombre |
| Nous | Violet/sombre |
| Bronze | Cuivré |
| Slate | Gris ardoise |
| Mono | Noir/blanc épuré |
| Variantes claires | Disponibles pour chaque thème |

---

## Installation PWA (Progressive Web App)

Tu peux **installer Hermes Workspace comme une app native** sur :
- Windows (Chrome/Edge) → icône dans la barre des tâches
- macOS → icône dans le Dock
- iPhone/iPad → Safari → "Sur l'écran d'accueil"
- Android → Chrome → "Installer l'application"

Puis avec **Tailscale** pour y accéder depuis n'importe où.

---

## Accès distant via Tailscale

```bash
# Sur le serveur WSL2
tailscale up

# Dans .env du workspace
HERMES_API_URL=http://100.x.x.x:8642
HERMES_DASHBOARD_URL=http://100.x.x.x:9119
HERMES_ALLOW_INSECURE_REMOTE=1

# Lancer le gateway sur 0.0.0.0
API_SERVER_HOST=0.0.0.0 hermes gateway run
```

→ [[07 - MCP & Intégrations]] pour connecter des services externes
