# %%
# # Updater Module
# Startup & on-demand component health checker and synchronization engine.
# Runs in background on app startup, shutdown, and on-demand from Settings.

import os
import re
import sys
import json
import time
import shutil
import threading
import concurrent.futures
from typing import Dict, Any, Optional, List
from logger import logger

# Suppress SSL verification warnings
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

_init_state = _load_state()
_status: Dict[str, Any] = {
    "running": False,
    "last_run": _init_state.get("last_run"),
    "last_run_formatted": _init_state.get("last_run_formatted"),
    "repos": {},
    "steamtools": {},
    "signatures": {},
    "library": {"checked": 0, "updated": 0, "running": False},
    "bypass": {"checked": False, "updated": False},
    "actions": []
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

def _append_action(action_str: str):
    with _status_lock:
        if action_str not in _status["actions"]:
            _status["actions"].append(action_str)

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) SteaMRogue-Updater",
    "Accept": "application/vnd.github.v3+json"
}
_TIMEOUT = 10

def _get_repo_latest_sha(repo_url: str, cached_etag: Optional[str] = None, cached_sha: Optional[str] = None) -> (Optional[str], Optional[str]):
    """
    Fetches latest commit SHA for a GitHub repo with ETag caching and Atom feed rate-limit fallback.
    Returns (sha, etag).
    """
    import requests as req

    parts = repo_url.rstrip("/").replace("https://github.com/", "").split("/")
    if len(parts) < 2:
        return None, None
    owner, repo = parts[0], parts[1]

    headers = dict(_HEADERS)
    if cached_etag:
        headers["If-None-Match"] = cached_etag

    api_url = f"https://api.github.com/repos/{owner}/{repo}/commits?per_page=1"

    # 1. Try GitHub API with ETag
    try:
        r = req.get(api_url, headers=headers, timeout=_TIMEOUT)
        if r.status_code == 304 and cached_sha:
            # Not modified, saved API quota!
            return cached_sha, cached_etag
        if r.status_code == 200:
            data = r.json()
            if data and isinstance(data, list) and len(data) > 0:
                new_sha = data[0].get("sha")
                new_etag = r.headers.get("ETag")
                return new_sha, new_etag
    except Exception as e:
        logger.debug(f"[Updater] GitHub API request failed for {owner}/{repo}: {e}")

    # 2. Rate-Limit Fallback: Parse Atom Feed (No API quota limit)
    for branch in ["main", "master"]:
        atom_url = f"https://github.com/{owner}/{repo}/commits/{branch}.atom"
        try:
            r = req.get(atom_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=_TIMEOUT)
            if r.status_code == 200 and r.text:
                # Match commit SHA in atom entries
                # <id>tag:github.com,2008:Grit::Commit/48f0...</id> or /commit/48f0...
                m = re.search(r"Commit/([a-f0-9]{40})", r.text, re.IGNORECASE)
                if not m:
                    m = re.search(r"/commit/([a-f0-9]{40})", r.text, re.IGNORECASE)
                if m:
                    return m.group(1), None
        except Exception:
            pass

    return cached_sha, cached_etag

