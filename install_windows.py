r"""
Installation de l'environnement Windows — Scraper signal-arnaques.com
======================================================================
Lance ce script UNE SEULE FOIS depuis PowerShell Windows :

    cd "C:\Users\user0\Documents\###MEGOBSI\MegaObs\Obsidian-Drop\Formation-anti-arnaques seniors"
    python install_windows.py

Il crée un venv Windows (.venv_win), installe les dépendances,
et télécharge Chromium pour Playwright.
"""

import subprocess
import sys
import venv
from pathlib import Path

HERE     = Path(__file__).parent
VENV_DIR = HERE / ".venv_win"
REQS     = ["playwright", "playwright-stealth"]


def run(*cmd, **kw):
    print(f"\n>>> {' '.join(str(c) for c in cmd)}")
    subprocess.run(list(cmd), check=True, **kw)


def main():
    print("=" * 60)
    print("  Installation Windows — Playwright + dépendances")
    print("=" * 60)

    # ── 1. Créer le venv Windows ──────────────────────────────────
    if VENV_DIR.exists():
        print(f"\n[✔] venv existant : {VENV_DIR}")
    else:
        print(f"\n[1] Création du venv dans : {VENV_DIR}")
        venv.create(str(VENV_DIR), with_pip=True)
        print("    OK")

    # Chemin vers le pip et python du venv Windows
    pip    = VENV_DIR / "Scripts" / "pip.exe"
    python = VENV_DIR / "Scripts" / "python.exe"

    if not pip.exists():
        print(f"\n[!] pip introuvable dans {pip}")
        print("    Vérifiez que Python Windows est correctement installé.")
        sys.exit(1)

    # ── 2. Mettre à jour pip ──────────────────────────────────────
    print("\n[2] Mise à jour de pip...")
    run(python, "-m", "pip", "install", "--upgrade", "pip", "--quiet")

    # ── 3. Installer les paquets ──────────────────────────────────
    print("\n[3] Installation des paquets...")
    for pkg in REQS:
        run(pip, "install", pkg, "--quiet")
        print(f"    {pkg} installé")

    # ── 4. Télécharger Chromium pour Playwright ───────────────────
    print("\n[4] Téléchargement de Chromium (peut prendre 1-2 min)...")
    run(python, "-m", "playwright", "install", "chromium")

    # ── 5. Résumé ─────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  Installation terminée !")
    print("=" * 60)
    print(r"""
Pour collecter les IDs depuis PowerShell Windows :

    .venv_win\Scripts\python.exe collecter_ids.py --tag vinted
    .venv_win\Scripts\python.exe collecter_ids.py --tag leboncoin

Puis depuis WSL2 Kali (venv active) :

    python scraper_signal_arnaques.py --detail --tag vinted
""")


if __name__ == "__main__":
    main()
