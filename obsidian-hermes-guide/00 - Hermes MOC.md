# Hermes Agent — Map of Content
#hermes #ia #agent #nous-research

> [!abstract] C'est quoi Hermes ?
> **Hermes Agent** est un agent IA autonome créé par **Nous Research**. Il tourne en local dans ton terminal WSL2 Kali Linux, apprend de tes habitudes, crée des compétences réutilisables, et est accessible depuis ton browser, Telegram, Discord, ou n'importe quelle autre plateforme de messagerie.
> 
> Ton instance tourne à : `\\wsl.localhost\kali-linux\home\user0\.hermes`

---

## 🗺️ Index des notes

| Note | Contenu |
|------|---------|
| [[01 - Installation & Démarrage]] | Installer Hermes + Hermes Workspace, premiers pas |
| [[02 - Configuration]] | `config.yaml`, `.env`, providers, outils |
| [[03 - Commandes CLI]] | Référence complète de toutes les commandes `hermes` |
| [[04 - Mémoire & Profil]] | `MEMORY.md`, `USER.md`, `SOUL.md` — comment Hermes te retient |
| [[05 - Skills]] | Installer, utiliser, créer des skills |
| [[06 - Hermes Workspace]] | L'interface web : chat, terminal, fichiers, mémoire |
| [[07 - MCP & Intégrations]] | Connecter des serveurs MCP externes |
| [[08 - Automatisations]] | Cron, délégation, Swarm Mode |
| [[09 - Cas d'usage — Scraping & Arnaques]] | Exemples concrets pour ton projet de scraping |

---

## 🏗️ Architecture globale

```
Toi (WSL2 / Browser / Telegram)
        │
        ▼
┌──────────────────────────────┐
│   Hermes Workspace  :3000    │  ← Interface web (optionnel)
└──────────────────┬───────────┘
                   │
        ┌──────────▼──────────┐
        │  Gateway API :8642   │  ← Cœur : chat, streaming, jobs
        └──────────┬───────────┘
                   │
        ┌──────────▼──────────┐
        │  Dashboard   :9119   │  ← Sessions, skills, config, MCP
        └──────────────────────┘
                   │
        ~/.hermes/             ← Données locales (mémoire, skills, config)
```

---

## ⚡ Démarrage rapide

```bash
# Terminal 1 — Lance le cerveau
hermes gateway run

# Terminal 2 — Lance le dashboard
hermes dashboard

# Terminal 3 — Lance l'UI web (si hermes-workspace installé)
cd ~/hermes-workspace && pnpm dev

# Ou simplement chatter en CLI
hermes
```

---

## 📁 Structure `~/.hermes`

```
~/.hermes/
├── config.yaml        # Configuration principale
├── .env               # Clés API (secrets)
├── MEMORY.md          # Mémoire globale de l'agent
├── USER.md            # Ton profil utilisateur
├── SOUL.md            # Personnalité de l'agent
├── memories/          # Mémoires par session
├── skills/            # Tes skills installés/créés
└── sessions/          # Historique des sessions
```

---

## 🔗 Ressources

- [GitHub hermes-workspace](https://github.com/outsourc-e/hermes-workspace)
- [Docs officielles Nous Research](https://hermes-agent.nousresearch.com/docs/)
- [Discord communauté](https://discord.gg/nousresearch)
