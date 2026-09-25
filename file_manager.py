# %% [markdown]
# # File Manager Module
# Manages file copying, ACF manifest generation, and libraryfolders.vdf modification with backups.

# %%
import os
import re
import shutil
import time
from typing import Dict, List, Any, Tuple, Optional
from logger import logger
from exceptions import VdfParseError, BackupRestoreError

# %%
class VdfParser:
    """Simple and robust parser and serializer for Valve Data Format (VDF) files."""
    
    @staticmethod
    def parse(text: str) -> Dict[str, Any]:
        """Parses VDF string into a nested Python dictionary."""
        # Tokenize by quoting, braces, or non-whitespace words
        tokens = re.findall(r'"[^"]*"|[{}]|[^\s{}]+', text)
        token_iter = iter(tokens)
        
        def parse_node(iterator) -> Dict[str, Any]:
            node = {}
            for token in iterator:
                if token == '}':
                    return node
                elif token == '{':
                    continue
                else:
                    key = token.strip('"')
                    try:
                        next_token = next(iterator)
                    except StopIteration:
                        raise VdfParseError("Unexpected end of VDF content.")
                        
                    if next_token == '{':
                        node[key] = parse_node(iterator)
                    else:
                        node[key] = next_token.strip('"')
            return node
            
        try:
            return parse_node(token_iter)
        except Exception as e:
            raise VdfParseError(f"Error parsing VDF format: {e}")

    @staticmethod
    def serialize(data: Dict[str, Any], indent: int = 0) -> str:
        """Serializes a nested Python dictionary back into a VDF string format."""
        lines = []
        tabs = "\t" * indent
        for k, v in data.items():
            if isinstance(v, dict):
                lines.append(f'{tabs}"{k}"')
                lines.append(f'{tabs}{{')
                lines.append(VdfParser.serialize(v, indent + 1))
                lines.append(f'{tabs}}}')
            else:
                lines.append(f'{tabs}"{k}"\t\t"{v}"')
        return "\n".join(lines)

