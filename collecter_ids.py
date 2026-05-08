"""
ETAPE 1 — Collecte des IDs d'arnaques via Google CSE (ouvre Chrome)
--------------------------------------------------------------------
Lance ce script DEPUIS POWERSHELL (pas depuis Claude Code).
Il ouvre un vrai Chrome, parcourt toutes les pages de résultats
et sauvegarde les IDs dans un fichier JSON.

Usage :
    python collecter_ids.py                    # tag vinted
    python collecter_ids.py --tag leboncoin    # autre tag
    python collecter_ids.py --tag paypal
    python collecter_ids.py --tag amazon

Une fois terminé, lance le scraper principal :
    python scraper_signal_arnaques.py --detail --tag vinted
"""

import argparse
import io
import json
import re
import sys
import time
from pathlib import Path

# Force UTF-8 sur la console Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE_URL = "https://www.signal-arnaques.com"


def collect_ids(tag: str) -> list[str]:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

    search_url = f"{BASE_URL}/tag/{tag}?q={tag}"
    all_ids: list[str] = []
    seen: set[str] = set()

    print(f"  Ouverture de Chrome sur : {search_url}")
    print("  (Une fenetre Chrome va s'ouvrir — ne la fermez pas.)\n")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = browser.new_page(
            locale="fr-FR",
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        page.goto(search_url, wait_until="domcontentloaded", timeout=30000)

        # Fermer le bandeau cookies si present
        try:
            for txt in ["Refuser", "Tout refuser", "Accepter"]:
                btn = page.get_by_role("button", name=re.compile(txt, re.I))
                if btn.is_visible(timeout=2000):
                    btn.click()
                    break
        except Exception:
            pass

        # Attendre les resultats Google CSE
        print("  Attente des resultats CSE...", end="", flush=True)
        try:
            page.wait_for_selector(".gsc-cursor-page", timeout=15000)
            print(" OK")
        except PWTimeout:
            print(" TIMEOUT — verifiez que la page a charge correctement.")
            browser.close()
            return []

        def collect_current_page() -> list[str]:
            links = page.query_selector_all('.gsc-result a[href*="/scam/view/"]')
            ids = []
            for a in links:
                href = a.get_attribute("href") or ""
                m = re.search(r"/scam/view/(\d+)", href)
                if m and m.group(1) not in seen:
                    seen.add(m.group(1))
                    ids.append(m.group(1))
            return ids

        nb_pages = len(page.query_selector_all(".gsc-cursor-page"))
        print(f"  {nb_pages} pages de resultats detectees.\n")

        for p in range(1, nb_pages + 1):
            # Cliquer sur la page p
            try:
                cursor_pages = page.query_selector_all(".gsc-cursor-page")
                target = next(
                    (el for el in cursor_pages if el.inner_text().strip() == str(p)),
                    None,
                )
                if target:
                    target.click()
                    time.sleep(2.5)
            except Exception:
                pass

            new_ids = collect_current_page()
            all_ids.extend(new_ids)
            print(f"  Page {p:2d}/{nb_pages} : {len(new_ids):2d} nouveaux IDs"
                  f"  (total : {len(all_ids)})")

        browser.close()

    return all_ids


def main():
    ap = argparse.ArgumentParser(description="Collecte d'IDs d'arnaques via Chrome")
    ap.add_argument("--tag", default="vinted",
                    help="Tag a rechercher (defaut: vinted)")
    args = ap.parse_args()

    tag = args.tag.lower().strip()
    out_file = Path(f"ids_{tag}.json")

    print(f"\n=== Collecte des IDs — tag : «{tag}» ===\n")

    ids = collect_ids(tag)

    if not ids:
        print("\nAucun ID collecte. Verifiez que Chrome a pu charger la page.")
        sys.exit(1)

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(ids, f, ensure_ascii=False, indent=2)

    print(f"\n{len(ids)} IDs sauvegardes dans : {out_file.resolve()}")
    print(f"\nLancez maintenant :")
    print(f"  python scraper_signal_arnaques.py --detail --tag {tag}\n")


if __name__ == "__main__":
    main()
