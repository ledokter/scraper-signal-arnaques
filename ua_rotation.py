"""
Rotation User-Agent + Proxy — bridge vers Users-agent-random/
Charge les profils JSON et expose les fonctions utiles au scraper.
"""

import json
import logging
import random
from pathlib import Path

logger = logging.getLogger("scraper")

HERE    = Path(__file__).parent
UA_DIR  = HERE / "Users-agent-random"

_UA_FILES = [
    UA_DIR / "user_agents.json",
    UA_DIR / "user_agents_random.json",
]
PROXIES_FILE = UA_DIR / "french_proxies.json"

# Cache en mémoire
_profiles: list[dict] = []
_proxies:  list[dict] = []


def _load_profiles() -> list[dict]:
    global _profiles
    if _profiles:
        return _profiles
    for fp in _UA_FILES:
        if fp.exists():
            try:
                data = json.loads(fp.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    _profiles.extend(data)
                    logger.debug(f"UA: {len(data)} profils chargés depuis {fp.name}")
            except Exception as e:
                logger.warning(f"UA: impossible de lire {fp.name}: {e}")
    if not _profiles:
        logger.warning("UA: aucun profil trouvé dans Users-agent-random/ — fallback hardcodé")
    return _profiles


def _load_proxies() -> list[dict]:
    global _proxies
    if _proxies:
        return _proxies
    if PROXIES_FILE.exists():
        try:
            data = json.loads(PROXIES_FILE.read_text(encoding="utf-8"))
            _proxies = data if isinstance(data, list) else []
            logger.debug(f"Proxies: {len(_proxies)} entrées chargées")
        except Exception as e:
            logger.warning(f"Proxies: impossible de lire {PROXIES_FILE.name}: {e}")
    return _proxies


# ── Fallback UA desktop uniquement (curl_cffi ne supporte pas les UA mobiles) ──
_FALLBACK_DESKTOP = [
    {
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "platform": "Win32", "language": "fr-FR", "timezone": "Europe/Paris",
        "screen_resolution": "1920x1080", "device_pixel_ratio": 1.0,
        "memory_gb": 8, "cpu_cores": 8, "touch_support": False,
        "gpu_vendor": "Intel Inc.", "gpu_renderer": "Intel UHD Graphics 630",
    },
    {
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "platform": "Win32", "language": "fr-FR", "timezone": "Europe/Paris",
        "screen_resolution": "1920x1080", "device_pixel_ratio": 1.0,
        "memory_gb": 16, "cpu_cores": 12, "touch_support": False,
        "gpu_vendor": "NVIDIA Corporation", "gpu_renderer": "NVIDIA GeForce RTX 3060",
    },
    {
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "platform": "MacIntel", "language": "fr-FR", "timezone": "Europe/Paris",
        "screen_resolution": "2560x1600", "device_pixel_ratio": 2.0,
        "memory_gb": 16, "cpu_cores": 10, "touch_support": False,
        "gpu_vendor": "Apple", "gpu_renderer": "Apple M2",
    },
]


def get_random_profile(desktop_only: bool = False) -> dict:
    """Retourne un profil aléatoire. desktop_only=True pour curl_cffi."""
    profiles = _load_profiles()
    if desktop_only:
        desktop = [p for p in profiles
                   if p.get("device_type", "").upper() in ("PC", "DESKTOP", "LAPTOP")
                   or p.get("touch_support") is False]
        pool = desktop if desktop else _FALLBACK_DESKTOP
    else:
        pool = profiles if profiles else _FALLBACK_DESKTOP
    return random.choice(pool)


def get_ua_string(desktop_only: bool = True) -> str:
    """Retourne uniquement le user-agent string."""
    p = get_random_profile(desktop_only=desktop_only)
    return p.get("user_agent") or p.get("userAgent") or _FALLBACK_DESKTOP[0]["user_agent"]


def get_random_proxy() -> dict | None:
    """Retourne un proxy aléatoire ou None si aucun disponible."""
    proxies = _load_proxies()
    return random.choice(proxies) if proxies else None


def proxy_url(proxy: dict) -> str:
    """Convertit un dict proxy en URL."""
    proto = proxy.get("protocol", "http").lower()
    return f"{proto}://{proxy['host']}:{proxy['port']}"


def build_playwright_context_options(profile: dict, proxy: dict | None = None) -> dict:
    """Options pour browser.new_context() Playwright."""
    res = profile.get("screen_resolution", "1920x1080").split("x")
    w, h = (int(res[0]), int(res[1])) if len(res) == 2 else (1920, 1080)

    opts: dict = {
        "user_agent":         profile.get("user_agent") or profile.get("userAgent", ""),
        "viewport":           {"width": w, "height": h},
        "locale":             profile.get("language", "fr-FR"),
        "timezone_id":        profile.get("timezone", "Europe/Paris"),
        "device_scale_factor": float(profile.get("device_pixel_ratio", 1.0)),
        "has_touch":          bool(profile.get("touch_support", False)),
        "ignore_https_errors": True,
    }

    if proxy:
        opts["proxy"] = {"server": proxy_url(proxy)}

    return opts


def generate_injection_script(profile: dict) -> str:
    """Script JS à injecter via page.add_init_script() pour masquer le fingerprint."""
    ua      = (profile.get("user_agent") or profile.get("userAgent", "")).replace("'", "\\'")
    plat    = profile.get("platform", "Win32").replace("'", "\\'")
    lang    = profile.get("language", "fr-FR")
    dpr     = float(profile.get("device_pixel_ratio", 1.0))
    cores   = int(profile.get("cpu_cores") or profile.get("hardwareConcurrency", 4))
    mem     = int(profile.get("memory_gb") or profile.get("deviceMemory", 4))
    touch   = 1 if profile.get("touch_support") else 0
    vendor  = (profile.get("gpu_vendor") or profile.get("webglVendor", "Intel Inc.")).replace("'", "\\'")
    renderer = (profile.get("gpu_renderer") or profile.get("webglRenderer", "Intel Iris OpenGL Engine")).replace("'", "\\'")

    return f"""() => {{
        Object.defineProperty(navigator, 'webdriver',          {{ get: () => undefined }});
        Object.defineProperty(navigator, 'userAgent',          {{ get: () => '{ua}' }});
        Object.defineProperty(navigator, 'platform',           {{ get: () => '{plat}' }});
        Object.defineProperty(navigator, 'language',           {{ get: () => '{lang}' }});
        Object.defineProperty(navigator, 'languages',          {{ get: () => ['{lang}', 'fr'] }});
        Object.defineProperty(navigator, 'hardwareConcurrency',{{ get: () => {cores} }});
        Object.defineProperty(navigator, 'deviceMemory',       {{ get: () => {mem} }});
        Object.defineProperty(navigator, 'maxTouchPoints',     {{ get: () => {touch} }});
        Object.defineProperty(window,    'devicePixelRatio',   {{ get: () => {dpr} }});
        const _getParam = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(p) {{
            if (p === 37445) return '{vendor}';
            if (p === 37446) return '{renderer}';
            return _getParam.call(this, p);
        }};
        const _getParam2 = WebGL2RenderingContext.prototype.getParameter;
        WebGL2RenderingContext.prototype.getParameter = function(p) {{
            if (p === 37445) return '{vendor}';
            if (p === 37446) return '{renderer}';
            return _getParam2.call(this, p);
        }};
    }}"""


def log_profile(profile: dict):
    ua   = (profile.get("user_agent") or profile.get("userAgent", ""))[:80]
    dev  = profile.get("device_type", "?")
    os_  = profile.get("os", "?")
    lang = profile.get("language", "?")
    logger.debug(f"Profil UA : [{dev}] {os_} | lang={lang} | {ua}")
