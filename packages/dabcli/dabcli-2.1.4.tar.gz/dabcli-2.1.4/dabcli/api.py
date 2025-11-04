# api.py
import requests
import urllib.parse
from typing import Dict, Optional, Tuple

from dabcli.config import config
from dabcli.utils import require_login

# -------------------- SSL patch --------------------
# Disable SSL certificate verification warnings globally
requests.packages.urllib3.disable_warnings(
    requests.packages.urllib3.exceptions.InsecureRequestWarning
)

BASE_URL = "https://dabmusic.xyz/api"


def _should_debug() -> bool:
    return bool(getattr(config, "debug", False) or getattr(config, "test_mode", False))


def _mask_headers(h: dict) -> dict:
    masked = dict(h or {})
    cookie = masked.get("Cookie")
    if cookie and "session=" in cookie:
        val = cookie.split("session=", 1)[1]
        if ";" in val:
            val = val.split(";", 1)[0]
        if len(val) > 10:
            val_mask = val[:4] + "…(masked)…" + val[-4:]
        else:
            val_mask = "…(masked)…"
        masked["Cookie"] = f"session={val_mask}"
    return masked


def get_auth_header():
    return config.get_auth_header() or {}


def login(email: str, password: str):
    session = requests.Session()
    url = f"{BASE_URL}/auth/login"
    payload = {"email": email, "password": password}

    try:
        resp = session.post(url, json=payload, verify=False)
    except requests.RequestException as e:
        print(f"Network error during login: {e}")
        return

    token = session.cookies.get("session")
    if resp.status_code == 200 and token:
        config.email = email
        config.password = password
        config._save_token(token)
        print("Login successful. Token and credentials saved.")
    else:
        print("Login failed. Check email/password.")
        if _should_debug():
            print(f"[DEBUG] Status {resp.status_code}; Body:\n{resp.text[:500]}")


def _safe_json(resp, endpoint):
    try:
        return resp.json()
    except ValueError:
        if _should_debug():
            print(f"[DEBUG] Invalid JSON response from {endpoint} ({len(resp.text)} bytes):\n{resp.text[:800]}")
        return None


def _request(method: str, endpoint: str, **kwargs):
    if not require_login(config, silent=False):
        return None

    headers = get_auth_header()
    headers["User-Agent"] = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/1337.0.0.0 Safari/537.36"
    )

    url = BASE_URL + endpoint

    params = kwargs.get("params")
    if params:
        try:
            q = urllib.parse.urlencode(params, doseq=True, safe="/:")
        except Exception:
            q = str(params)
        debug_url = f"{url}?{q}"
    else:
        debug_url = url

    if _should_debug():
        masked_headers = _mask_headers(headers)
        body_preview = ""
        if "json" in kwargs and kwargs["json"] is not None:
            body_preview = f" | JSON: {str(kwargs['json'])[:200]}"
        print(f"[DEBUG] {method} {debug_url} | HEADERS: {masked_headers}{body_preview}")

    try:
        # SSL verification disabled silently
        resp = requests.request(method, url, headers=headers, verify=False, **kwargs)
        resp.raise_for_status()
        return _safe_json(resp, endpoint)
    except requests.HTTPError as e:
        if _should_debug() and e.response is not None:
            print(f"[DEBUG] HTTP error {e.response.status_code} on {debug_url}")
            print(f"[DEBUG] Response body: {e.response.text[:1000]}")
        return None
    except requests.RequestException as e:
        if _should_debug():
            print(f"[DEBUG] Request error on {debug_url}: {e}")
        return None

def get_current_user():
    """Return current logged-in user info or None"""
    from config import config
    if not config.token:
        return None
    try:
        r = requests.get(
            f"{BASE_URL}/auth/me",
            headers={"Cookie": f"session={config.token}"},
            verify=False
        )
        if r.status_code != 200:
            return {"error": r.status_code}
        return r.json()  # expects {"user": {...}} or {"user": null}
    except:
        return None


def get(endpoint: str, params=None):
    return _request("GET", endpoint, params=params)


def post(endpoint: str, json=None):
    return _request("POST", endpoint, json=json)


def delete(endpoint: str, params=None):
    return _request("DELETE", endpoint, params=params)


def patch(endpoint: str, json=None):
    return _request("PATCH", endpoint, json=json)


# -------------------- New function for lyrics --------------------
def get_lyrics(title: str, artist: str) -> Tuple[str, bool] | Tuple[None, None]:
    """
    Fetch lyrics for a song from the API.
    Returns (lyrics_text, unsynced: bool).
    If lyrics not found, returns (None, None) silently.
    """
    if not title or not artist:
        return None, None

    resp = get("/lyrics", params={"title": title, "artist": artist})
    if not resp or "lyrics" not in resp:
        return None, None

    lyrics = resp.get("lyrics", "").strip()
    unsynced = resp.get("unsynced", True)
    if not lyrics:
        return None, None

    return lyrics, unsynced
