# %% [markdown]
# # Manifest Finder Module
# Downloads, extracts, and filters manifest and LUA files from repositories or local folders.

# %%
import os
import zipfile
import io
import requests
from typing import List, Dict, Any, Optional, Callable
from logger import logger

# %%
class ManifestFinder:
    """Discovers and downloads manifest/LUA configurations from community databases."""

    @staticmethod
    def filter_lua_content(content_str: str, repo_url: str) -> str:
        """Applies cleaning rules to LUA scripts while strictly preserving addappid and setManifestid."""
        import re
        lines = content_str.lstrip("\ufeff").splitlines()
        filtered_lines = []
        
        for line in lines:
            stripped = line.strip()
            # Always keep addappid and setManifestid (critical for SteamTools to hook manifests and prevent Access Denied)
            if stripped.startswith("addappid(") or stripped.startswith("setManifestid(") or stripped.startswith("setmanifestid("):
                if stripped.startswith("addappid("):
                    stripped = re.sub(r'^addappid\s*\(\s*(\d+)\s*\)', r'addappid(\1, 1)', stripped)
                    stripped = re.sub(r'^addappid\s*\(\s*(\d+)\s*,\s*0\s*,', r'addappid(\1, 1,', stripped)
                filtered_lines.append(stripped)
            elif stripped.startswith("setAppTicket(") or stripped.startswith("setETicket(") or stripped.startswith("addtoken("):
                filtered_lines.append(stripped)
            elif stripped.startswith("--"):
                filtered_lines.append(stripped)
            elif not stripped:
                filtered_lines.append("")
            else:
                # Keep other valid lua statements if not empty
                filtered_lines.append(stripped)
            
        # Append signature
        filtered_lines.append("")
        filtered_lines.append("-- Made with love by SteaMRogue")
        return "\n".join(filtered_lines)

    @classmethod
    def download_repo_zip(cls, repo_url: str, appid: str, progress_callback: Optional[Callable[[int, int], None]] = None) -> Optional[bytes]:
        """Downloads the zip archive for a specific AppID branch from a given repository."""
        zip_url = f"{repo_url}/archive/refs/heads/{appid}.zip"
        headers = {
            "User-Agent": "Project-Lightning",
            "Accept": "application/zip,application/octet-stream,*/*"
        }
        
        try:
            try:
                response = requests.get(zip_url, headers=headers, stream=True, timeout=15)
            except requests.exceptions.SSLError:
                logger.debug("SSL verification failed; retrying download without verification.")
                response = requests.get(zip_url, headers=headers, stream=True, timeout=15, verify=False)
            
            if response.status_code != 200:
                logger.debug(f"Repo branch not found (HTTP {response.status_code}) for: {zip_url}")
                return None
                
            total_size = int(response.headers.get('content-length', 0))
            buffer = io.BytesIO()
            downloaded = 0
            
            for chunk in response.iter_content(chunk_size=4096):
                if not chunk:
                    break
                buffer.write(chunk)
                downloaded += len(chunk)
                if progress_callback and total_size > 0:
                    progress_callback(downloaded, total_size)
                    
            logger.info(f"Downloaded manifest zip from: {repo_url} ({downloaded} bytes)")
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Error downloading from {repo_url}: {e}")
            return None

    @classmethod
    def extract_and_process_zip(cls, zip_bytes: bytes, repo_url: str) -> Dict[str, List[Dict[str, Any]]]:
        """Extracts files from zip, filters contents, and organizes them by file type."""
        result = {
            "manifests": [],
            "luas": []
        }
        
        try:
            with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
                for file_info in z.infolist():
                    if file_info.is_dir():
                        continue
                        
                    filename = os.path.basename(file_info.filename)
                    if not filename:
                        continue
                        
                    lower_name = filename.lower()
                    
                    if lower_name.endswith(".manifest"):
                        manifest_content = z.read(file_info.filename)
                        result["manifests"].append({
                            "name": filename,
                            "content": manifest_content
                        })
                        logger.debug(f"Found manifest in ZIP: {filename}")
                        
                    elif lower_name.endswith(".lua"):
                        lua_raw = z.read(file_info.filename)
                        try:
                            lua_str = lua_raw.decode("utf-8-sig")
                        except UnicodeDecodeError:
                            lua_str = lua_raw.decode("latin-1", errors="ignore")
                            
                        lua_str = lua_str.lstrip("\ufeff")
                        filtered_lua = cls.filter_lua_content(lua_str, repo_url).lstrip("\ufeff")
                        result["luas"].append({
                            "name": filename,
                            "content": filtered_lua.encode("utf-8")
                        })
                        logger.debug(f"Processed LUA in ZIP: {filename}")
                        
            # Ensure every manifest extracted has a corresponding setManifestid in the LUA script
            if result["manifests"] and result["luas"]:
                import re
                manifest_map = {}
                for m_item in result["manifests"]:
                    m = re.match(r"^(\d+)_(\d+)\.manifest$", m_item["name"], re.IGNORECASE)
                    if m:
                        manifest_map[m.group(1)] = m.group(2)
                
                for lua_item in result["luas"]:
                    lua_str = lua_item["content"].decode("utf-8", errors="ignore")
                    lines = lua_str.splitlines()
                    added_any = False
                    for depot_id, gid in manifest_map.items():
                        pat = rf"setManifestid\s*\(\s*['\"]?{depot_id}['\"]?\s*,"
                        if not re.search(pat, lua_str, re.IGNORECASE):
                            lines.append(f'setManifestid({depot_id}, "{gid}")')
                            added_any = True
                            logger.info(f"Auto-pinned manifest in LUA for depot {depot_id}: {gid}")
                    if added_any:
                        lua_item["content"] = "\n".join(lines).encode("utf-8")
                        
        except Exception as e:
            logger.error(f"Failed to extract or process zip archive: {e}")
            
        return result

    @classmethod
    def find_online(cls, appid: str, repos: List[str], progress_callback: Optional[Callable[[int, int, str], None]] = None) -> Optional[Dict[str, Any]]:
        """Searches through repositories in parallel for the game manifest, then downloads and processes it."""
        import concurrent.futures

        if progress_callback:
            progress_callback(10, 100, f"Topluluk depoları taranıyor ({len(repos)} kaynak)...")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) SteaMRogue/1.2.1",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }

        def check_branch_exists(repo_url: str) -> Optional[str]:
            tree_url = f"{repo_url}/tree/{appid}"
            try:
                r = requests.get(tree_url, headers=headers, timeout=8, allow_redirects=False)
                if r.status_code in (200, 301, 302):
                    return repo_url
            except Exception as ex:
                logger.debug(f"Branch check error for {repo_url}: {ex}")
            return None

        # 1. Fast parallel check preserving priority order
        found_repo = None
        checked_repos = set()
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(4, len(repos))) as executor:
                futures = [executor.submit(check_branch_exists, repo) for repo in repos]
                for future, repo in zip(futures, repos):
                    try:
                        res = future.result()
                        checked_repos.add(repo)
                        if res and not found_repo:
                            found_repo = res
                    except Exception:
                        pass
        except Exception as e:
            logger.debug(f"Parallel branch check exception: {e}")

        # 2. If found via fast check, download and extract
        if found_repo:
            repo_name = found_repo.split("/")[-1]
            if progress_callback:
                progress_callback(40, 100, f"Manifest bulundu ({repo_name}), indiriliyor...")

            p_cb = None
            if progress_callback:
                p_cb = lambda cur, tot: progress_callback(cur, tot, f"[{repo_name}] Manifest indiriliyor...")

            zip_data = cls.download_repo_zip(found_repo, appid, progress_callback=p_cb)
            if zip_data:
                processed = cls.extract_and_process_zip(zip_data, found_repo)
                if processed["manifests"] or processed["luas"]:
                    return {
                        "source": "online",
                        "repo": found_repo,
                        "manifests": processed["manifests"],
                        "luas": processed["luas"]
                    }

        # 3. Fallback sequential check: ONLY for any repo that could not be verified in step 1
        unchecked_repos = [r for r in repos if r not in checked_repos]
        for index, repo in enumerate(unchecked_repos):
            repo_name = repo.split("/")[-1]
            p_cb = None
            if progress_callback:
                p_cb = lambda cur, tot: progress_callback(cur, tot, f"[{index+1}/{len(unchecked_repos)}] Kontrol ediliyor: {repo_name}...")
            zip_data = cls.download_repo_zip(repo, appid, progress_callback=p_cb)
            if zip_data:
                processed = cls.extract_and_process_zip(zip_data, repo)
                if processed["manifests"] or processed["luas"]:
                    return {
                        "source": "online",
                        "repo": repo,
                        "manifests": processed["manifests"],
                        "luas": processed["luas"]
                    }

        return None

    @staticmethod
    def scan_local_depotcache(steam_path: str, appid: str) -> List[Dict[str, Any]]:
        """Scans local Steam directories for any manifests matching the given AppID."""
        manifests = []
        # Possible local depotcache folders
        paths_to_scan = [
            os.path.join(steam_path, "depotcache"),
            os.path.join(steam_path, "config", "depotcache")
        ]
        
        for base_path in paths_to_scan:
            if not os.path.isdir(base_path):
                continue
                
            try:
                for file in os.listdir(base_path):
                    # Local manifests are named: <DepotID>_<ManifestID>.manifest
                    # Usually, the first part is the DepotID, and sometimes a depot is identical to AppID
                    # We can look for manifest files starting with appid_
                    if file.lower().endswith(".manifest") and file.startswith(f"{appid}_"):
                        full_path = os.path.join(base_path, file)
                        try:
                            with open(full_path, "rb") as f:
                                manifests.append({
                                    "name": file,
                                    "content": f.read(),
                                    "local_path": full_path
                                })
                                logger.info(f"Discovered local manifest: {file} at {base_path}")
                        except Exception as e:
                            logger.error(f"Failed to read local manifest file {file}: {e}")
            except Exception as e:
                logger.debug(f"Failed scanning folder {base_path}: {e}")
                
        return manifests
