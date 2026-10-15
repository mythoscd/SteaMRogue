# %% [markdown]
# # Validator Module
# Validates Steam path structures, AppID numbers, and verifies if Steam is running.

# %%
import os
import sys
import subprocess
import re
from typing import Union
from exceptions import AppIdValidationError, SteamPathNotFoundError
from logger import logger

# %%
def extract_appid(input_val: Union[str, int]) -> str:
    """Extracts numeric AppID from raw string, integer, or Steam URL."""
    if not input_val:
        return ""
    clean = str(input_val).strip()
    if clean.isdigit():
        return clean
    match = re.search(r"(?:store\.steampowered\.com/app|steamdb\.info/app|steamcommunity\.com/app|app)/(\d+)", clean, re.IGNORECASE)
    if match:
        return match.group(1)
    uri_match = re.search(r"steam://store/(\d+)", clean, re.IGNORECASE)
    if uri_match:
        return uri_match.group(1)
    return clean

# %%
def validate_appid(appid: Union[str, int]) -> str:
    """Validates the format of Steam AppID, supporting direct IDs and store links."""
    clean_id = extract_appid(appid)
    if not clean_id.isdigit():
        logger.error(f"AppID validation failed for input: '{appid}' (must be numeric or valid link)")
        raise AppIdValidationError(f"AppID veya link '{appid}' geçersiz. Lütfen geçerli bir sayısal AppID veya Steam linki girin.")
    return clean_id

# %%
def validate_steam_path(path: str) -> str:
    """Validates that the directory is a valid Steam installation folder."""
    if not path or not os.path.isdir(path):
        logger.error(f"Steam path does not exist or is not a directory: '{path}'")
        raise SteamPathNotFoundError(f"Directory '{path}' does not exist.")
        
    # Check for core Steam files
    steam_exe = os.path.join(path, "steam.exe")
    steamapps_dir = os.path.join(path, "steamapps")
    
    if not os.path.isfile(steam_exe) and not os.path.isdir(steamapps_dir):
        logger.warning(f"Directory '{path}' is missing steam.exe or steamapps folder. It might not be a valid installation.")
        
    return os.path.normpath(path)

# %%
def is_steam_running() -> bool:
    """Checks whether any Steam client or CEF process is currently running."""
    if sys.platform != "win32":
        return False
        
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        flags = 0x08000000
        
        output = subprocess.check_output(
            'tasklist /NH',
            shell=True,
            startupinfo=startupinfo,
            creationflags=flags,
            encoding="utf-8",
            errors="ignore"
        ).lower()
        return ("steam.exe" in output) or ("steamwebhelper.exe" in output) or ("steamservice.exe" in output)
    except Exception as e:
        logger.debug(f"Failed checking process list for Steam status: {e}")
        return False

# %%
def resolve_steam_exe(steam_path: Optional[str] = None) -> Optional[str]:
    """Finds the absolute path to steam.exe via explicit path, Windows registry, or standard locations."""
    if steam_path and os.path.isdir(steam_path):
        cand = os.path.join(steam_path, "steam.exe")
        if os.path.isfile(cand):
            return os.path.normpath(cand)
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as key:
            val, _ = winreg.QueryValueEx(key, "SteamExe")
            if val and os.path.isfile(val):
                return os.path.normpath(val)
    except Exception:
        pass
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as key:
            val, _ = winreg.QueryValueEx(key, "SteamPath")
            if val:
                cand = os.path.join(val, "steam.exe")
                if os.path.isfile(cand):
                    return os.path.normpath(cand)
    except Exception:
        pass
    for p in [r"C:\Program Files (x86)\Steam\steam.exe", r"C:\Program Files\Steam\steam.exe"]:
        if os.path.isfile(p):
            return os.path.normpath(p)
    return None

