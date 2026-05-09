#!/usr/bin/env python3
"""
proxy_finder.py — Trouver, tester et gérer les proxies
-------------------------------------------------------
find : trouve des proxies via ProxyBroker (multi-pays, multi-types)
test : teste les proxies du fichier JSON et supprime les invalides
list : affiche les proxies disponibles

Usage :
  python proxy_finder.py find --countries FR DE NL --limit 30
  python proxy_finder.py find --countries FR --types HTTP HTTPS SOCKS5 --limit 50
  python proxy_finder.py test
  python proxy_finder.py test --remove-invalid --workers 20
  python proxy_finder.py list
"""

import argparse
import io
import json
import sys
import time
from pathlib import Path

HERE        = Path(__file__).parent
UA_DIR      = HERE / "Users-agent-random"
DEFAULT_OUT = str(UA_DIR / "french_proxies.json")
DEFAULT_URL = "https://httpbin.org/ip"

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")



# ─────────────────────────────────────────────────────────────────────────────
# CMD : find  (sans ProxyBroker — APIs publiques + test curl_cffi)
# ─────────────────────────────────────────────────────────────────────────────

# Sources publiques filtrées par pays et protocole
_PROXY_SOURCES = [
    # proxyscrape — résultats directs host:port, filtre pays et proto
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol={proto}&timeout=5000&country={country}&ssl=all&anonymity=all",
    # proxy-list.download — filtre pays, elite seulement
    "https://www.proxy-list.download/api/v1/get?type={proto}&anon=elite&country={country}",
]
# Fallback générique (pas de filtre pays) si les sources filtrées donnent peu de résultats
_PROXY_FALLBACK = [
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/{proto}.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/{proto}.txt",
]


def _fetch_url(url: str, timeout: int = 15) -> str:
    """Télécharge une URL et retourne le texte brut."""
    import urllib.request
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception as e:
        return ""


def _parse_host_port(text: str) -> list[tuple[str, int]]:
    """Extrait les paires (host, port) d'un texte brut ligne par ligne."""
    result = []
    for line in text.splitlines():
        line = line.strip()
        if ":" not in line:
            continue
        parts = line.split(":")
        if len(parts) >= 2:
            host = parts[0].strip()
            port_str = parts[1].strip().split()[0]
            if port_str.isdigit() and 1 <= int(port_str) <= 65535:
                # Valider que c'est bien une IP ou un hostname
                import re
                if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", host):
                    result.append((host, int(port_str)))
    return result


