"""
Scraper pour signal-arnaques.com — par tag (vinted, leboncoin, paypal…)
------------------------------------------------------------------------
USAGE :
  python scraper_signal_arnaques.py                               # vinted, mode rapide
  python scraper_signal_arnaques.py --tag leboncoin
  python scraper_signal_arnaques.py --detail                      # données complètes
  python scraper_signal_arnaques.py --detail --max 50
  python scraper_signal_arnaques.py --detail --resume             # reprendre un scrape interrompu
  python scraper_signal_arnaques.py --detail --debug              # logs détaillés dans logs/
  python scraper_signal_arnaques.py --detail --delay 15 40        # délai 15-40s entre requêtes
  python scraper_signal_arnaques.py --detail --delay 30 60        # mode très lent (recommandé si 1015)

SORTIES :
  arnaques_<tag>_listing.json / .csv   — top 10 (mode rapide)
  arnaques_<tag>.json / .csv           — données complètes (--detail)
  checkpoint_<tag>.json                — point de reprise automatique
  logs/debug_<tag>_<datetime>.log      — logs debug (--debug)

CLOUDFLARE :
  Error 1015 (rate limit) : le scraper attend automatiquement 90s avant retry.
  Ban complet              : checkpoint sauvegardé, changez d'IP puis --resume.
"""

import argparse
import csv
import io
import json
import logging
import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup
import curl_cffi.requests as cffi_req

# Force UTF-8 sur la console Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE_URL = "https://www.signal-arnaques.com"
CSE_CX   = "005578480640153127982:bfu2riqgbin"

# Phrases indiquant un rate-limit temporaire (Error 1015) — attendre puis retry
RATELIMIT_PHRASES = [
    "Error 1015",
    "rate limited",
    "You are being rate limited",
    "1015",
]

# Phrases indiquant un ban Cloudflare complet — checkpoint + exit 2
BAN_PHRASES = [
    "Sorry, you have been blocked",
    "Access denied",
    "Enable JavaScript and cookies",
    "cf-error-details",
    "Attention Required! | Cloudflare",
]
BAN_CONSECUTIVE_THRESHOLD = 3  # bans d'affilée avant d'arrêter

# Délais par défaut entre requêtes (secondes) — augmentez si vous avez des 1015
DEFAULT_DELAY_LO = 10.0
DEFAULT_DELAY_HI = 25.0

logger = logging.getLogger("scraper")


# ──────────────────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────────────────

