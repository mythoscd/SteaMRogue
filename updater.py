# %%
# # Updater Module
# Startup & shutdown component health checker.
# Runs in background on app open and close to keep manifest repos + SteamTools in sync.

import os
import json
import time
import zipfile
import io
import threading
import hashlib
import warnings
from typing import Dict, Any, Optional
from logger import logger

# Suppress SSL verification warnings (some systems lack proper cert chain)
try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except Exception:
    pass


_STATE_FILE = os.path.join(
    os.environ.get("APPDATA", os.path.expanduser("~")),
    "SteaMRogue",
    "updater_state.json"
)

def _load_state() -> Dict[str, Any]:
    try:
        if os.path.exists(_STATE_FILE):
            with open(_STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def _save_state(state: Dict[str, Any]) -> None:
    try:
        os.makedirs(os.path.dirname(_STATE_FILE), exist_ok=True)
        with open(_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        logger.error(f"[Updater] Failed to save state: {e}")

_status: Dict[str, Any] = {
    "running": False,
    "last_run": None,
    "repos": {},
    "steamtools": {}
}
_status_lock = threading.Lock()

def get_status() -> Dict[str, Any]:
    with _status_lock:
        import copy
        return copy.deepcopy(_status)

def _set_status(**kwargs):
    with _status_lock:
        _status.update(kwargs)

def _set_repo_status(repo_url: str, **kwargs):
    with _status_lock:
        if repo_url not in _status["repos"]:
            _status["repos"][repo_url] = {}
        _status["repos"][repo_url].update(kwargs)

def _set_st_status(**kwargs):
    with _status_lock:
        _status["steamtools"].update(kwargs)

_HEADERS = {"User-Agent": "SteaMRogue-Updater", "Accept": "application/vnd.github.v3+json"}
_TIMEOUT = 10

def _get_repo_latest_sha(repo_url: str) -> Optional[str]:
    try:
        import requests as req
        parts = repo_url.rstrip("/").replace("https://github.com/", "").split("/")
        if len(parts) < 2:
            return None
        owner, repo = parts[0], parts[1]
        api_url = f"https://api.github.com/repos/{owner}/{repo}/commits?per_page=1"
        try:
            r = req.get(api_url, headers=_HEADERS, timeout=_TIMEOUT)
        except Exception:
            r = req.get(api_url, headers=_HEADERS, timeout=_TIMEOUT, verify=False)
        if r.status_code == 200:
            data = r.json()
            if data and isinstance(data, list):
                return data[0].get("sha")
    except Exception as e:
        logger.debug(f"[Updater] SHA fetch failed for {repo_url}: {e}")
    return None

def check_and_update_repos(manifest_repos, force: bool = False) -> Dict[str, Any]:
    state = _load_state()
    repo_shas = state.get("repo_shas", {})
    summary = {}

    for repo_url in manifest_repos:
        short = repo_url.split("/")[-1]
        _set_repo_status(repo_url, checked=False, updated=False, error=None)
        logger.info(f"[Updater] Checking repo: {short}")

        try:
            latest_sha = _get_repo_latest_sha(repo_url)
            _set_repo_status(repo_url, checked=True, sha=latest_sha)

            if latest_sha is None:
                _set_repo_status(repo_url, error="Could not fetch commit SHA")
                summary[repo_url] = {"updated": False, "error": "SHA fetch failed"}
                continue

            old_sha = repo_shas.get(repo_url)
            if not force and old_sha == latest_sha:
                logger.info(f"[Updater] {short}: up-to-date (SHA: {latest_sha[:8]})")
                _set_repo_status(repo_url, updated=False)
                summary[repo_url] = {"updated": False, "sha": latest_sha}
            else:
                logger.info(f"[Updater] {short}: new commits ({(old_sha or 'none')[:8]} -> {latest_sha[:8]})")
                repo_shas[repo_url] = latest_sha
                _set_repo_status(repo_url, updated=True)
                summary[repo_url] = {"updated": True, "sha": latest_sha, "old_sha": old_sha}

        except Exception as e:
            logger.error(f"[Updater] Error checking {repo_url}: {e}")
            _set_repo_status(repo_url, error=str(e))
            summary[repo_url] = {"updated": False, "error": str(e)}

    state["repo_shas"] = repo_shas
    _save_state(state)
    return summary

_STEAMTOOLS_GITHUB_URL = "https://raw.githubusercontent.com/mythoscd/SteaMRogue/main/steamtools_files"
_STEAMTOOLS_DLLS = ["dwmapi.dll", "xinput1_4.dll", "OpenSteamTool.dll"]

def _find_bundled_steamtools():
    import sys
    candidates = []
    if getattr(sys, 'frozen', False):
        if hasattr(sys, '_MEIPASS'):
            candidates.append(os.path.join(sys._MEIPASS, "steamtools_files"))
        exe_dir = os.path.dirname(sys.executable)
        candidates.append(os.path.join(exe_dir, "steamtools_files"))
        candidates.append(os.path.join(exe_dir, "..", "steamtools_files"))
        candidates.append(os.path.join(exe_dir, "resources", "steamtools_files"))
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        candidates.append(os.path.join(base_dir, "steamtools_files"))
    
    local_st = os.path.join(os.path.dirname(os.path.abspath(__file__)), "steamtools_files")
    candidates.append(local_st)
    
    for c in candidates:
        if os.path.isdir(c) and os.path.isfile(os.path.join(c, "OpenSteamTool.dll")):
            return c
    for c in candidates:
        if os.path.isdir(c):
            return c
    return None

def check_and_update_steamtools(steam_path: str, force: bool = False) -> Dict[str, Any]:
    import requests as req
    import shutil

    if not steam_path or not os.path.isdir(steam_path):
        _set_st_status(checked=False, error="Steam path not configured")
        return {"updated": False, "error": "Steam path not configured"}

    _set_st_status(checked=False, updated=False, error=None)
    logger.info("[Updater] Checking SteamTools components...")

    extracted = []
    
    # 1. First priority: Check bundled files for missing DLLs
    bundled_dir = _find_bundled_steamtools()
    if bundled_dir and os.path.isdir(bundled_dir):
        for dll_name in _STEAMTOOLS_DLLS:
            src = os.path.join(bundled_dir, dll_name)
            dst = os.path.join(steam_path, dll_name)
            if os.path.isfile(src) and (not os.path.isfile(dst) or force):
                try:
                    shutil.copy2(src, dst)
                    extracted.append(dll_name)
                    logger.info(f"[Updater] Restored {dll_name} from bundled files to {dst}")
                except Exception as e:
                    logger.warning(f"[Updater] Failed copying bundled {dll_name}: {e}")

    # 2. Check if any target DLL is still missing from Steam
    missing_dlls = []
    for dll_name in _STEAMTOOLS_DLLS:
        target = os.path.join(steam_path, dll_name)
        if not os.path.isfile(target):
            missing_dlls.append(dll_name)

    # 3. If any DLL missing or force update requested, fetch from GitHub
    if missing_dlls or force:
        dlls_to_fetch = _STEAMTOOLS_DLLS if force else missing_dlls
        logger.info(f"[Updater] Fetching SteamTools components from GitHub: {dlls_to_fetch}...")
        for dll_name in dlls_to_fetch:
            url = f"{_STEAMTOOLS_GITHUB_URL}/{dll_name}"
            try:
                r = req.get(url, headers={"User-Agent": "SteaMRogue"}, timeout=30)
                if r.status_code == 200 and len(r.content) > 1000:
                    dst = os.path.join(steam_path, dll_name)
                    with open(dst, "wb") as f:
                        f.write(r.content)
                    if dll_name not in extracted:
                        extracted.append(dll_name)
                    logger.info(f"[Updater] Successfully downloaded and updated {dll_name}")
            except Exception as e:
                logger.warning(f"[Updater] Failed downloading {dll_name} from GitHub: {e}")

    updated = len(extracted) > 0
    _set_st_status(checked=True, updated=updated, extracted=extracted)
    return {"updated": updated, "extracted": extracted}

def check_and_update_library_manifests(steam_path: str, manifest_repos) -> Dict[str, Any]:
    """
    Checks all currently installed games in stplug-in.
    Fetches latest manifest/lua if needed and updates them.
    """
    if not steam_path or not os.path.isdir(steam_path):
        return {"updated": 0, "checked": 0}

    plugin_dir = os.path.join(steam_path, "config", "stplug-in")
    if not os.path.isdir(plugin_dir):
        return {"updated": 0, "checked": 0}

    from manifest_finder import ManifestFinder
    from file_manager import FileManager

    appids = []
    for fname in os.listdir(plugin_dir):
        if fname.endswith(".lua"):
            stem = fname[:-4]
            if stem.isdigit():
                appids.append(stem)

    checked_count = len(appids)
    updated_count = 0

    for aid in appids:
        try:
            found = ManifestFinder.find_online(aid, manifest_repos)
            if found and (found.get("manifests") or found.get("luas")):
                FileManager.write_steamtools_files(steam_path, found.get("manifests", []), found.get("luas", []))
                updated_count += 1
                logger.info(f"[Updater] Refreshed manifest & lua for game AppID: {aid}")
        except Exception as e:
            logger.debug(f"[Updater] Manifest refresh failed for {aid}: {e}")

    return {"checked": checked_count, "updated": updated_count}

def run_startup_checks(manifest_repos, steam_path: str, force: bool = False) -> None:
    _set_status(running=True, last_run=time.time())

    def _worker():
        try:
            logger.info("[Updater] === Startup component check started ===")
            check_and_update_repos(manifest_repos, force=force)
            check_and_update_steamtools(steam_path, force=force)
            # Check and refresh manifests of installed games
            res = check_and_update_library_manifests(steam_path, manifest_repos)
            logger.info(f"[Updater] Library manifest check: {res['checked']} checked, {res['updated']} updated.")
            logger.info("[Updater] === Startup component check finished ===")
        except Exception as e:
            logger.error(f"[Updater] Startup check worker error: {e}")
        finally:
            _set_status(running=False, last_run=time.time())

    t = threading.Thread(target=_worker, daemon=True, name="updater-startup")
    t.start()

def run_shutdown_checks(manifest_repos, steam_path: str) -> None:
    """Runs quick cleanup and state save on application shutdown."""
    try:
        logger.info("[Updater] Running shutdown checks and saving state...")
        state = _load_state()
        state["last_shutdown"] = time.time()
        _save_state(state)
    except Exception as e:
        logger.error(f"[Updater] Shutdown check failed: {e}")

