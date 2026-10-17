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
            
        # Automatically repair and ensure all manifests are pinned to depots
        cls.repair_stplugin_luas(steam_path)
        return written_files

    @classmethod
    def repair_stplugin_luas(cls, steam_path: str) -> int:
        """Inspects all LUA files in config/stplug-in and config/lua.
        If any depot has a matching manifest in depotcache (or config/depotcache)
        but the LUA is missing setManifestid, injects setManifestid so Steam
        never requests unauthorized manifest codes from Valve servers."""
        plugin_folder = os.path.join(steam_path, "config", "stplug-in")
        lua_folder = os.path.join(steam_path, "config", "lua")
        depotcache_folder = os.path.join(steam_path, "config", "depotcache")
        official_depotcache = os.path.join(steam_path, "depotcache")

        if not os.path.isdir(plugin_folder):
            return 0

        # Collect all available manifests: depot_id -> gid
        depot_manifests = {}
        for d_folder in [depotcache_folder, official_depotcache]:
            if os.path.isdir(d_folder):
                try:
                    for fname in os.listdir(d_folder):
                        m = re.match(r"^(\d+)_(\d+)\.manifest$", fname, re.IGNORECASE)
                        if m:
                            depot_id, gid = m.groups()
                            depot_manifests[depot_id] = gid
                except Exception as e:
                    logger.debug(f"Error scanning depotcache folder {d_folder}: {e}")

        fixed_count = 0
        try:
            for fname in os.listdir(plugin_folder):
                if not fname.lower().endswith(".lua"):
                    continue
                lua_path = os.path.join(plugin_folder, fname)
                try:
                    with open(lua_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    depots = re.findall(r"addappid\((\d+)", content)
                    modified = False
                    lines = content.splitlines()

                    # Normalize addappid calls to have license flag 1 (full license)
                    new_lines = []
                    for line in lines:
                        l_sub = re.sub(r'^(\s*addappid\s*\(\s*\d+)\s*\)', r'\1, 1)', line)
                        l_sub = re.sub(r'^(\s*addappid\s*\(\s*\d+\s*),\s*0\s*,', r'\1, 1,', l_sub)
                        if l_sub != line:
                            modified = True
                        new_lines.append(l_sub)
                    lines = new_lines

                    for d in depots:
                        if d in depot_manifests:
                            pattern = rf"setManifestid\s*\(\s*['\"]?{d}['\"]?\s*,"
                            if not re.search(pattern, content, re.IGNORECASE):
                                gid = depot_manifests[d]
                                line_to_add = f'setManifestid({d}, "{gid}")'
                                # Find index of addappid(d
                                idx_to_insert = -1
                                for idx, line in enumerate(lines):
                                    if f"addappid({d}" in line:
                                        idx_to_insert = idx + 1
                                        break
                                if idx_to_insert != -1:
                                    lines.insert(idx_to_insert, line_to_add)
                                else:
                                    lines.append(line_to_add)
                                modified = True
                                fixed_count += 1
                                logger.info(f"Auto-pinned manifest in {fname}: {line_to_add}")

                    if modified:
                        new_content = "\n".join(lines)
                        with open(lua_path, "w", encoding="utf-8") as f:
                            f.write(new_content)
                        if os.path.isdir(lua_folder):
                            dest_lua = os.path.join(lua_folder, fname)
                            with open(dest_lua, "w", encoding="utf-8") as f:
                                f.write(new_content)
                except Exception as ex:
                    logger.error(f"Error checking lua {fname}: {ex}")
        except Exception as e:
            logger.error(f"Error repairing stplug-in luas: {e}")

        return fixed_count

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

        # 3. Clean appmanifest ACF file from libraries and libraryfolders.vdf
        cls.clean_acf_manifests(steam_path, appid)
        cls.remove_from_library_folders(steam_path, appid)

    @classmethod
    def clean_acf_manifests(cls, steam_path: str, appid: str) -> None:
        """Removes appmanifest ACF files for a specific AppID from all Steam libraries."""
        libs = cls.get_library_folders(steam_path)
        acf_name = f"appmanifest_{appid}.acf"
        for _, lib_path in libs:
            for fname in [acf_name, f"{acf_name}.bak"]:
                acf_path = os.path.join(lib_path, "steamapps", fname)
                if os.path.exists(acf_path):
                    try:
                        os.remove(acf_path)
                        logger.info(f"Deleted manifest ACF: {acf_path}")
                    except Exception as e:
                        logger.warning(f"Could not delete ACF file {acf_path}: {e}")

    @classmethod
    def get_active_steam_id64(cls, steam_path: str) -> str:
        """Finds the current logged in user's 64-bit Steam ID from loginusers.vdf."""
        vdf_path = os.path.join(steam_path, "config", "loginusers.vdf")
        if os.path.isfile(vdf_path):
            try:
                with open(vdf_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                matches = re.findall(r'"(\d{17})"\s*\{([^}]+)\}', content)
                for steamid, block in matches:
                    if re.search(r'"AutoLogin"\s+"1"', block):
                        return steamid
                if matches:
                    def get_timestamp(pair):
                        m = re.search(r'"timestamp"\s+"(\d+)"', pair[1])
                        return int(m.group(1)) if m else 0
                    sorted_matches = sorted(matches, key=get_timestamp, reverse=True)
                    return sorted_matches[0][0]
            except Exception as e:
                logger.debug(f"Error reading loginusers.vdf: {e}")
        return "76561199568801812"

    @classmethod
    def generate_acf_manifest(
        cls, 
        library_path: str, 
        appid: str, 
        game_name: str, 
        manifests: List[Dict[str, Any]] = None,
        actual_size: int = 0
    ) -> str:
        """Auto-generates appmanifest_<AppID>.acf file under steamapps folder.
        
        Uses StateFlags: 4 (Installed) and real SizeOnDisk so Steam knows the game is ready to play.
        """
        dest_dir = os.path.join(library_path, "steamapps")
        os.makedirs(dest_dir, exist_ok=True)
        acf_path = os.path.join(dest_dir, f"appmanifest_{appid}.acf")
        
        # Sanitize installdir from game name (letters, digits, spaces only)
        installdir = re.sub(r'[^a-zA-Z0-9\s\-\_]', '', game_name).strip()
        if not installdir:
            installdir = f"SteamApp_{appid}"
            
        active_owner = cls.get_active_steam_id64(library_path)
        main_steam_path = library_path
        try:
            from config import config
            if config.steam_path and os.path.isdir(config.steam_path):
                main_steam_path = config.steam_path
                if not os.path.isfile(os.path.join(library_path, "config", "loginusers.vdf")):
                    active_owner = cls.get_active_steam_id64(config.steam_path)
        except Exception:
            pass

        steam_exe = os.path.join(main_steam_path, "steam.exe").replace("/", "\\")
        
        # Collect all depots for this AppID
        depot_map = {}  # depot_id -> {"manifest": manifest_id, "size": size_str}

        # 1. From manifests list
        if manifests:
            for item in manifests:
                fname = item.get("name", "") if isinstance(item, dict) else str(item)
                m = re.match(r'^(\d+)_(\d+)\.manifest$', fname, re.IGNORECASE)
                if m:
                    depot_map[m.group(1)] = {"manifest": m.group(2), "size": "0"}

        # 2. From LUA files in config/stplug-in and config/lua
        lua_folders = [
            os.path.join(main_steam_path, "config", "stplug-in"),
            os.path.join(main_steam_path, "config", "lua")
        ]
        for l_folder in lua_folders:
            lp = os.path.join(l_folder, f"{appid}.lua")
            if os.path.isfile(lp):
                try:
                    with open(lp, "r", encoding="utf-8", errors="ignore") as fp:
                        txt = fp.read()
                    for m in re.finditer(r'setManifestid\s*\(\s*(\d+)\s*,\s*["\'](\d+)["\'](?:\s*,\s*(\d+))?', txt):
                        d_id, m_id, d_sz = m.group(1), m.group(2), m.group(3) or "0"
                        depot_map[d_id] = {"manifest": m_id, "size": str(d_sz)}
                    for m in re.finditer(r'addappid\s*\(\s*(\d+)', txt):
                        d_id = m.group(1)
                        if d_id != appid and d_id not in depot_map:
                            depot_map[d_id] = {"manifest": "0", "size": "0"}
                except Exception:
                    pass

        # 3. Check depotcache for manifests matching any depot that has manifest '0'
        depotcache_dirs = [
            os.path.join(main_steam_path, "depotcache"),
            os.path.join(main_steam_path, "config", "depotcache"),
            os.path.join(library_path, "depotcache")
        ]
        for d_dir in depotcache_dirs:
            if os.path.isdir(d_dir):
                try:
                    for f in os.listdir(d_dir):
                        m = re.match(r'^(\d+)_(\d+)\.manifest$', f, re.IGNORECASE)
                        if m:
                            d_id, m_id = m.group(1), m.group(2)
                            if d_id in depot_map and depot_map[d_id]["manifest"] == "0":
                                depot_map[d_id]["manifest"] = m_id
                except Exception:
                    pass

        # Format InstalledDepots entries
        depot_lines = []
        total_size = 0
        for d_id, d_info in depot_map.items():
            m_id = d_info["manifest"]
            sz = d_info["size"]
            try:
                total_size += int(sz)
            except Exception:
                pass
            depot_lines.append(f'\t\t"{d_id}"')
            depot_lines.append("\t\t{")
            depot_lines.append(f'\t\t\t"manifest"\t\t"{m_id}"')
            depot_lines.append(f'\t\t\t"size"\t\t"{sz}"')
            depot_lines.append("\t\t}")

        depots_str = "\n".join(depot_lines)
        common_game_dir = os.path.join(library_path, "steamapps", "common", installdir)
        disk_size = actual_size
        if disk_size <= 0 and os.path.isdir(common_game_dir):
            try:
                disk_size = sum(os.path.getsize(os.path.join(r, f)) for r, d, fs in os.walk(common_game_dir) for f in fs)
            except Exception:
                pass

        if disk_size > 5 * 1024 * 1024:
            state_flags = "4"
            size_on_disk = str(disk_size)
            bytes_to_download = "0"
            bytes_downloaded = "0"
        else:
            # Game is uninstalled, ready to be downloaded natively via Steam!
            # StateFlags 1026 = StateUpdateRequired (2) + StateUpdateQueued (1024)
            state_flags = "1026"
            size_on_disk = "0"
            bytes_to_download = str(total_size if total_size > 1000000 else 10737418240)
            bytes_downloaded = "0"

        last_updated = str(int(time.time()))
        final_depots_str = depots_str

        acf_content = f'''"AppState"
{{
	"appid"		"{appid}"
	"Universe"		"1"
	"LauncherPath"		"{steam_exe}"
	"name"		"{game_name}"
	"StateFlags"		"{state_flags}"
	"installdir"		"{installdir}"
	"LastUpdated"		"{last_updated}"
	"UpdateResult"		"0"
	"SizeOnDisk"		"{size_on_disk}"
	"buildid"		"0"
	"LastOwner"		"{active_owner}"
	"BytesToDownload"		"{bytes_to_download}"
	"BytesDownloaded"		"{bytes_downloaded}"
	"BytesToStage"		"0"
	"BytesStaged"		"0"
	"TargetBuildID"		"0"
	"AutoUpdateBehavior"		"0"
	"AllowOtherDownloadsWhileRunning"		"0"
	"UserConfig"
	{{
		"language"		"turkish"
	}}
	"InstalledDepots"
	{{
{final_depots_str}
	}}
}}
'''
        # If ACF already exists, backup
        if os.path.exists(acf_path):
            cls.backup_file(acf_path)
            
        with open(acf_path, "w", encoding="utf-8") as f:
            f.write(acf_content)
            
        logger.info(f"Generated ACF manifest (StateFlags={state_flags}) for AppID {appid} at: {acf_path}")
        return acf_path
