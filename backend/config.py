# %% [markdown]
# # Config Module
# Handles Windows Registry discovery, settings storage, and repo URLs.

# %%
import os
import json
import sys
from typing import Optional, List
from dataclasses import dataclass, field, asdict
from logger import logger

# %%
# Registry path constants
REG_KEY_CU = r"Software\Valve\Steam"
REG_KEY_LM = r"SOFTWARE\WOW6432Node\Valve\Steam"

def get_default_settings_path() -> str:
    appdata = os.environ.get("APPDATA")
    if appdata:
        target_dir = os.path.join(appdata, "SteaMRogue")
    else:
        target_dir = os.path.expanduser("~/.steamrogue")
    os.makedirs(target_dir, exist_ok=True)
    appdata_file = os.path.join(target_dir, "settings.json")
    if os.path.isfile("settings.json") and not os.path.isfile(appdata_file):
        try:
            import shutil
            shutil.copy2("settings.json", appdata_file)
        except Exception:
            pass
    return appdata_file

# %%
@dataclass
class AppConfig:
    steam_path: str = ""
    default_library: str = ""
    settings_file: str = field(default_factory=get_default_settings_path)
    manifest_repos: List[str] = field(default_factory=lambda: [
        "https://github.com/LightnigFast/ProjectLightningManifests",
        "https://github.com/SPIN0ZAi/SB_manifest_DB",
        "https://github.com/dvahana2424-web/sojogamesdatabase1",
        "https://github.com/SteamAutoCracks/ManifestHub"
    ])
    
    def load(self) -> None:
        """Loads configuration from settings.json or searches system defaults."""
        target_file = self.settings_file
        if not os.path.exists(target_file) and os.path.exists("settings.json"):
            target_file = "settings.json"

        if os.path.exists(target_file):
            try:
                with open(target_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.steam_path = data.get("steam_path", "")
                    self.default_library = data.get("default_library", "")
                    self.manifest_repos = data.get("manifest_repos", self.manifest_repos)
                    logger.debug(f"Loaded config from {target_file}")
                    if self.steam_path:
                        return
            except Exception as e:
                logger.error(f"Error loading {target_file}: {e}")
        
        # Discover Steam Path
        discovered = self.discover_steam_path()
        if discovered:
            self.steam_path = discovered
            self.save()
        else:
            logger.warning("Could not automatically discover Steam path.")

    def save(self) -> None:
        """Saves current configuration to settings.json in AppData."""
        try:
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(asdict(self), f, indent=4)
                logger.debug(f"Saved config to {self.settings_file}")
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")

    @staticmethod
    def discover_steam_path() -> Optional[str]:
        """Queries Windows registry to locate the Steam installation directory."""
        if sys.platform != "win32":
            logger.debug("Non-windows platform detected, registry search skipped.")
            return None
            
        import winreg
        
        # Try HKEY_CURRENT_USER first
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY_CU) as key:
                path, _ = winreg.QueryValueEx(key, "SteamPath")
                if path and os.path.isdir(path):
                    path = os.path.normpath(path)
                    logger.info(f"Steam path discovered in HKCU: {path}")
                    return path
        except OSError:
            logger.debug("Failed querying HKCU SteamPath registry key.")
            
        # Try HKEY_LOCAL_MACHINE WOW6432Node second
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, REG_KEY_LM) as key:
                path, _ = winreg.QueryValueEx(key, "InstallPath")
                if path and os.path.isdir(path):
                    path = os.path.normpath(path)
                    logger.info(f"Steam path discovered in HKLM: {path}")
                    return path
        except OSError:
            logger.debug("Failed querying HKLM InstallPath registry key.")

        # Check common folders across drives
        common_locations = [
            r"C:\Program Files (x86)\Steam",
            r"C:\Program Files\Steam",
            r"C:\Steam",
            r"D:\Steam",
            r"E:\Steam",
            r"F:\Steam",
        ]
        for loc in common_locations:
            if os.path.isdir(loc):
                logger.info(f"Steam path discovered in common locations: {loc}")
                return loc
            
        return None

# %%
# Global configuration instance
config = AppConfig()
config.load()