def check_and_update_repos(manifest_repos: List[str], force: bool = False) -> Dict[str, Any]:
    state = _load_state()
    repo_shas = state.get("repo_shas", {})
    repo_etags = state.get("repo_etags", {})
    summary = {}

    def _check_single_repo(url: str):
        short = url.split("/")[-1]
        _set_repo_status(url, checked=False, updated=False, error=None)
        logger.info(f"[Updater] Checking manifest repo: {short}")

        try:
            cached_etag = repo_etags.get(url)
            cached_sha = repo_shas.get(url)

            latest_sha, new_etag = _get_repo_latest_sha(url, cached_etag, cached_sha)
            _set_repo_status(url, checked=True, sha=latest_sha)

            if latest_sha is None:
                _set_repo_status(url, error="Could not fetch commit SHA")
                return url, {"updated": False, "error": "SHA fetch failed"}

            if new_etag:
                repo_etags[url] = new_etag

            old_sha = cached_sha
            if not force and old_sha == latest_sha:
                logger.info(f"[Updater] {short}: güncel (SHA: {latest_sha[:8]})")
                _set_repo_status(url, updated=False)
                return url, {"updated": False, "sha": latest_sha}
            else:
                logger.info(f"[Updater] {short}: yeni commitler bulundu ({(old_sha or 'yok')[:8]} -> {latest_sha[:8]})")
                repo_shas[url] = latest_sha
                _set_repo_status(url, updated=True)
                _append_action(f"Manifest deposu güncellendi: {short} ({latest_sha[:8]})")
                return url, {"updated": True, "sha": latest_sha, "old_sha": old_sha}

        except Exception as e:
            logger.error(f"[Updater] Error checking repo {url}: {e}")
            _set_repo_status(url, error=str(e))
            return url, {"updated": False, "error": str(e)}

    # Parallelize checking across manifest repos
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(4, len(manifest_repos) or 1)) as executor:
        futures = [executor.submit(_check_single_repo, repo_url) for repo_url in manifest_repos]
        for f in concurrent.futures.as_completed(futures):
            u, res = f.result()
            summary[u] = res

    state["repo_shas"] = repo_shas
    state["repo_etags"] = repo_etags
    _save_state(state)
    return summary

_STEAMTOOLS_GITHUB_URL = "https://raw.githubusercontent.com/mythoscd/SteaMRogue/main/steamtools_files"
_STEAMTOOLS_DLLS = ["xinput1_4.dll", "OpenSteamTool.dll"]

