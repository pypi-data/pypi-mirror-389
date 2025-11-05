#############################
# TRANSLATIONS 
#############################


import json
import os
import urllib.request
from typing import Dict, Any

# URL por defecto a tu JSON de traducciones
_DEFAULT_URL = os.getenv(
    "GADL_TRANSLATIONS_URL",
    "https://raw.githubusercontent.com/GeoagrobyTEK/traducciones_dicc/main/translations.json"
)

_TIMEOUT = float(os.getenv("GADL_TRANSLATIONS_TIMEOUT", "30"))  # segundos
_REFRESH_FLAG = "GADL_TRANSLATIONS_REFRESH"

# Caché en memoria (solo durante el proceso)
_REMOTE_TRANSLATIONS: Dict[str, Any] | None = None


def _download_translations(url: str) -> Dict[str, Any]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "geoagrodatalab/translations-loader",
            "Accept": "application/json",
        },
    )

    with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
        if getattr(resp, "status", 200) != 200:
            raise RuntimeError(f"HTTP {getattr(resp, 'status', '???')}")
        data = resp.read().decode("utf-8")

    obj = json.loads(data)
    if not isinstance(obj, dict):
        raise ValueError("El JSON de traducciones debe tener un objeto dict en la raíz.")
    return obj


def _get_translations() -> Dict[str, Any]:
    global _REMOTE_TRANSLATIONS

    url = _DEFAULT_URL.strip()
    force_refresh = os.getenv(_REFRESH_FLAG) == "1"

    if url:
        if _REMOTE_TRANSLATIONS is None or force_refresh:
            try:
                _REMOTE_TRANSLATIONS = _download_translations(url)
            except Exception:
                _REMOTE_TRANSLATIONS = {}

        return _REMOTE_TRANSLATIONS

    return {}


def translate(string: str, language: str) -> str:
    data = _get_translations()
    try:
        return data[string][language]
    except Exception:
        return "Unknown"