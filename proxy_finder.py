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

# ── Patch asyncio Python 3.10+ : loop= supprimé de toutes les primitives ─────
# ProxyBroker (2016) utilise asyncio.Event/Lock/Semaphore/Queue avec loop=
import asyncio as _aio


def _strip_loop(orig):
    """Retourne un __init__ qui ignore silencieusement le kwarg loop=."""
    def _patched(self, *args, **kw):
        kw.pop("loop", None)
        orig(self, *args, **kw)
    return _patched


for _cls in (_aio.Queue, _aio.Event, _aio.Lock,
             _aio.Semaphore, _aio.BoundedSemaphore, _aio.Condition):
    _cls.__init__ = _strip_loop(_cls.__init__)


# ─────────────────────────────────────────────────────────────────────────────
# CMD : find
# ─────────────────────────────────────────────────────────────────────────────

def cmd_find(args):
    pb_path = UA_DIR / "ProxyBroker"
    if pb_path.exists():
        sys.path.insert(0, str(pb_path))

    try:
        from proxybroker import Broker  # noqa: F401
    except ImportError as e:
        print(f"[ERREUR] ProxyBroker non disponible : {e}")
        print(f"  Chemin testé : {pb_path}")
        print(f"  Installez avec : pip install proxybroker")
        sys.exit(1)

    import asyncio

    countries = [c.upper().strip() for c in args.countries if c.strip()]
    limit     = args.limit
    out_path  = Path(args.output)

    type_map = {
        "HTTP":   ("HTTP",   ("Anonymous", "High")),
        "HTTPS":  ("HTTPS",  ("Anonymous", "High")),
        "SOCKS4": ("SOCKS4", None),
        "SOCKS5": ("SOCKS5", None),
    }
    types = []
    for t in args.types:
        entry = type_map.get(t.upper())
        if entry:
            proto, anon = entry
            types.append((proto, anon) if anon else proto)

    print(f"[FIND] Pays   : {', '.join(countries)}")
    print(f"[FIND] Types  : {', '.join(args.types)}")
    print(f"[FIND] Limite : {limit}")
    print(f"[FIND] Sortie : {out_path}")
    print("[FIND] Démarrage... (peut prendre plusieurs minutes)")
    sys.stdout.flush()

    found = []

    async def _run():
        queue  = asyncio.Queue()
        broker = Broker(queue, timeout=8, max_conn=100, max_tries=2, verify_ssl=False)

        async def _collect():
            while True:
                proxy = await queue.get()
                if proxy is None:
                    break
                country = proxy.geo.code if proxy.geo else "??"
                city    = getattr(proxy.geo, "city", "") or ""
                proto   = list(proxy.types)[0] if proxy.types else "HTTP"
                anon    = (proxy.anonymity if isinstance(proxy.anonymity, str)
                           else getattr(proxy.anonymity, "level", "?"))
                info = {
                    "host":      proxy.host,
                    "port":      proxy.port,
                    "protocol":  str(proto),
                    "anonymity": str(anon),
                    "country":   country,
                    "city":      city,
                }
                found.append(info)
                print(f"  [+] {proxy.host}:{proxy.port}  {proto}  {anon}  {country} {city}")
                sys.stdout.flush()

        await asyncio.gather(
            broker.find(types=types, countries=countries, limit=limit),
            _collect(),
        )

    try:
        asyncio.run(_run())
    except Exception as e:
        print(f"[ERREUR] {e}")
        import traceback
        traceback.print_exc()

    # Fusionner avec l'existant (dédupliquer)
    existing = []
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
    print(f"\n[DONE] {len(found)} trouvés  +{new_count} nouveaux  "
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
