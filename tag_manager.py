"""
Gestionnaire de tags — validation, découverte, rapport de couverture
--------------------------------------------------------------------
Fonctions :
  validate_tag(session, tag)  → True si le tag a des résultats sur le site
  discover_tags()             → tags trouvés dans les données scrapées (themes)
  coverage_report()           → état complet de chaque tag (scrapé/manquant/échecs)
  clean_invalid_tags(tags)    → retourne uniquement les tags valides
"""

import json
import logging
import re
import time
from pathlib import Path

logger = logging.getLogger("scraper")

HERE = Path(__file__).parent
BASE_URL = "https://www.signal-arnaques.com"

# Tags connus (source : lanceur.py)
KNOWN_TAGS = [
    "vinted","leboncoin","facebook-marketplace","seloger","pap","vivastreet",
    "lacentrale","la-centrale","amazon","cdiscount","fnac","darty","ebay",
    "aliexpress","shein","temu","wish","paypal","paylib","lydia","sumeria",
    "credit-agricole","bnp","societe-generale","caisse-epargne","lcl",
    "boursorama","orange-bank","revolut","wise","chronopost","colissimo",
    "laposte","mondial-relay","ups","dhl","fedex","dpd","gls","facebook",
    "instagram","whatsapp","telegram","snapchat","twitter","tiktok","linkedin",
    "netflix","spotify","disney","canal","prime","deezer","molotov",
    "impots","ameli","cpam","caf","urssaf","retraite","assurance-maladie",
    "antai","prefecture","service-public","edf","enedis","engie","sfr",
    "orange","free","bouygues","sosh","sms","email","telephone","phishing",
    "arnaque","escroquerie","crypto","bitcoin","investissement","emploi",
    "loterie","cagnotte",
]


# ──────────────────────────────────────────────────────────────
# Validation d'un tag
# ──────────────────────────────────────────────────────────────

def validate_tag(session, tag: str) -> tuple[bool, int]:
    """
    Vérifie que le tag existe et a des résultats sur signal-arnaques.com.
    Retourne (existe: bool, nb_résultats: int).
    """
    from bs4 import BeautifulSoup
    try:
        r = session.get(f"{BASE_URL}/tag/{tag}", timeout=15)
        if r.status_code != 200 or len(r.text) < 1000:
            return False, 0
        soup = BeautifulSoup(r.text, "html.parser")
        # Compter les arnaques dans la page
        rows = soup.select("table.scams-table tr.media")
        if not rows:
            # Vérifier s'il y a un message "aucun résultat"
            body = r.text.lower()
            if "aucun" in body or "no result" in body or "0 signal" in body:
                return False, 0
            # Page existe mais format différent — considérer valide
            return True, -1
        return True, len(rows)
    except Exception as e:
        logger.warning(f"validate_tag({tag}): {e}")
        return False, 0


def validate_all_tags(session, tags: list[str],
                      pause: float = 3.0) -> dict[str, tuple[bool, int]]:
    """Valide une liste de tags. Retourne {tag: (valide, nb)}."""
    results = {}
    for i, tag in enumerate(tags, 1):
        ok, nb = validate_tag(session, tag)
        results[tag] = (ok, nb)
        status = f"OK ({nb})" if ok and nb >= 0 else ("OK (non vide)" if ok else "INVALIDE")
        print(f"  [{i:>3}/{len(tags)}] {tag:<30} {status}")
        time.sleep(pause)
    return results


# ──────────────────────────────────────────────────────────────
# Découverte de nouveaux tags
# ──────────────────────────────────────────────────────────────

def discover_tags(data_dir: Path = HERE) -> dict[str, int]:
    """
    Scanne tous les arnaques_*.json et extrait les tags du champ 'themes'.
    Retourne {tag: nb_occurrences} pour les tags non encore connus.
    """
    from collections import Counter
    counter: Counter = Counter()
    known_lower = {t.lower() for t in KNOWN_TAGS}

    files = [f for f in data_dir.glob("arnaques_*.json")
             if "_listing" not in f.stem and "_partial" not in f.stem]

    for fp in files:
        try:
            records = json.loads(fp.read_text(encoding="utf-8"))
            for rec in records:
                themes = rec.get("themes") or rec.get("apercu") or ""
                # Extraire les tags (séparés par virgules ou espaces)
                parts = re.split(r"[,;\|]+", themes)
                for p in parts:
                    t = p.strip().lower()
                    t = re.sub(r"\s+", "-", t)
                    t = re.sub(r"[^a-z0-9\-]", "", t)
                    if len(t) >= 3 and t not in known_lower:
                        counter[t] += 1
        except Exception:
            pass

    # Trier par fréquence, filtrer bruit
    return {t: n for t, n in counter.most_common() if n >= 2}


