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
    """Checks if steam.exe is currently running on the system."""
    if sys.platform != "win32":
        return False
        
    try:
        # Run tasklist command filtering for steam.exe
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        output = subprocess.check_output(
            'tasklist /FI "IMAGENAME eq steam.exe" /NH',
            shell=True,
            startupinfo=startupinfo,
            encoding="utf-8",
            errors="ignore"
        )
        return "steam.exe" in output.lower()
    except Exception as e:
        logger.debug(f"Failed checking process list for Steam status: {e}")
        return False

# %%
def kill_steam() -> bool:
    """Attempts to kill steam.exe, its process tree, and steamwebhelper cleanly."""
    if sys.platform != "win32":
        return False
        
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        flags = 0x08000000
        
        for cmd in ['taskkill /F /T /IM steam.exe', 'taskkill /F /IM steamwebhelper.exe']:
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
        logger.info("Sent clean termination signal to steam.exe and steamwebhelper.exe.")
        return True
    except Exception as e:
        logger.error(f"Failed to close Steam: {e}")
        return False