def _find_bundled_steamtools():
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

    if not steam_path or not os.path.isdir(steam_path):
        _set_st_status(checked=False, error="Steam dizini yapılandırılmadı")
        return {"updated": False, "error": "Steam dizini yapılandırılmadı"}

    _set_st_status(checked=False, updated=False, error=None)
    logger.info("[Updater] Checking SteamTools components...")

    extracted = []

    # Remove obsolete dwmapi.dll to prevent VGUI_Setup failure & recursion
    dwmapi_legacy = os.path.join(steam_path, "dwmapi.dll")
    if os.path.isfile(dwmapi_legacy):
        try:
            os.remove(dwmapi_legacy)
            logger.info("[Updater] Cleaned obsolete dwmapi.dll from Steam folder.")
            _append_action("Eski dwmapi.dll kancası temizlendi.")
        except Exception:
            pass

    # 1. First priority: Check bundled files for missing DLLs & opensteamtool patterns
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
                except PermissionError:
                    logger.debug(f"[Updater] {dll_name} is locked (Steam running), skipping overwrite.")
                except Exception as e:
                    logger.warning(f"[Updater] Failed copying bundled {dll_name}: {e}")

        # Copy opensteamtool signature files
        opensteamtool_src = os.path.join(bundled_dir, "opensteamtool")
        opensteamtool_dst = os.path.join(steam_path, "opensteamtool")
        if os.path.isdir(opensteamtool_src):
            os.makedirs(opensteamtool_dst, exist_ok=True)
            for root, _, files in os.walk(opensteamtool_src):
                for f in files:
                    if f.endswith(".toml"):
                        src_f = os.path.join(root, f)
                        rel_path = os.path.relpath(src_f, opensteamtool_src)
                        dst_f = os.path.join(opensteamtool_dst, rel_path)
                        os.makedirs(os.path.dirname(dst_f), exist_ok=True)
                        if not os.path.isfile(dst_f) or force:
                            try:
                                shutil.copy2(src_f, dst_f)
                            except Exception:
                                pass

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
                r = req.get(url, headers={"User-Agent": "SteaMRogue"}, timeout=20)
                if r.status_code == 200 and len(r.content) > 1000:
                    dst = os.path.join(steam_path, dll_name)
                    with open(dst, "wb") as f:
                        f.write(r.content)
                    if dll_name not in extracted:
                        extracted.append(dll_name)
                    logger.info(f"[Updater] Successfully downloaded and updated {dll_name}")
                    _append_action(f"SteamTools bileşeni indirildi/güncellendi: {dll_name}")
            except PermissionError:
                logger.debug(f"[Updater] {dll_name} is locked by Steam, skipping online overwrite.")
            except Exception as e:
                logger.warning(f"[Updater] Failed downloading {dll_name} from GitHub: {e}")

    # Silence modal MessageBoxA in OpenSteamTool.dll to prevent freezing
    ost_dll = os.path.join(steam_path, "OpenSteamTool.dll")
    if os.path.isfile(ost_dll):
        try:
            with open(ost_dll, "r+b") as f_ost:
                f_ost.seek(0x7423b)
                b_check = f_ost.read(6)
                if b_check == bytes.fromhex("ff15d7d60700"):
                    f_ost.seek(0x7423b)
                    f_ost.write(bytes.fromhex("909090909090"))
                    logger.info("[Updater] Silenced modal MessageBoxA in OpenSteamTool.dll")
        except Exception:
            pass

    # Verify upstream OpenSteamTool official release availability
    try:
        r_rel = req.get("https://api.github.com/repos/OpenSteam001/OpenSteamTool/releases/latest", headers={"User-Agent": "SteaMRogue"}, timeout=5)
        if r_rel.status_code == 200:
            rel_data = r_rel.json()
            up_tag = rel_data.get("tag_name")
            if up_tag:
                logger.info(f"[Updater] Upstream OpenSteamTool version verified: {up_tag}")
    except Exception:
        pass

    # 4. Ensure depotcache manifests are synchronized to official depotcache (fixes 'İnternet Yok')
    config_depotcache = os.path.join(steam_path, "config", "depotcache")
    depotcache = os.path.join(steam_path, "depotcache")
    if os.path.isdir(config_depotcache):
        os.makedirs(depotcache, exist_ok=True)
        for f in os.listdir(config_depotcache):
            if f.endswith(".manifest"):
                src = os.path.join(config_depotcache, f)
                dst = os.path.join(depotcache, f)
                if not os.path.isfile(dst) or (os.path.getsize(dst) != os.path.getsize(src)):
                    try:
                        shutil.copy2(src, dst)
                    except Exception:
                        pass

    # 5. Adapt OpenSteamTool TOML signatures for the active Steam build
    try:
        import validator
        sig_result = validator.ensure_opensteamtool_signatures(steam_path)
        if sig_result:
            _append_action("OpenSteamTool TOML imzaları aktif Steam yapısına uyarlandı.")
    except Exception as e:
        logger.debug(f"[Updater] Signature adaptation: {e}")

    updated = len(extracted) > 0
    _set_st_status(checked=True, updated=updated, extracted=extracted)
    return {"updated": updated, "extracted": extracted}

def check_and_update_bypass_database() -> Dict[str, Any]:
    """
    Checks and updates the local web/bypass_data.json with the latest online OnlineFix bypass database.
    """
    import requests as req
    bypass_url = "https://raw.githubusercontent.com/mythoscd/SteaMRogue/main/web/bypass_data.json"
    
    # Locate local bypass_data.json candidates
    candidates = []
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates.append(os.path.join(base_dir, "web", "bypass_data.json"))
    
    appdata = os.environ.get("APPDATA")
    if appdata:
        candidates.append(os.path.join(appdata, "SteaMRogue", "bypass_data.json"))
        
    target_path = candidates[0]
    
    try:
        r = req.get(bypass_url, headers=_HEADERS, timeout=10)
        if r.status_code == 200 and len(r.content) > 50:
            remote_json = r.json()
            if isinstance(remote_json, (dict, list)):
                # Write to target
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                with open(target_path, "w", encoding="utf-8") as f:
                    json.dump(remote_json, f, ensure_ascii=False, indent=2)
                logger.info(f"[Updater] Successfully synchronized OnlineFix bypass database ({len(remote_json)} items)")
                _append_action(f"OnlineFix çok oyunculu veritabanı güncellendi ({len(remote_json)} oyun).")
                with _status_lock:
                    _status["bypass"] = {"checked": True, "updated": True, "count": len(remote_json)}
                return {"updated": True, "count": len(remote_json)}
    except Exception as e:
        logger.debug(f"[Updater] Bypass database sync note: {e}")

    with _status_lock:
        _status["bypass"] = {"checked": True, "updated": False}
    return {"updated": False}