# ──────────────────────────────────────────────────────────────
# Rapport de couverture
# ──────────────────────────────────────────────────────────────

def coverage_report(data_dir: Path = HERE) -> list[dict]:
    """
    Pour chaque tag qui a un fichier arnaques_*.json, retourne :
    {tag, fichier, total_scrapé, échecs, checkpoint_en_cours, dernière_maj}
    """
    report = []

    for fp in sorted(data_dir.glob("arnaques_*.json")):
        if "_listing" in fp.stem or "_partial" in fp.stem:
            continue
        tag = fp.stem.replace("arnaques_", "")
        try:
            records  = json.loads(fp.read_text(encoding="utf-8"))
            total    = len(records)
            ok_count = sum(1 for r in records if r.get("date"))
            fails    = total - ok_count
        except Exception:
            total = ok_count = fails = 0

        # Chercher checkpoint
        cp_path = data_dir / f"checkpoint_{tag}.json"
        cp_info = {}
        if cp_path.exists():
            try:
                cp_info = json.loads(cp_path.read_text(encoding="utf-8"))
            except Exception:
                pass

        stat = {
            "tag":            tag,
            "fichier":        fp.name,
            "total_scrapé":   total,
            "ok":             ok_count,
            "échecs":         fails,
            "en_cours":       bool(cp_info),
            "cp_done":        cp_info.get("done_count", 0),
            "cp_total":       cp_info.get("total_count", 0),
            "cp_failed":      len(cp_info.get("failed_ids", [])),
            "dernière_maj":   fp.stat().st_mtime,
        }
        report.append(stat)

    return sorted(report, key=lambda x: x["tag"])


def print_coverage_report(data_dir: Path = HERE):
    """Affiche le rapport dans le terminal."""
    rows = coverage_report(data_dir)
    if not rows:
        print("  Aucun fichier arnaques_*.json trouvé.")
        return

    total_ok   = sum(r["ok"] for r in rows)
    total_fail = sum(r["échecs"] for r in rows)
    total_all  = sum(r["total_scrapé"] for r in rows)

    print(f"\n{'Tag':<25} {'Scrapé':>8} {'OK':>6} {'Échecs':>8} {'En cours'}")
    print("─" * 65)
    for r in rows:
        en_cours = f"⏸ {r['cp_done']}/{r['cp_total']} (+{r['cp_failed']} échecs)" if r["en_cours"] else ""
        print(f"  {r['tag']:<23} {r['total_scrapé']:>8} {r['ok']:>6} {r['échecs']:>8}  {en_cours}")
    print("─" * 65)
    print(f"  {'TOTAL':<23} {total_all:>8} {total_ok:>6} {total_fail:>8}")
    print()


# ──────────────────────────────────────────────────────────────
# CLI standalone
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse, sys, io
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(description="Gestionnaire de tags signal-arnaques.com")
    ap.add_argument("command", choices=["report", "discover", "validate"],
                    help="report=couverture | discover=nouveaux tags | validate=vérifier les tags")
    ap.add_argument("--tags", nargs="*", help="Tags à valider (défaut: tous les tags connus)")
    args = ap.parse_args()

    if args.command == "report":
        print_coverage_report()

    elif args.command == "discover":
        print("\nRecherche de nouveaux tags dans les données scrapées...\n")
        new_tags = discover_tags()
        if new_tags:
            print(f"  {len(new_tags)} tags potentiels trouvés :\n")
            for t, n in list(new_tags.items())[:50]:
                print(f"  {t:<35} ({n} occurrences)")
        else:
            print("  Aucun nouveau tag détecté.")

    elif args.command == "validate":
        import curl_cffi.requests as cffi_req
        from ua_rotation import get_ua_string
        tags_to_check = args.tags or KNOWN_TAGS
        print(f"\nValidation de {len(tags_to_check)} tags...\n")
        s = cffi_req.Session(impersonate="chrome124")
        s.headers["User-Agent"] = get_ua_string()
        results = validate_all_tags(s, tags_to_check)
        invalid = [t for t, (ok, _) in results.items() if not ok]
        print(f"\n  Invalides ({len(invalid)}) : {', '.join(invalid) or 'aucun'}")