# %%
def kill_steam(steam_path: Optional[str] = None) -> bool:
    """Gracefully terminates Steam via '-shutdown' first, falling back to force kill."""
    if sys.platform != "win32":
        return False
        
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        flags = 0x08000000
        
        # 1. Resolve steam_exe
        steam_exe = resolve_steam_exe(steam_path)

        if steam_exe:
            try:
                subprocess.run(
                    f'"{steam_exe}" -shutdown',
                    shell=True,
                    startupinfo=startupinfo,
                    creationflags=flags,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=4.0
                )
            except Exception:
                pass
                
        # 2. Wait up to 8 seconds for graceful shutdown to finish
        import time
        for _ in range(16):
            if not is_steam_running():
                logger.info("Steam exited gracefully via -shutdown.")
                if steam_exe:
                    cleanup_steam_crashes(os.path.dirname(steam_exe))
                return True
            time.sleep(0.5)

        # 3. If still running after 8s, force terminate lingering processes
        for cmd in [
            'taskkill /F /T /IM steam.exe',
            'taskkill /F /IM steamwebhelper.exe',
            'taskkill /F /IM gameoverlayui.exe',
            'taskkill /F /IM steamservice.exe'
        ]:
            try:
                subprocess.run(
                    cmd,
                    shell=True,
                    startupinfo=startupinfo,
                    creationflags=flags,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            except Exception:
                pass
        time.sleep(0.5)
        if steam_exe:
            cleanup_steam_crashes(os.path.dirname(steam_exe))
        logger.info("Sent termination signals to lingering steam processes.")
        return True
    except Exception as e:
        logger.error(f"Failed to close Steam: {e}")
        return False

# %%
def wait_for_steam_exit(timeout: float = 6.0) -> bool:
    """Waits until all Steam processes (both steam.exe and steamwebhelper.exe) have completely exited."""
    import time
    start = time.time()
    while time.time() - start < timeout:
        if not is_steam_running():
            return True
        time.sleep(0.3)
    return not is_steam_running()

def ensure_opensteamtool_signatures(steam_path: str) -> bool:
    """
    Ensures OpenSteamTool signature files (.toml) exist for the current Steam build.
    Only downloads verified upstream signatures from steam-monitor repo.
    """
    if not steam_path or not os.path.isdir(steam_path):
        return False

    ost_dir = os.path.join(steam_path, "opensteamtool")
    if not os.path.isdir(ost_dir):
        return False

    import hashlib

    def get_sha256(file_path):
        if not os.path.isfile(file_path):
            return None
        h = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                while chunk := f.read(65536):
                    h.update(chunk)
            return h.hexdigest().lower()
        except Exception:
            return None

    steamui_path = os.path.join(steam_path, "steamui.dll")
    steamclient64_path = os.path.join(steam_path, "steamclient64.dll")

    hash_ui = get_sha256(steamui_path)
    hash_client = get_sha256(steamclient64_path)

    synced_any = False

    targets = []
    if hash_ui:
        targets.append(("pattern", "steamui", hash_ui))
    if hash_client:
        targets.append(("pattern", "steamclient", hash_client))
        targets.append(("ipc", "steamclient", hash_client))

    for channel, comp, sha in targets:
        comp_dir = os.path.join(ost_dir, channel, comp)
        os.makedirs(comp_dir, exist_ok=True)
        target_file = os.path.join(comp_dir, f"{sha}.toml")

        # Clean unverified/obsolete steamui signature that disrupts UI frame loop
        if comp == "steamui" and sha == "1b9457943205dc3af0bd53463ba331cbd2a381388699705c02271aac7a2b1252" and os.path.isfile(target_file):
            try:
                os.remove(target_file)
                logger.info(f"[OST Signatures] Removed unverified steamui signature: {sha}.toml")
            except Exception:
                pass
            continue

        # If file already exists and is non-empty, keep it
        if os.path.isfile(target_file) and os.path.getsize(target_file) > 100:
            continue

        downloaded = False
        try:
            import requests
            url = f"https://raw.githubusercontent.com/OpenSteam001/steam-monitor/{channel}/{comp}/{sha}.toml"
            resp = requests.get(url, timeout=2.0)
            if resp.status_code == 200 and len(resp.content) > 100:
                with open(target_file, "wb") as f_out:
                    f_out.write(resp.content)
                logger.info(f"[OST Signatures] Downloaded upstream {channel}/{comp}/{sha}.toml")
                downloaded = True
                synced_any = True
        except Exception:
            pass

    return synced_any

# %%
def cleanup_steam_crashes(steam_path: str) -> bool:
    """Cleans lingering .crash flag, stale ActiveProcess pid, redundant proxy DLLs, crashed CEF htmlcache, and adapts OpenSteamTool signatures."""
    cleaned = False
    if steam_path and os.path.isdir(steam_path):
        # 1. Clean .crash flag
        crash_file = os.path.join(steam_path, ".crash")
        if os.path.isfile(crash_file):
            try:
                os.remove(crash_file)
                logger.info("[cleanup_steam_crashes] Removed lingering .crash flag.")
                cleaned = True
            except Exception:
                pass

        # 2. Prevent VGUI_Setup failed error: dwmapi.dll proxy in Steam folder causes circular export
        # forwarder failure when 64-bit vgui2_s.dll imports DWMAPI. Always remove dwmapi.dll.
        dwmapi_path = os.path.join(steam_path, "dwmapi.dll")
        if os.path.isfile(dwmapi_path):
            try:
                os.remove(dwmapi_path)
                logger.info("[cleanup_steam_crashes] Removed dwmapi.dll to prevent VGUI_Setup failed crash.")
                cleaned = True
            except Exception:
                pass

        # 3. Ensure OpenSteamTool.dll modal MessageBoxA is silenced (NOP'd) to prevent startup freezing
        ost_dll = os.path.join(steam_path, "OpenSteamTool.dll")
        if os.path.isfile(ost_dll):
            try:
                with open(ost_dll, "r+b") as f_ost:
                    f_ost.seek(0x7423b)
                    b_check = f_ost.read(6)
                    if b_check == bytes.fromhex("ff15d7d60700"):
                        f_ost.seek(0x7423b)
                        f_ost.write(bytes.fromhex("909090909090"))
                        logger.info("[cleanup_steam_crashes] Silenced modal MessageBoxA in OpenSteamTool.dll.")
                        cleaned = True
            except Exception as oe:
                logger.debug(f"[cleanup_steam_crashes] OpenSteamTool patch error: {oe}")

        # 4. Ensure OpenSteamTool signatures match current Steam DLL hashes to prevent modal error popups
        try:
            ensure_opensteamtool_signatures(steam_path)
        except Exception as se:
            logger.debug(f"[cleanup_steam_crashes] signature check error: {se}")

    # 5. Clean stale ActiveProcess PID in Registry if Steam is not running
    try:
        if not is_steam_running():
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam\ActiveProcess", 0, winreg.KEY_READ | winreg.KEY_SET_VALUE) as key:
                cur_pid, _ = winreg.QueryValueEx(key, "pid")
                if cur_pid != 0:
                    winreg.SetValueEx(key, "pid", 0, winreg.REG_DWORD, 0)
                    logger.info("[cleanup_steam_crashes] Reset stale ActiveProcess pid to 0.")
                    cleaned = True
    except Exception as re:
        logger.debug(f"[cleanup_steam_crashes] ActiveProcess check: {re}")

    # 6. Clean CEF htmlcache and sanitize Local State
    local_appdata = os.environ.get("LOCALAPPDATA", "")
    if local_appdata:
        cef_htmlcache = os.path.join(local_appdata, "Steam", "htmlcache")
        local_state = os.path.join(cef_htmlcache, "Local State")
        if os.path.isfile(local_state):
            try:
                with open(local_state, "r", encoding="utf-8", errors="ignore") as f:
                    content_ls = f.read()
                if '"crashed":true' in content_ls or '"exit_type":"Crashed"' in content_ls:
                    import shutil
                    shutil.rmtree(cef_htmlcache, ignore_errors=True)
                    logger.info("[cleanup_steam_crashes] Cleared crashed CEF htmlcache.")
                    cleaned = True
                elif '"variations_crash_streak"' in content_ls:
                    import json
                    ls_json = json.loads(content_ls)
                    if ls_json.get("variations_crash_streak", 0) > 0:
                        ls_json["variations_crash_streak"] = 0
                        if "user_experience_metrics" in ls_json and "stability" in ls_json["user_experience_metrics"]:
                            ls_json["user_experience_metrics"]["stability"]["exited_cleanly"] = True
                        with open(local_state, "w", encoding="utf-8") as f_out:
                            json.dump(ls_json, f_out)
                        cleaned = True
            except Exception:
                pass
    return cleaned

# %%
def launch_steam(steam_exe: str) -> bool:
    """Launches Steam client cleanly and directly with interactive GUI."""
    if not steam_exe or not os.path.isfile(steam_exe):
        logger.error(f"Cannot launch Steam, invalid executable: {steam_exe}")
        return False
        
    steam_dir = os.path.dirname(steam_exe)
    logger.info(f"Launching Steam: {steam_exe} (cwd: {steam_dir})")

    # 1. Clean crash residues, adapt OpenSteamTool signatures, and reset stale mutexes
    cleanup_steam_crashes(steam_dir)

    # 2. Clean environment without PyInstaller temp _MEI directories in PATH
    clean_env = os.environ.copy()
    if "PATH" in clean_env:
        paths = clean_env["PATH"].split(os.pathsep)
        clean_paths = [p for p in paths if "_MEI" not in p and "SteamTools_Auto" not in p]
        clean_env["PATH"] = os.pathsep.join(clean_paths)

    launched = False

    # Ensure current working directory is steam_dir so Steam finds its bin\ modules
    try:
        os.chdir(steam_dir)
    except Exception:
        pass

    # 3. Priority 1: Native Windows ShellExecuteW with explicit steam_dir working directory (SW_SHOWNORMAL = 1)
    try:
        import ctypes
        res = ctypes.windll.shell32.ShellExecuteW(
            None, "open", steam_exe, None, steam_dir, 1
        )
        if res > 32:
            logger.info(f"Launched Steam successfully via ShellExecuteW ({steam_exe}) in cwd ({steam_dir}).")
            launched = True
        else:
            logger.warning(f"ShellExecuteW returned code {res}")
    except Exception as e:
        logger.warning(f"ShellExecuteW failed: {e}")

    # 4. Priority 2: Native os.startfile (after os.chdir to steam_dir)
    if not launched:
        try:
            os.startfile(steam_exe)
            logger.info(f"Launched Steam successfully via os.startfile ({steam_exe}).")
            launched = True
        except Exception as e:
            logger.warning(f"os.startfile failed: {e}")

    # 5. Priority 3: Detached subprocess fallback with cwd=steam_dir and CREATE_BREAKAWAY_FROM_JOB
    if not launched:
        try:
            CREATE_BREAKAWAY_FROM_JOB = 0x01000000
            DETACHED_PROCESS = 0x00000008
            CREATE_NEW_PROCESS_GROUP = 0x00000200
            subprocess.Popen(
                [steam_exe],
                cwd=steam_dir,
                env=clean_env,
                creationflags=CREATE_BREAKAWAY_FROM_JOB | DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
                close_fds=True
            )
            logger.info("Launched Steam successfully via detached subprocess with breakaway.")
            launched = True
        except Exception as ex:
            logger.error(f"Failed to launch Steam via detached subprocess: {ex}")

    # 6. Verification: Wait up to 6 seconds to verify Steam process is running
    import time
    for _ in range(12):
        if is_steam_running():
            logger.info("Verified Steam process is actively running.")
            return True
        time.sleep(0.5)

    return launched