def check_and_update_library_manifests(steam_path: str, manifest_repos: List[str]) -> Dict[str, Any]:
    """
    Checks all currently installed games in stplug-in using a high-performance thread pool.
    Fetches latest manifest/lua if needed and updates them in parallel.
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
    if checked_count == 0:
        return {"updated": 0, "checked": 0}

    with _status_lock:
        _status["library"] = {"checked": 0, "updated": 0, "total": checked_count, "running": True}

    updated_count = 0
    updated_lock = threading.Lock()

    def _check_game(aid: str):
        nonlocal updated_count
        try:
            found = ManifestFinder.find_online(aid, manifest_repos)
            if found and (found.get("manifests") or found.get("luas")):
                FileManager.write_steamtools_files(steam_path, found.get("manifests", []), found.get("luas", []))
                with updated_lock:
                    updated_count += 1
                logger.info(f"[Updater] Refreshed manifest & lua for game AppID: {aid}")
        except Exception as e:
            logger.debug(f"[Updater] Manifest refresh failed for {aid}: {e}")

    # Use 5 concurrent workers for fast non-blocking lookup
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(5, checked_count)) as executor:
        list(executor.map(_check_game, appids))

    if updated_count > 0:
        _append_action(f"{updated_count} adet kurulu oyunun manifestosu ve Lua betiği en güncel sürüme yükseltildi.")

    with _status_lock:
        _status["library"] = {"checked": checked_count, "updated": updated_count, "total": checked_count, "running": False}

    return {"checked": checked_count, "updated": updated_count}

def run_full_update_now(manifest_repos: List[str], steam_path: str, force: bool = False) -> Dict[str, Any]:
    """
    Runs the complete synchronization suite immediately and returns detailed results.
    """
    start_time = time.time()
    formatted_time = time.strftime("%d.%m.%Y %H:%M:%S")

    _set_status(running=True, last_run=start_time, last_run_formatted=formatted_time, actions=[])

    try:
        logger.info("[Updater] === Full component & manifest synchronization started ===")
        repo_res = check_and_update_repos(manifest_repos, force=force)
        st_res = check_and_update_steamtools(steam_path, force=force)
        bp_res = check_and_update_bypass_database()
        lib_res = check_and_update_library_manifests(steam_path, manifest_repos)
        logger.info("[Updater] === Full component & manifest synchronization completed ===")

        current_status = get_status()
        current_status["success"] = True
        current_status["duration_seconds"] = round(time.time() - start_time, 2)
        return current_status
    except Exception as e:
        logger.error(f"[Updater] Synchronization failed: {e}")
        return {"success": False, "error": str(e), "actions": get_status().get("actions", [])}
    finally:
        finished_ts = time.time()
        finished_fmt = time.strftime("%d.%m.%Y %H:%M:%S")
        _set_status(running=False, last_run=finished_ts, last_run_formatted=finished_fmt)
        try:
            st = _load_state()
            st["last_run"] = finished_ts
            st["last_run_formatted"] = finished_fmt
            _save_state(st)
        except Exception:
            pass

def run_startup_checks(manifest_repos: List[str], steam_path: str, force: bool = False) -> None:
    """Runs full component synchronization in the background on startup."""
    def _worker():
        try:
            run_full_update_now(manifest_repos, steam_path, force=force)
        except Exception as e:
            logger.error(f"[Updater] Startup check worker error: {e}")

    t = threading.Thread(target=_worker, daemon=True, name="updater-startup")
    t.start()

def run_shutdown_checks(manifest_repos: List[str], steam_path: str) -> None:
    """Runs quick cleanup and state save on application shutdown."""
    try:
        logger.info("[Updater] Running shutdown checks and saving state...")
        state = _load_state()
        state["last_shutdown"] = time.time()
        _save_state(state)
    except Exception as e:
        logger.error(f"[Updater] Shutdown check failed: {e}")
