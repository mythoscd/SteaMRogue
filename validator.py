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
        return ("steam.exe" in output) or ("steamwebhelper.exe" in output)
    except Exception as e:
        logger.debug(f"Failed checking process list for Steam status: {e}")
        return False

# %%
def kill_steam() -> bool:
    """Gracefully terminates Steam via '-shutdown' first, falling back to force kill."""
    if sys.platform != "win32":
        return False
        
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        flags = 0x08000000
        
        # 1. Try graceful shutdown first via steam.exe -shutdown
        steam_exe = None
        for p in [r"C:\Program Files (x86)\Steam\steam.exe", r"C:\Program Files\Steam\steam.exe"]:
            if os.path.isfile(p):
                steam_exe = p
                break
        if steam_exe:
            try:
                subprocess.run(
                    f'"{steam_exe}" -shutdown',
                    shell=True,
                    startupinfo=startupinfo,
                    creationflags=flags,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=3.0
                )
            except Exception:
                pass
                
        # 2. Wait up to 3 seconds for graceful shutdown to finish
        import time
        for _ in range(6):
            if not is_steam_running():
                logger.info("Steam exited gracefully via -shutdown.")
                return True
            time.sleep(0.5)

        # 3. If still running, force terminate lingering processes
        for cmd in [
            'taskkill /F /T /IM steam.exe',
            'taskkill /F /IM steamwebhelper.exe',
            'taskkill /F /IM gameoverlayui.exe'
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

# %%
def cleanup_steam_crashes(steam_path: str) -> bool:
    """Cleans lingering .crash flag in Steam directory and crashed CEF htmlcache in LocalAppData."""
    cleaned = False
    if steam_path and os.path.isdir(steam_path):
        crash_file = os.path.join(steam_path, ".crash")
        if os.path.isfile(crash_file):
            try:
                os.remove(crash_file)
                logger.info("[cleanup_steam_crashes] Removed lingering .crash flag.")
                cleaned = True
            except Exception:
                pass

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
            except Exception:
                pass
    return cleaned

# %%
def launch_steam(steam_exe: str) -> bool:
    """Launches Steam client with normal interactive GUI via Windows Shell."""
    if not steam_exe or not os.path.isfile(steam_exe):
        logger.error(f"Cannot launch Steam, invalid executable: {steam_exe}")
        return False
        
    steam_dir = os.path.dirname(steam_exe)
    logger.info(f"Launching Steam with GUI: {steam_exe} (cwd: {steam_dir})")

    # Clean any lingering .crash file so Steam doesn't enter recovery mode
    crash_file = os.path.join(steam_dir, ".crash")
    if os.path.isfile(crash_file):
        try:
            os.remove(crash_file)
            logger.info("Removed lingering .crash flag.")
        except Exception:
            pass

    # Ensure htmlcache is clean if previously crashed
    local_appdata = os.environ.get("LOCALAPPDATA", "")
    if local_appdata:
        cef_htmlcache = os.path.join(local_appdata, "Steam", "htmlcache")
        local_state = os.path.join(cef_htmlcache, "Local State")
        if os.path.isfile(local_state):
            try:
                with open(local_state, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    if '"crashed":true' in content or '"exit_type":"Crashed"' in content:
                        import shutil
                        shutil.rmtree(cef_htmlcache, ignore_errors=True)
                        logger.info("Cleared crashed CEF htmlcache before launch.")
            except Exception:
                pass

    # Find official shortcut if available (launching via shortcut guarantees desktop shell interactive context)
    shortcut_candidates = [
        os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs\Steam\Steam.lnk"),
        os.path.join(os.environ.get("PROGRAMDATA", ""), r"Microsoft\Windows\Start Menu\Programs\Steam\Steam.lnk"),
        os.path.join(os.environ.get("PUBLIC", ""), r"Desktop\Steam.lnk"),
        os.path.join(os.environ.get("USERPROFILE", ""), r"Desktop\Steam.lnk")
    ]
    target_to_launch = steam_exe
    for sc in shortcut_candidates:
        if os.path.isfile(sc):
            target_to_launch = sc
            break

    # 1. Native Windows ShellExecute via ctypes with SW_SHOWNORMAL (1) - NO ARGS
    try:
        import ctypes
        res = ctypes.windll.shell32.ShellExecuteW(
            None, "open", target_to_launch, None, steam_dir, 1
        )
        if res > 32:
            logger.info(f"Launched Steam successfully via ShellExecuteW ({target_to_launch}).")
            return True
        else:
            logger.warning(f"ShellExecuteW returned code {res}")
    except Exception as e:
        logger.warning(f"ShellExecuteW failed: {e}")

    # 2. Native os.startfile
    try:
        os.startfile(target_to_launch)
        logger.info(f"Launched Steam successfully via os.startfile ({target_to_launch}).")
        return True
    except Exception as e:
        logger.warning(f"os.startfile failed: {e}")

    # 3. Fallback: cmd.exe start (runs via Windows Shell with SW_SHOWNORMAL)
    try:
        subprocess.Popen(
            f'cmd.exe /c start "" "{steam_exe}"',
            cwd=steam_dir,
            shell=True,
            creationflags=0x00000008 | 0x00000200
        )
        logger.info("Launched Steam successfully via cmd.exe start.")
        return True
    except Exception as ex:
        logger.error(f"Failed to launch Steam: {ex}")
        return False