# %%
class FileManager:
    """Handles file operations for Steam configurations, manifests, and library database updates."""

    @staticmethod
    def backup_file(file_path: str) -> str:
        """Creates a backup of a file. Returns the backup file path."""
        if not os.path.exists(file_path):
            raise BackupRestoreError(f"Cannot backup file. Path does not exist: {file_path}")
            
        backup_path = file_path + ".bak"
        try:
            shutil.copy2(file_path, backup_path)
            logger.info(f"Backup created successfully: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Failed to create backup of {file_path}: {e}")
            raise BackupRestoreError(f"Failed to create backup: {e}")

    @staticmethod
    def restore_file(file_path: str) -> None:
        """Restores a file from its backup version if it exists."""
        backup_path = file_path + ".bak"
        if not os.path.exists(backup_path):
            raise BackupRestoreError(f"Backup file does not exist: {backup_path}")
            
        try:
            shutil.copy2(backup_path, file_path)
            logger.info(f"File restored successfully from backup: {file_path}")
        except Exception as e:
            logger.error(f"Failed to restore file {file_path} from backup: {e}")
            raise BackupRestoreError(f"Failed to restore file: {e}")

    @classmethod
    def get_library_folders(cls, steam_path: str) -> List[Tuple[str, str]]:
        """Parses libraryfolders.vdf and returns a list of library indices and directory paths.
        
        Returns:
            List of (index_string, library_path) tuples.
        """
        vdf_path = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
        if not os.path.exists(vdf_path):
            # Fallback to config/libraryfolders.vdf
            vdf_path_config = os.path.join(steam_path, "config", "libraryfolders.vdf")
            if os.path.exists(vdf_path_config):
                vdf_path = vdf_path_config
            else:
                return [("0", steam_path)]
            
        try:
            with open(vdf_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            parsed = VdfParser.parse(content)
            folders = parsed.get("libraryfolders", {})
            
            library_list = []
            for idx, info in folders.items():
                if isinstance(info, dict) and "path" in info:
                    library_list.append((idx, os.path.normpath(info["path"])))
            
            return library_list
        except Exception as e:
            logger.error(f"Failed reading library folders: {e}")
            return [("0", steam_path)]

    @classmethod
    def update_library_folders(cls, steam_path: str, appid: str, library_idx: str = "0") -> None:
        """Adds the AppID to the specified library folder inside libraryfolders.vdf."""
        vdf_path = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
        if not os.path.exists(vdf_path):
            vdf_path_config = os.path.join(steam_path, "config", "libraryfolders.vdf")
            if os.path.exists(vdf_path_config):
                vdf_path = vdf_path_config
            else:
                logger.warning(f"libraryfolders.vdf not found at {vdf_path}. Skipping VDF update.")
                return
            
        # Take backup before modification
        cls.backup_file(vdf_path)
        
        try:
            with open(vdf_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            parsed = VdfParser.parse(content)
            
            # Navigate to libraryfolders -> index -> apps
            folders = parsed.setdefault("libraryfolders", {})
            lib_info = folders.setdefault(library_idx, {})
            apps = lib_info.setdefault("apps", {})
            
            # Add or update app ID (value is typically game size on disk, default 0 or dummy)
            apps[appid] = "0"
            
            serialized = VdfParser.serialize(parsed)
            with open(vdf_path, "w", encoding="utf-8") as f:
                f.write(serialized)
                
            logger.info(f"Registered AppID {appid} in libraryfolders.vdf (library {library_idx})")
        except Exception as e:
            logger.error(f"Failed to update libraryfolders.vdf: {e}")
            # Try to restore from backup
            try:
                cls.restore_file(vdf_path)
            except Exception:
                pass
            raise VdfParseError(f"Could not update libraryfolders.vdf: {e}")

    @classmethod
    def remove_from_library_folders(cls, steam_path: str, appid: str) -> None:
        """Removes the AppID from all libraries in libraryfolders.vdf."""
        vdf_path = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
        if not os.path.exists(vdf_path):
            vdf_path_config = os.path.join(steam_path, "config", "libraryfolders.vdf")
            if os.path.exists(vdf_path_config):
                vdf_path = vdf_path_config
            else:
                return
            
        try:
            with open(vdf_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            parsed = VdfParser.parse(content)
            folders = parsed.get("libraryfolders", {})
            modified = False
            
            for idx, lib_info in folders.items():
                if isinstance(lib_info, dict) and "apps" in lib_info:
                    apps = lib_info["apps"]
                    if appid in apps:
                        del apps[appid]
                        modified = True
                        logger.info(f"Removed AppID {appid} from library folders index {idx}")
                        
            if modified:
                cls.backup_file(vdf_path)
                serialized = VdfParser.serialize(parsed)
                with open(vdf_path, "w", encoding="utf-8") as f:
                    f.write(serialized)
        except Exception as e:
            logger.error(f"Failed to remove AppID from libraryfolders.vdf: {e}")

    @classmethod
    def write_steamtools_files(cls, steam_path: str, manifests: List[Dict[str, Any]], luas: List[Dict[str, Any]]) -> List[str]:
        """Writes downloaded manifest and LUA files to their corresponding SteamTools directories."""
        written_files = []
        
        # Define paths
        plugin_folder = os.path.join(steam_path, "config", "stplug-in")
        depotcache_folder = os.path.join(steam_path, "config", "depotcache")
        lua_folder = os.path.join(steam_path, "config", "lua")
        official_depotcache = os.path.join(steam_path, "depotcache")
        
        # Ensure directories exist
        for folder in [plugin_folder, depotcache_folder, lua_folder, official_depotcache]:
            os.makedirs(folder, exist_ok=True)
            
        # Write .manifest files to BOTH SteamTools depotcache and Steam's official depotcache
        for item in manifests:
            name = item["name"]
            content = item["content"]
            
            # Destination 1: config/depotcache
            dest1 = os.path.join(depotcache_folder, name)
            with open(dest1, "wb") as f:
                f.write(content)
            written_files.append(dest1)
            
            # Destination 2: official depotcache
            dest2 = os.path.join(official_depotcache, name)
            with open(dest2, "wb") as f:
                f.write(content)
            written_files.append(dest2)
            
            logger.info(f"Saved manifest: {name}")
            
        # Write LUA scripts to config/stplug-in and config/lua
        for item in luas:
            name = item["name"]
            content = item["content"]
            
            # Destination 1: config/stplug-in
            dest1 = os.path.join(plugin_folder, name)
            with open(dest1, "wb") as f:
                f.write(content)
            written_files.append(dest1)
            
            # Destination 2: config/lua
            dest2 = os.path.join(lua_folder, name)
            with open(dest2, "wb") as f:
                f.write(content)
            written_files.append(dest2)
            
            logger.info(f"Saved LUA config: {name}")
            
        return written_files

    @classmethod
    def clean_game_files(cls, steam_path: str, appid: str) -> None:
        """Deletes .manifest, .lua, and appmanifest ACF files for a specific AppID."""
        plugin_folder = os.path.join(steam_path, "config", "stplug-in")
        depotcache_folder = os.path.join(steam_path, "config", "depotcache")
        lua_folder = os.path.join(steam_path, "config", "lua")
        official_depotcache = os.path.join(steam_path, "depotcache")
        
        # 1. Clean LUA configurations
        lua_name = f"{appid}.lua"
        for folder in [plugin_folder, lua_folder]:
            file_path = os.path.join(folder, lua_name)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"Deleted LUA file: {file_path}")
                except Exception as e:
                    logger.warning(f"Could not delete LUA file {file_path}: {e}")
                    
        # 2. Clean manifest files in depotcache
        # Look for files starting with appid_ in depotcache folders
        for folder in [depotcache_folder, official_depotcache]:
            if not os.path.isdir(folder):
                continue
            try:
                for file in os.listdir(folder):
                    if file.lower().endswith(".manifest") and file.startswith(f"{appid}_"):
                        file_path = os.path.join(folder, file)
                        try:
                            os.remove(file_path)
                            logger.info(f"Deleted manifest file: {file_path}")
                        except Exception as e:
                            logger.warning(f"Could not delete manifest file {file_path}: {e}")
            except Exception as e:
                logger.debug(f"Error listing folder {folder} during clean: {e}")

        # 3. Clean appmanifest ACF file from libraries
        cls.clean_acf_manifests(steam_path, appid)

    @classmethod
    def clean_acf_manifests(cls, steam_path: str, appid: str) -> None:
        """Removes appmanifest ACF files for a specific AppID from all Steam libraries."""
        libs = cls.get_library_folders(steam_path)
        acf_name = f"appmanifest_{appid}.acf"
        for _, lib_path in libs:
            acf_path = os.path.join(lib_path, "steamapps", acf_name)
            if os.path.exists(acf_path):
                try:
                    os.remove(acf_path)
                    logger.info(f"Deleted manifest ACF: {acf_path}")
                except Exception as e:
                    logger.warning(f"Could not delete ACF file {acf_path}: {e}")

    @classmethod
    def generate_acf_manifest(
        cls, 
        library_path: str, 
        appid: str, 
        game_name: str, 
        manifests: List[Dict[str, Any]] = None
    ) -> str:
        """Auto-generates appmanifest_<AppID>.acf file under steamapps folder.
        
        Parses manifest file list to populate InstalledDepots if available.
        """
        dest_dir = os.path.join(library_path, "steamapps")
        os.makedirs(dest_dir, exist_ok=True)
        acf_path = os.path.join(dest_dir, f"appmanifest_{appid}.acf")
        
        # Sanitize installdir from game name (letters, digits, spaces only)
        installdir = re.sub(r'[^a-zA-Z0-9\s\-\_]', '', game_name).strip()
        if not installdir:
            installdir = f"SteamApp_{appid}"
            
        current_time = int(time.time())
        
        # Extract depots from manifest filenames
        depot_entries = []
        if manifests:
            for item in manifests:
                # Name: <DepotID>_<ManifestID>.manifest
                match = re.match(r'^(\d+)_(\d+)\.manifest$', item["name"], re.IGNORECASE)
                if match:
                    depot_id = match.group(1)
                    manifest_id = match.group(2)
                    depot_entries.append(f'\t\t"{depot_id}"')
                    depot_entries.append("\t\t{")
                    depot_entries.append(f'\t\t\t"manifest"\t\t"{manifest_id}"')
                    depot_entries.append('\t\t\t"size"\t\t"0"')
                    depot_entries.append("\t\t}")
                    
        depots_str = "\n".join(depot_entries) if depot_entries else ""
        
        acf_content = f'''"AppState"
{{
	"appid"		"{appid}"
	"Universe"		"1"
	"name"		"{game_name}"
	"StateFlags"		"1"
	"installdir"		"{installdir}"
	"LastUpdated"		"{current_time}"
	"LastPlayed"		"0"
	"SizeOnDisk"		"0"
	"buildid"		"12345678"
	"BytesToDownload"		"0"
	"BytesDownloaded"		"0"
	"BytesToStage"		"0"
	"BytesStaged"		"0"
	"TargetBuildID"		"12345678"
	"ProjectLightning"		"1"
	"AutoUpdateBehavior"		"0"
	"AllowOtherDownloadsWhileRunning"		"0"
	"InstalledDepots"
	{{
{depots_str}
	}}
	"UserConfig"
	{{
	}}
}}
'''
        # If ACF already exists, backup
        if os.path.exists(acf_path):
            cls.backup_file(acf_path)
            
        with open(acf_path, "w", encoding="utf-8") as f:
            f.write(acf_content)
            
        logger.info(f"Generated appmanifest file: {acf_path}")
        return acf_path