def setup_logging(tag: str, debug: bool):
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s",
                            datefmt="%H:%M:%S")
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG if debug else logging.INFO)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    if debug:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
        fh  = logging.FileHandler(log_dir / f"debug_{tag}_{ts}.log",
                                  encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(fmt)
        logger.addHandler(fh)
        logger.debug(f"Log fichier ouvert : logs/debug_{tag}_{ts}.log")


# ──────────────────────────────────────────────────────────
# Checkpoint (reprise)
# ──────────────────────────────────────────────────────────

def checkpoint_path(tag: str) -> Path:
    return Path(f"checkpoint_{tag}.json")


def load_checkpoint(tag: str) -> dict | None:
    cp = checkpoint_path(tag)
    if cp.exists():
        try:
            return json.loads(cp.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def save_checkpoint(tag: str, all_ids: list, done_ids: set,
                    started_at: str, details: list):
    stem    = f"arnaques_{tag}"
    partial = Path(f"{stem}_partial.json")
    if details:
        with open(partial, "w", encoding="utf-8") as f:
            json.dump(details, f, ensure_ascii=False, indent=2)

    cp = {
        "tag":          tag,
        "all_ids":      all_ids,
        "done_ids":     sorted(done_ids),
        "started_at":   started_at,
        "last_updated": datetime.now().isoformat(timespec="seconds"),
        "done_count":   len(done_ids),
        "total_count":  len(all_ids),
        "partial_file": str(partial) if details else "",
    }
    checkpoint_path(tag).write_text(
        json.dumps(cp, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    logger.debug(f"Checkpoint sauvegardé : {len(done_ids)}/{len(all_ids)}")


def delete_checkpoint(tag: str):
    cp = checkpoint_path(tag)
    if cp.exists():
        cp.unlink()
    partial = Path(f"arnaques_{tag}_partial.json")
    if partial.exists():
        partial.unlink()


# ──────────────────────────────────────────────────────────
# Utilitaires
# ──────────────────────────────────────────────────────────

def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()

# Délais configurables via --delay (modifiés dans main())
_DELAY_LO = DEFAULT_DELAY_LO
_DELAY_HI = DEFAULT_DELAY_HI

def pause(lo: float | None = None, hi: float | None = None):
    t = random.uniform(lo or _DELAY_LO, hi or _DELAY_HI)
    logger.debug(f"Pause {t:.1f}s")
    time.sleep(t)

def is_ratelimited(html: str) -> bool:
    return any(p in html for p in RATELIMIT_PHRASES)

def is_banned(html: str) -> bool:
    return any(p in html for p in BAN_PHRASES)


# ──────────────────────────────────────────────────────────
# Session HTTP curl_cffi
# ──────────────────────────────────────────────────────────

# Profils d'impersonation à rotation
_IMPERSONATE_PROFILES = [
    "chrome124", "chrome123", "chrome120", "chrome119",
    "chrome116", "chrome110",
]
_profile_idx = 0

def make_session() -> cffi_req.Session:
    global _profile_idx
    profile = _IMPERSONATE_PROFILES[_profile_idx % len(_IMPERSONATE_PROFILES)]
    _profile_idx += 1
    logger.debug(f"Création session curl_cffi  profil={profile}")
    s = cffi_req.Session(impersonate=profile)
    s.headers.update({
        "Accept":             "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language":    "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding":    "gzip, deflate, br",
        "Cache-Control":      "max-age=0",
        "Sec-Fetch-Dest":     "document",
        "Sec-Fetch-Mode":     "navigate",
        "Sec-Fetch-Site":     "none",
        "Sec-Fetch-User":     "?1",
        "Upgrade-Insecure-Requests": "1",
        "Referer":            BASE_URL + "/",
    })
    logger.debug(f"Warm-up GET {BASE_URL}")
    r = s.get(BASE_URL, timeout=20)
    logger.debug(f"Warm-up -> HTTP {r.status_code}, {len(r.text)} chars")
    time.sleep(random.uniform(2, 4))
    return s


def get_html(session, url: str, retries=3) -> str:
    for attempt in range(retries):
        try:
            logger.debug(f"GET {url}")
            r = session.get(url, timeout=25)
            logger.debug(f"  -> HTTP {r.status_code}, {len(r.text)} chars")

            if r.status_code == 200 and len(r.text) > 3000:
                # Rate-limit 1015 dans le corps de la réponse
                if is_ratelimited(r.text):
                    wait = 90 + attempt * 60
                    logger.warning(f"  -> Rate limit 1015 — pause {wait}s avant retry {attempt+2}/{retries}")
                    print(f"      [1015] Rate limit Cloudflare — attente {wait}s avant retry {attempt+2}/{retries}…")
                    time.sleep(wait)
                    continue
                if is_banned(r.text):
                    logger.warning(f"  -> BAN détecté (contenu Cloudflare)")
                    return r.text  # retourne pour que l'appelant gère
                return r.text

            # HTTP 429 = Too Many Requests
            if r.status_code == 429:
                wait = 90 + attempt * 60
                logger.warning(f"  [HTTP 429] Too Many Requests — pause {wait}s")
                print(f"      [429] Too Many Requests — attente {wait}s avant retry {attempt+2}/{retries}…")
                time.sleep(wait)
                continue

            wait = 10 + attempt * 20
            logger.warning(f"  [HTTP {r.status_code}] — retry {attempt+2}/{retries} dans {wait}s")
            print(f"      [!] HTTP {r.status_code} — attente {wait}s avant retry {attempt+2}/{retries}…")
            time.sleep(wait)

        except Exception as e:
            wait = 10 + attempt * 20
            logger.error(f"  [Exception] {e.__class__.__name__}: {e}")
            print(f"      [!] Erreur réseau : {e} — retry {attempt+2}/{retries} dans {wait}s")
            time.sleep(wait)

    logger.error(f"Échec définitif après {retries} tentatives : {url}")
    return ""


# ──────────────────────────────────────────────────────────
# Parsers HTML
# ──────────────────────────────────────────────────────────

def parse_listing_page(html: str) -> list[dict]:
    soup  = BeautifulSoup(html, "html.parser")
    seen  = set()
    items = []
    for row in soup.select("table.scams-table tr.media"):
        link = row.select_one("a.a-scam-title")
        if not link:
            continue
        path = link.get("href", "")
        m = re.search(r"/scam/view/(\d+)", path)
        if not m:
            continue
        sid = m.group(1)
        if sid in seen:
            continue
        seen.add(sid)
        title   = row.select_one(".last-scam-title")
        cat     = row.select_one(".type-label")
        comment = row.select_one(".lastScam-comment-text")
        img     = row.select_one("img.media-object")
        items.append({
            "id":        sid,
            "url":       BASE_URL + path if path.startswith("/") else path,
            "titre":     clean(title.get_text(" ") if title else ""),
            "categorie": clean(cat.get_text() if cat else "").lstrip("> "),
            "apercu":    clean(comment.get_text(" ") if comment else ""),
            "image":     img.get("src", "") if img else "",
        })
    logger.debug(f"Listing parsé : {len(items)} entrées")
    return items


def parse_detail_page(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    heading   = soup.select_one("h1, h2")
    statut    = clean(heading.get_text() if heading else "")
    cat_el    = soup.select_one("a[href*='/cat/']")
    categorie = clean(cat_el.get_text() if cat_el else "")

    title_tag = soup.find("title")
    nb_signal = ""
    if title_tag:
        m = re.search(r"(\d+)\s+signalement", title_tag.get_text())
        nb_signal = m.group(1) if m else ""

    fields: dict[str, str] = {}
    for tr in soup.find_all("tr"):
        th = tr.find("th")
        td = tr.find("td")
        if th and td:
            lbl = clean(th.get_text())
            val = clean(td.get_text(" "))
            val = re.sub(r"\.[a-z]+\{[^}]+\}", "", val).strip()
            fields[lbl] = val

    tags: list[str] = []
    seen_t: set[str] = set()
    for a in soup.select("a[href*='/tag/'], .badge"):
        t = clean(a.get_text())
        if t and t not in seen_t:
            seen_t.add(t)
            tags.append(t)

    url_arn = fields.get("Url / Site internet", "")
    url_arn = re.split(r"\s", url_arn)[0] if url_arn else ""
    m_id    = re.search(r"/scam/view/(\d+)", url)

    return {
        "id":              m_id.group(1) if m_id else "",
        "url":             url,
        "statut":          statut,
        "categorie":       categorie or fields.get("Categorie", ""),
        "nb_signalements": nb_signal,
        "date":            fields.get("Date", ""),
        "email":           fields.get("Email", ""),
        "pseudonyme":      fields.get("Pseudonyme utilise", "") or fields.get("Pseudonyme utilisé", ""),
        "url_arnaque":     url_arn,
        "contenu":         fields.get("Contenu de l'arnaque", ""),
        "commentaire":     fields.get("Commentaire / Explications", ""),
        "themes":          ", ".join(tags),
    }


# ──────────────────────────────────────────────────────────
# Collecte IDs via Playwright
# ──────────────────────────────────────────────────────────

def collect_cse_ids_via_browser(tag: str, headless: bool) -> list[str]:
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    except ImportError:
        logger.error("playwright non installé — pip install playwright && playwright install chromium")
        return []

    logger.info(f"Ouverture navigateur {'headless' if headless else 'visible'}…")
    all_ids: list[str] = []
    seen: set[str] = set()

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        page = browser.new_page(
            locale="fr-FR",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        search_url = f"{BASE_URL}/tag/{tag}?q={tag}"
        logger.debug(f"Navigation -> {search_url}")
        page.goto(search_url, wait_until="domcontentloaded", timeout=30000)

        try:
            btn = page.locator("button:has-text('Refuser'), button:has-text('Accepter')").first
            if btn.is_visible(timeout=3000):
                btn.click()
                time.sleep(0.5)
        except Exception:
            pass

        try:
            page.wait_for_selector(".gsc-cursor-page", timeout=12000)
        except PWTimeout:
            logger.error("Les résultats CSE n'ont pas chargé.")
            browser.close()
            return []

        nb_pages = page.evaluate("document.querySelectorAll('.gsc-cursor-page').length")
        logger.info(f"{nb_pages} pages CSE détectées.")

        def collect_page_ids():
            try:
                ids = page.evaluate("""
                    () => [...new Set(
                      [...document.querySelectorAll('.gsc-result a[href*="/scam/view/"]')]
                      .map(a => { const m = a.href.match(/\\/scam\\/view\\/(\\d+)/); return m ? m[1] : null; })
                      .filter(Boolean)
                    )]
                """)
                return ids or []
            except Exception:
                return []

        for p in range(1, nb_pages + 1):
            try:
                page.evaluate(f"""
                    (() => {{
                        const btn = [...document.querySelectorAll('.gsc-cursor-page')]
                            .find(el => el.textContent.trim() === '{p}');
                        if (btn) btn.click();
                    }})()
                """)
                time.sleep(2.5)
            except Exception as e:
                logger.warning(f"Page {p} — navigation impossible ({e.__class__.__name__}), arrêt.")
                break

            try:
                ids = collect_page_ids()
            except Exception:
                logger.warning(f"Page {p} — browser fermé, {len(all_ids)} IDs conservés.")
                break

            new = [i for i in ids if i not in seen]
            seen.update(new)
            all_ids.extend(new)
            logger.info(f"Page CSE {p:2d}/{nb_pages}: {len(new):2d} nouveaux IDs (total: {len(all_ids)})")

        try:
            browser.close()
        except Exception:
            pass

    return all_ids


# ──────────────────────────────────────────────────────────
# Export JSON + CSV
# ──────────────────────────────────────────────────────────

DETAIL_FIELDS  = ["id", "url", "statut", "categorie", "nb_signalements",
                  "date", "email", "pseudonyme", "url_arnaque",
                  "contenu", "commentaire", "themes"]
LISTING_FIELDS = ["id", "url", "titre", "categorie", "apercu", "image"]


def save(data: list[dict], stem: str, fields: list[str]):
    json_path = Path(f"{stem}.json")
    csv_path  = Path(f"{stem}.csv")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        csv.DictWriter(f, fieldnames=fields, extrasaction="ignore").writeheader()
        csv.DictWriter(f, fieldnames=fields, extrasaction="ignore").writerows(data)
    logger.info(f"JSON -> {json_path.resolve()}")
    logger.info(f"CSV  -> {csv_path.resolve()}")


# ──────────────────────────────────────────────────────────
# Point d'entrée
# ──────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Scraper signal-arnaques.com",
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    ap.add_argument("--tag",      default="vinted")
    ap.add_argument("--detail",   action="store_true")
    ap.add_argument("--max",      type=int, default=0)
    ap.add_argument("--headless", action="store_true")
    ap.add_argument("--resume",   action="store_true",
                    help="Reprendre un scrape interrompu depuis le checkpoint")
    ap.add_argument("--debug",    action="store_true", default=True,
                    help="Logs détaillés (console + fichier logs/debug_*.log) — actif par défaut")
    ap.add_argument("--delay",    type=float, nargs=2,
                    metavar=("MIN", "MAX"),
                    default=[DEFAULT_DELAY_LO, DEFAULT_DELAY_HI],
                    help=f"Délai min/max entre requêtes en secondes "
                         f"(défaut: {DEFAULT_DELAY_LO} {DEFAULT_DELAY_HI}). "
                         f"Augmentez si vous avez des erreurs 1015.")
    args = ap.parse_args()

    tag  = args.tag.lower().strip()
    stem = f"arnaques_{tag}"
    setup_logging(tag, args.debug)

    # Appliquer les délais configurés
    global _DELAY_LO, _DELAY_HI
    _DELAY_LO, _DELAY_HI = args.delay[0], args.delay[1]
    logger.info(f"Délais entre requêtes : {_DELAY_LO:.0f}–{_DELAY_HI:.0f}s")

    print(f"\n=== Scraper signal-arnaques.com  |  tag: «{tag}» ===\n")

    # ── Session HTTP ───────────────────────────────────────
    logger.info("Démarrage session HTTP (warm-up Cloudflare)...")
    session = make_session()

    # ── 1. Listing tag ─────────────────────────────────────
    logger.info(f"[1] Listing /tag/{tag}...")
    listing_html = get_html(session, f"{BASE_URL}/tag/{tag}")
    listing      = parse_listing_page(listing_html)
    logger.info(f"    {len(listing)} arnaques dans le listing.")

    if not args.detail:
        print()
        save(listing, stem + "_listing", LISTING_FIELDS)
        print(f"\nMode rapide : {len(listing)} arnaques sauvegardées.")
        print(f"-> Relancez avec --detail pour les données complètes.\n")
        return

    # ── 2. Collecte des IDs ────────────────────────────────
    ids_file    = Path(f"ids_{tag}.json")
    listing_ids = [it["id"] for it in listing]

    if ids_file.exists():
        logger.info(f"[2] Lecture des IDs depuis {ids_file}...")
        with open(ids_file, encoding="utf-8") as f:
            cse_ids = json.load(f)
        logger.info(f"    {len(cse_ids)} IDs chargés depuis le fichier.")
    else:
        logger.info(f"[2] Collecte des IDs via Google CSE (navigateur)...")
        logger.info(f"    Conseil : lancez d'abord  python collecter_ids.py --tag {tag}")
        cse_ids = collect_cse_ids_via_browser(tag, headless=args.headless)

    all_ids = list(dict.fromkeys(cse_ids + listing_ids))
    logger.info(f"    {len(all_ids)} IDs uniques collectés.")

    if args.max > 0:
        all_ids = all_ids[:args.max]
        logger.info(f"    Limité à {len(all_ids)} arnaques (--max {args.max}).")

    # ── 3. Reprise depuis checkpoint ───────────────────────
    details     = []
    done_ids    = set()
    started_at  = datetime.now().isoformat(timespec="seconds")

    if args.resume:
        cp = load_checkpoint(tag)
        if cp:
            done_ids   = set(cp["done_ids"])
            started_at = cp.get("started_at", started_at)
            # Fusionner les IDs du checkpoint avec ceux récents
            all_ids = list(dict.fromkeys(cp["all_ids"] + all_ids))
            partial = Path(f"{stem}_partial.json")
            if partial.exists():
                try:
                    details = json.loads(partial.read_text(encoding="utf-8"))
                except Exception:
                    details = []
            logger.info(f"[REPRISE] Checkpoint trouvé : {len(done_ids)}/{len(cp['all_ids'])} déjà traités.")
            print(f"  [REPRISE] {len(done_ids)} IDs déjà traités, "
                  f"{len(all_ids) - len(done_ids)} restants.\n")
        else:
            logger.warning("[REPRISE] Aucun checkpoint trouvé, démarrage normal.")
            print("  [REPRISE] Aucun checkpoint trouvé — démarrage normal.\n")

    remaining = [sid for sid in all_ids if sid not in done_ids]
    logger.info(f"[3] Scraping de {len(remaining)} pages de détail"
                f" ({len(done_ids)} déjà faits)...\n")
    print(f"\n[3] Scraping des {len(remaining)} pages de détail...\n")

    errors          = 0
    consecutive_ban = 0

    for i, sid in enumerate(remaining, 1):
        url  = f"{BASE_URL}/scam/view/{sid}"
        html = get_html(session, url)

        # ── Détection ban ──────────────────────────────────
        if html and is_banned(html):
            consecutive_ban += 1
            logger.warning(f"  BAN détecté ({consecutive_ban}/{BAN_CONSECUTIVE_THRESHOLD})")
            print(f"  [BAN {consecutive_ban}/{BAN_CONSECUTIVE_THRESHOLD}] Cloudflare a bloqué l'IP.")
            if consecutive_ban >= BAN_CONSECUTIVE_THRESHOLD:
                save_checkpoint(tag, all_ids, done_ids, started_at, details)
                save(details, stem + "_partial", DETAIL_FIELDS)
                print(f"\n[BAN_DETECTED]")
                print(f"  Trop de blocages consécutifs.")
                print(f"  Checkpoint sauvegardé : {len(done_ids)}/{len(all_ids)} traités.")
                print(f"  -> Changez d'IP (VPN), puis relancez :")
                print(f"     python scraper_signal_arnaques.py --detail --tag {tag} --resume\n")
                sys.exit(2)
            pause(15, 25)
            continue
        else:
            consecutive_ban = 0

        if not html:
            logger.error(f"  ÉCHEC {url}")
            print(f"  [{i:>4}/{len(remaining)}] ECHEC  {url}")
            errors += 1
            done_ids.add(sid)
            pause(3, 6)
            continue

        data = parse_detail_page(html, url)
        details.append(data)
        done_ids.add(sid)

        label = (data.get("email") or data.get("url_arnaque")
                 or data.get("pseudonyme") or sid)
        ok    = "OK" if data.get("date") else "?"
        print(f"  [{i:>4}/{len(remaining)}] [{ok}] {label[:70]}")
        logger.debug(f"  Parsé : id={data.get('id')} date={data.get('date')} "
                     f"cat={data.get('categorie')}")

        # Sauvegarde checkpoint toutes les 10 arnaques
        if i % 10 == 0:
            save_checkpoint(tag, all_ids, done_ids, started_at, details)
            logger.debug(f"  Checkpoint intermédiaire : {len(done_ids)}/{len(all_ids)}")

        pause(2.0, 4.5)

    print()
    save(details, stem, DETAIL_FIELDS)
    delete_checkpoint(tag)

    ok_n = sum(1 for d in details if d.get("date"))
    print(f"\nTerminé : {ok_n} OK / {errors} échecs / {len(details)} total.\n")
    logger.info(f"Fin : {ok_n} OK, {errors} échecs, {len(details)} total.")


if __name__ == "__main__":
    main()