def cmd_find(args):
    """
    Trouve des proxies depuis des APIs publiques, les teste avec curl_cffi,
    et sauvegarde les proxies valides dans le fichier JSON.
    ProxyBroker n'est pas utilisé (incompatible Python 3.10+).
    """
    import concurrent.futures
    import re

    countries = [c.upper().strip() for c in args.countries if c.strip()]
    limit     = args.limit
    out_path  = Path(args.output)
    protos    = [t.lower() for t in args.types
                 if t.lower() in ("http", "https", "socks4", "socks5")]

    print(f"[FIND] Pays   : {', '.join(countries)}")
    print(f"[FIND] Types  : {', '.join(p.upper() for p in protos)}")
    print(f"[FIND] Limite : {limit}")
    print(f"[FIND] Sortie : {out_path}")
    print("[FIND] Récupération des listes publiques...")
    sys.stdout.flush()

    # ── Collecter les candidats ───────────────────────────────────────────────
    candidates: set[tuple[str, int, str, str]] = set()  # (host, port, proto, country)

    for proto in protos:
        if proto not in ("http", "https"):
            # SOCKS4/5 : sources différentes
            for cc in countries:
                url = f"https://api.proxyscrape.com/v2/?request=getproxies&protocol={proto}&timeout=5000&country={cc}"
                text = _fetch_url(url)
                for host, port in _parse_host_port(text):
                    candidates.add((host, port, proto, cc))
                if text:
                    print(f"  [+] {proto.upper()} {cc} : {len(_parse_host_port(text))} candidats depuis proxyscrape")
                    sys.stdout.flush()
            continue

        for cc in countries:
            for tpl in _PROXY_SOURCES:
                url  = tpl.format(proto=proto, country=cc.lower())
                text = _fetch_url(url)
                pairs = _parse_host_port(text)
                before = len(candidates)
                for host, port in pairs:
                    candidates.add((host, port, proto, cc))
                added = len(candidates) - before
                if pairs:
                    src = url.split("/")[2][:30]
                    print(f"  [+] {proto.upper()} {cc} via {src} : {added} nouveaux candidats")
                    sys.stdout.flush()

    # Fallback si peu de résultats
    if len(candidates) < limit * 2:
        print(f"  [fallback] Peu de candidats ({len(candidates)}), ajout de listes génériques...")
        sys.stdout.flush()
        for proto in protos:
            if proto not in ("http", "https"):
                continue
            for tpl in _PROXY_FALLBACK:
                url  = tpl.format(proto=proto)
                text = _fetch_url(url)
                before = len(candidates)
                for host, port in _parse_host_port(text):
                    candidates.add((host, port, proto, "??"))
                print(f"  [fallback] {proto.upper()} : +{len(candidates)-before} candidats")
                sys.stdout.flush()

    if not candidates:
        print("[ERREUR] Aucun proxy candidat trouvé. Vérifiez la connexion Internet.")
        sys.stdout.flush()
        return

    # Limiter à limit×4 pour ne pas tester trop longtemps
    all_candidates = list(candidates)[: limit * 4]
    print(f"\n[TEST] {len(all_candidates)} candidats à tester (timeout 8s)...")
    sys.stdout.flush()

    # ── Tester en parallèle avec curl_cffi ────────────────────────────────────
    found: list[dict] = []
    tested = 0
    workers = min(25, max(10, len(all_candidates) // 4))

    def _test(entry: tuple[str, int, str, str]):
        host, port, proto, country = entry
        proxy_url_str = f"{proto}://{host}:{port}"
        try:
            import curl_cffi.requests as cffi_req
            s  = cffi_req.Session(impersonate="chrome124")
            t0 = time.time()
            r  = s.get("https://httpbin.org/ip",
                       proxies={"http": proxy_url_str, "https": proxy_url_str},
                       timeout=8)
            elapsed = round(time.time() - t0, 2)
            if r.status_code == 200:
                return host, port, proto, country, elapsed
        except Exception:
            pass
        return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = list(concurrent.futures.as_completed(
            {ex.submit(_test, e): e for e in all_candidates}
        ))
        for fut in futs:
            tested += 1
            result = fut.result()
            if result:
                host, port, proto, country, elapsed = result
                info = {
                    "host":      host,
                    "port":      port,
                    "protocol":  proto.upper(),
                    "anonymity": "Unknown",
                    "country":   country,
                    "city":      "",
                }
                found.append(info)
                print(f"  [OK] {host}:{port}  {proto.upper()}  {country}  {elapsed}s")
                sys.stdout.flush()
                if len(found) >= limit:
                    break
            if tested % 30 == 0:
                print(f"  ... {tested}/{len(all_candidates)} testés  {len(found)} valides")
                sys.stdout.flush()

    # ── Fusionner avec l'existant ─────────────────────────────────────────────
    existing: list[dict] = []
    if out_path.exists():
        try:
            data = json.loads(out_path.read_text(encoding="utf-8"))
            existing = data if isinstance(data, list) else []
        except Exception:
            pass

    seen = {(p["host"], str(p["port"])) for p in existing}
    new_count = 0
    for p in found:
        key = (p["host"], str(p["port"]))
        if key not in seen:
            existing.append(p)
            seen.add(key)
            new_count += 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[DONE] {len(found)} valides  +{new_count} nouveaux  "
          f"{len(existing)} total → {out_path.name}")
    sys.stdout.flush()


# ─────────────────────────────────────────────────────────────────────────────
# CMD : test
# ─────────────────────────────────────────────────────────────────────────────

def cmd_test(args):
    in_path = Path(args.input)
    if not in_path.exists():
        print(f"[ERREUR] Fichier introuvable : {in_path}")
        sys.exit(1)
    try:
        proxies = json.loads(in_path.read_text(encoding="utf-8"))
        if not isinstance(proxies, list):
            proxies = []
    except Exception as e:
        print(f"[ERREUR] {e}")
        sys.exit(1)

    if not proxies:
        print("[INFO] Aucun proxy à tester dans le fichier.")
        return

    test_url = args.test_url
    timeout  = args.timeout
    workers  = args.workers

    print(f"[TEST] {len(proxies)} proxies  URL: {test_url}")
    print(f"[TEST] Timeout: {timeout}s  Threads: {workers}")
    sys.stdout.flush()

    import concurrent.futures

    def _test_one(proxy):
        host  = proxy.get("host", "")
        port  = proxy.get("port", "")
        proto = str(proxy.get("protocol", "http")).lower().split("(")[0].strip()
        if proto not in ("http", "https", "socks4", "socks5"):
            proto = "http"
        if not host or not port:
            return proxy, False, 0.0
        proxy_url_str = f"{proto}://{host}:{port}"
        try:
            import curl_cffi.requests as cffi_req
            s  = cffi_req.Session(impersonate="chrome124")
            t0 = time.time()
            r  = s.get(test_url,
                       proxies={"http": proxy_url_str, "https": proxy_url_str},
                       timeout=timeout)
            elapsed = round(time.time() - t0, 2)
            return proxy, r.status_code < 500, elapsed
        except Exception:
            return proxy, False, 0.0

    valid   = []
    invalid = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(_test_one, p): p for p in proxies}
        for i, fut in enumerate(concurrent.futures.as_completed(futs), 1):
            proxy, ok, elapsed = fut.result()
            label   = f"{proxy.get('host', '?')}:{proxy.get('port', '?')}"
            country = proxy.get("country", "??")
            status  = f"OK  {elapsed}s" if ok else "FAIL"
            print(f"  [{i:>3}/{len(proxies)}] {label:<22} {country}  {status}")
            sys.stdout.flush()
            if ok:
                valid.append(proxy)
            else:
                invalid.append(proxy)

    print(f"\n[RÉSULTAT] {len(valid)} valides  {len(invalid)} invalides")
    sys.stdout.flush()

    if args.remove_invalid:
        in_path.write_text(json.dumps(valid, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[SAVE] {len(valid)} proxies valides conservés dans {in_path.name}")
    else:
        print("[INFO] Fichier non modifié. Cochez 'Supprimer invalides' pour nettoyer.")
    sys.stdout.flush()


# ─────────────────────────────────────────────────────────────────────────────
# CMD : list
# ─────────────────────────────────────────────────────────────────────────────

def cmd_list(args):
    path = Path(args.input)
    if not path.exists():
        print(f"[INFO] Aucun fichier proxy : {path}")
        return
    try:
        proxies = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[ERREUR] {e}")
        return
    if not proxies:
        print("[INFO] Liste vide.")
        return

    print(f"\n{len(proxies)} proxies dans {path.name}\n")
    print(f"  {'Host':<18} {'Port':>5}  {'Proto':<7} {'Anon':<12} {'Pays'}  Ville")
    print("  " + "─" * 65)
    for p in proxies:
        print(f"  {str(p.get('host','?')):<18} {str(p.get('port','?')):>5}  "
              f"{str(p.get('protocol','?')):<7} {str(p.get('anonymity','?')):<12} "
              f"{p.get('country','??')}   {p.get('city','')}")
    print()


# ─────────────────────────────────────────────────────────────────────────────

def main():
    ap  = argparse.ArgumentParser(description="Proxy Finder & Tester",
                                  formatter_class=argparse.RawDescriptionHelpFormatter,
                                  epilog=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    pf = sub.add_parser("find", help="Trouver des proxies via ProxyBroker")
    pf.add_argument("--countries", nargs="+", default=["FR"], metavar="CC",
                    help="Codes pays ISO-2 (ex: FR DE NL BE CH)")
    pf.add_argument("--types",  nargs="+", default=["HTTP", "HTTPS"],
                    choices=["HTTP", "HTTPS", "SOCKS4", "SOCKS5"])
    pf.add_argument("--limit",  type=int, default=30,
                    help="Nombre max de proxies à trouver")
    pf.add_argument("--output", default=DEFAULT_OUT,
                    help="Fichier JSON de sortie")

    pt = sub.add_parser("test", help="Tester les proxies existants")
    pt.add_argument("--input",          default=DEFAULT_OUT)
    pt.add_argument("--test-url",       default=DEFAULT_URL)
    pt.add_argument("--timeout",        type=float, default=10.0)
    pt.add_argument("--workers",        type=int,   default=10)
    pt.add_argument("--remove-invalid", action="store_true",
                    help="Supprimer les proxies invalides du fichier")

    pl = sub.add_parser("list", help="Lister les proxies du fichier JSON")
    pl.add_argument("--input", default=DEFAULT_OUT)

    args = ap.parse_args()
    {"find": cmd_find, "test": cmd_test, "list": cmd_list}[args.cmd](args)


if __name__ == "__main__":
    main()
