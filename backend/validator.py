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
    if hash_client:
        targets.append(("pattern", "steamclient", hash_client))
        targets.append(("ipc", "steamclient", hash_client))
    if hash_ui:
        targets.append(("pattern", "steamui", hash_ui))

    for channel, comp, sha in targets:
        comp_dir = os.path.join(ost_dir, channel, comp)
        os.makedirs(comp_dir, exist_ok=True)
        target_file = os.path.join(comp_dir, f"{sha}.toml")

        # If file already exists and is non-empty, keep it
        if os.path.isfile(target_file) and os.path.getsize(target_file) > 100:
            continue

        downloaded = False
        try:
            import urllib.request
            url = f"https://raw.githubusercontent.com/OpenSteam001/steam-monitor/{channel}/{comp}/{sha}.toml"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                content = resp.read()
                if resp.status == 200 and len(content) > 100:
                    with open(target_file, "wb") as f_out:
                        f_out.write(content)
                    logger.info(f"[OST Signatures] Downloaded upstream {channel}/{comp}/{sha}.toml")
                    downloaded = True
                    synced_any = True
        except Exception:
            pass

        # Dynamic local AOB signature scanner fallback
        if not downloaded:
            try:
                # Find an existing template toml in the same directory
                existing_tomls = [os.path.join(comp_dir, f) for f in os.listdir(comp_dir) if f.endswith(".toml") and os.path.isfile(os.path.join(comp_dir, f))]
                if existing_tomls:
                    latest_toml = max(existing_tomls, key=os.path.getmtime)
                    if channel == "ipc":
                        import shutil
                        shutil.copy2(latest_toml, target_file)
                        logger.info(f"[OST Signatures] Generated dynamic IPC signature: {sha}.toml from template {os.path.basename(latest_toml)}")
                        synced_any = True
                    elif channel == "pattern":
                        # Scan binary for AOB signatures
                        dll_name = "SteamUI.dll" if comp == "steamui" else "steamclient64.dll"
                        target_dll = os.path.join(steam_path, dll_name)
                        if os.path.isfile(target_dll):
                            import re, struct
                            with open(target_dll, "rb") as df:
                                dll_bytes = df.read()

                            def pe_offset_to_rva(pe_data, offset):
                                e_lfanew = struct.unpack('<I', pe_data[0x3C:0x40])[0]
                                num_sections = struct.unpack('<H', pe_data[e_lfanew+6:e_lfanew+8])[0]
                                opt_header_size = struct.unpack('<H', pe_data[e_lfanew+20:e_lfanew+22])[0]
                                section_table_offset = e_lfanew + 24 + opt_header_size
                                for i in range(num_sections):
                                    sec_offset = section_table_offset + i * 40
                                    virtual_size, virtual_addr, raw_size, raw_ptr = struct.unpack('<IIII', pe_data[sec_offset+8:sec_offset+24])
                                    if raw_ptr <= offset < raw_ptr + raw_size:
                                        return offset - raw_ptr + virtual_addr
                                return offset

                            with open(latest_toml, "r", encoding="utf-8") as tf:
                                tlines = tf.readlines()

                            c_sec = None
                            t_sigs = {}
                            for tl in tlines:
                                tl = tl.strip()
                                if tl.startswith("[") and tl.endswith("]"):
                                    c_sec = tl
                                    t_sigs[c_sec] = {}
                                elif "=" in tl and c_sec:
                                    k, v = tl.split("=", 1)
                                    t_sigs[c_sec][k.strip()] = v.strip().strip('"')

                            out_lines = []
                            for sec_k, sdata in t_sigs.items():
                                sig_str = sdata.get("sig")
                                if not sig_str:
                                    continue
                                pat_bytes = []
                                for part in sig_str.split():
                                    if part in ("??", "?"):
                                        pat_bytes.append(b".")
                                    else:
                                        pat_bytes.append(re.escape(bytes.fromhex(part)))
                                rx = b"".join(pat_bytes)
                                m_list = list(re.finditer(rx, dll_bytes, re.DOTALL))
                                if len(m_list) == 1:
                                    raw_start = m_list[0].start()
                                    matched_rva = pe_offset_to_rva(dll_bytes, raw_start)
                                    out_lines.append(sec_k)
                                    out_lines.append(f'name = "{sdata["name"]}"')
                                    out_lines.append(f'rva = "0x{matched_rva:X}"')
                                    out_lines.append(f'sig = "{sig_str}"\n')

                            if out_lines:
                                with open(target_file, "w", encoding="utf-8") as out_f:
                                    out_f.write("\n".join(out_lines))
                                logger.info(f"[OST Signatures] Auto-generated dynamic AOB pattern signature: {sha}.toml ({len(out_lines)//4} functions mapped)")
                                synced_any = True
            except Exception as d_err:
                logger.debug(f"[OST Signatures] Dynamic generation error: {d_err}")

    all_present = all(
        os.path.isfile(os.path.join(ost_dir, channel, comp, f"{sha}.toml")) and 
        os.path.getsize(os.path.join(ost_dir, channel, comp, f"{sha}.toml")) > 100
        for channel, comp, sha in targets
    )
    return all_present or synced_any

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
        import winreg, ctypes
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam\ActiveProcess", 0, winreg.KEY_READ | winreg.KEY_SET_VALUE) as key:
            cur_pid, _ = winreg.QueryValueEx(key, "pid")
            if cur_pid != 0:
                # Check if process is still alive
                is_alive = False
                h_proc = ctypes.windll.kernel32.OpenProcess(0x1000, False, cur_pid)
                if h_proc:
                    ctypes.windll.kernel32.CloseHandle(h_proc)
                    is_alive = True
                if not is_alive or not is_steam_running():
                    winreg.SetValueEx(key, "pid", 0, winreg.REG_DWORD, 0)
                    logger.info(f"[cleanup_steam_crashes] Reset stale ActiveProcess pid ({cur_pid}) to 0.")
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

# %%
def check_vcredist_installed() -> dict:
    """Checks whether Microsoft Visual C++ 2015-2022 Redistributable (x86 and x64) are installed."""
    results = {
        "x86": False,
        "x64": False,
        "all_installed": False,
        "details": ""
    }
    
    if sys.platform != "win32":
        results["all_installed"] = True
        return results

    sys_root = os.environ.get("SystemRoot", r"C:\Windows")
    
    # 1. File existence check
    x86_dll = os.path.join(sys_root, "SysWOW64", "vcruntime140.dll")
    x64_dll = os.path.join(sys_root, "System32", "vcruntime140.dll")
    
    if os.path.isfile(x86_dll):
        results["x86"] = True
    if os.path.isfile(x64_dll):
        results["x64"] = True

    # 2. Registry check (authoritative for Visual Studio 2015-2022 v14.x)
    try:
        import winreg
        for reg_path in [
            r"SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\X86",
            r"SOFTWARE\WOW6432Node\Microsoft\VisualStudio\14.0\VC\Runtimes\X86"
        ]:
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path, 0, winreg.KEY_READ) as k:
                    val, _ = winreg.QueryValueEx(k, "Installed")
                    if val == 1:
                        results["x86"] = True
                        break
            except Exception:
                pass

        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\X64", 0, winreg.KEY_READ) as k:
                val, _ = winreg.QueryValueEx(k, "Installed")
                if val == 1:
                    results["x64"] = True
        except Exception:
            pass
    except Exception as e:
        logger.debug(f"[check_vcredist_installed] Registry check error: {e}")

    results["all_installed"] = results["x86"] and results["x64"]
    if results["all_installed"]:
        results["details"] = "Microsoft Visual C++ 2015-2022 (x86 ve x64) sistemde kurulu ve hazır."
    elif not results["x86"] and not results["x64"]:
        results["details"] = "Microsoft Visual C++ 2015-2022 (x86 ve x64) paketleri eksik!"
    elif not results["x86"]:
        results["details"] = "Microsoft Visual C++ 2015-2022 (x86) 32-bit çalışma zamanı paketi eksik (SteamTools için zorunlu)."
    else:
        results["details"] = "Microsoft Visual C++ 2015-2022 (x64) 64-bit çalışma zamanı paketi eksik (Oyunlar için zorunlu)."

    return results

# %%
def install_vcredist_silently(arch: str = "all") -> tuple:
    """
    Downloads and silently installs Microsoft Visual C++ 2015-2022 Redistributables.
    arch can be: 'x86', 'x64', or 'all'.
    Returns (success: bool, message: str).
    """
    if sys.platform != "win32":
        return False, "Sadece Windows sistemlerde desteklenir."

    current_status = check_vcredist_installed()
    to_install = []
    
    if arch in ("x86", "all") and not current_status["x86"]:
        to_install.append(("x86", "https://aka.ms/vs/17/release/vc_redist.x86.exe"))
    if arch in ("x64", "all") and not current_status["x64"]:
        to_install.append(("x64", "https://aka.ms/vs/17/release/vc_redist.x64.exe"))

    if not to_install:
        return True, "Gerekli Visual C++ çalışma zamanı paketleri zaten sistemde kurulu."

    import tempfile
    import urllib.request
    
    installed_any = False
    temp_dir = tempfile.gettempdir()

    for item_arch, download_url in to_install:
        temp_file = os.path.join(temp_dir, f"vc_redist_{item_arch}.exe")
        logger.info(f"[VC++ Redist] İndiriliyor: {item_arch} -> {download_url}")
        
        try:
            req = urllib.request.Request(
                download_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )
            with urllib.request.urlopen(req, timeout=45.0) as resp:
                with open(temp_file, "wb") as f_out:
                    while chunk := resp.read(65536):
                        f_out.write(chunk)
                        
            if not os.path.isfile(temp_file) or os.path.getsize(temp_file) < 1000000:
                return False, f"Visual C++ ({item_arch}) indirme dosyası bozuk veya tamamlanamadı."

            logger.info(f"[VC++ Redist] Sessiz kurulum başlatılıyor: {temp_file}")
            cmd = [temp_file, "/install", "/quiet", "/norestart"]
            flags = 0x08000000 # CREATE_NO_WINDOW
            
            proc = subprocess.run(
                cmd,
                creationflags=flags,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=180
            )
            
            if proc.returncode in (0, 1638, 3010):
                logger.info(f"[VC++ Redist] {item_arch} başarıyla kuruldu (çıkış kodu: {proc.returncode}).")
                installed_any = True
            else:
                logger.warning(f"[VC++ Redist] {item_arch} kurulum kodu: {proc.returncode}")
                new_check = check_vcredist_installed()
                if new_check.get(item_arch):
                    installed_any = True

        except subprocess.TimeoutExpired:
            logger.error(f"[VC++ Redist] {item_arch} kurulum zaman aşımına uğradı.")
        except Exception as e:
            logger.error(f"[VC++ Redist] {item_arch} kurulum hatası: {e}")
        finally:
            try:
                if os.path.isfile(temp_file):
                    os.remove(temp_file)
            except Exception:
                pass

    final_check = check_vcredist_installed()
    if final_check["all_installed"] or installed_any:
        return True, "Visual C++ çalışma zamanı paketleri başarıyla sisteme kuruldu."
    else:
        return False, "Visual C++ paketleri kurulurken bir hata oluştu veya yönetici izni gerekebilir."

# %%
def get_system_antivirus_info() -> dict:
    """Detects active antivirus software installed on the system via Windows Security Center (WMI)."""
    info = {
        "products": [],
        "has_third_party": False,
        "primary_av": "Windows Defender",
        "names": [],
        "defender_active": True
    }
    if sys.platform != "win32":
        return info

    try:
        import json
        cmd = "Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntivirusProduct | Select-Object displayName, productState | ConvertTo-Json"
        res = subprocess.check_output(
            ["powershell", "-NoProfile", "-Command", cmd],
            creationflags=0x08000000,
            encoding="utf-8",
            errors="ignore"
        )
        if res.strip():
            data = json.loads(res.strip())
            if isinstance(data, dict):
                data = [data]
            for item in data:
                name = item.get("displayName", "Bilinmeyen Antivirüs")
                state = item.get("productState", 0)
                is_enabled = bool(state & 0x1000) or bool(state & 0x040000)
                info["products"].append({"name": name, "state": state, "enabled": is_enabled})
                info["names"].append(name)
                if "defender" not in name.lower():
                    info["has_third_party"] = True
                    if is_enabled:
                        info["primary_av"] = name

            if info["has_third_party"] and info["primary_av"] != "Windows Defender":
                info["defender_active"] = False
    except Exception as e:
        logger.debug(f"[get_system_antivirus_info] Query failed: {e}")

    return info

# %%
def check_security_quarantine(steam_path: str) -> dict:
    """Checks whether key SteamTools DLLs have been deleted or quarantined by an antivirus."""
    res = {
        "is_quarantined": False,
        "missing_files": [],
        "av_info": get_system_antivirus_info(),
        "details": ""
    }
    if not steam_path or not os.path.isdir(steam_path):
        return res

    # If official SteamTools xinput1_4.dll (> 200KB) is present (active or safe mode), it is completely self-contained
    official_st = os.path.join(steam_path, "xinput1_4.dll")
    official_st_disabled = os.path.join(steam_path, "xinput1_4.dll.disabled")
    if (os.path.isfile(official_st) and os.path.getsize(official_st) > 200000) or \
       (os.path.isfile(official_st_disabled) and os.path.getsize(official_st_disabled) > 200000):
        res["details"] = "Resmi SteamTools kilit açıcı modülü mevcut ve korumalı durumda."
        return res

    required = ["xinput1_4.dll", "OpenSteamTool.dll"]
    for f in required:
        fp = os.path.join(steam_path, f)
        min_sz = 50000 if f == "xinput1_4.dll" else 500000
        if not os.path.isfile(fp) or os.path.getsize(fp) < min_sz:
            res["missing_files"].append(f)

    if res["missing_files"]:
        res["is_quarantined"] = True
        av_name = res["av_info"].get("primary_av", "Antivirüs")
        res["details"] = f"{', '.join(res['missing_files'])} Steam klasöründe eksik veya {av_name} tarafından karantinaya alınmış olabilir."
    else:
        res["details"] = "Steam kilit açıcı dosyaları eksiksiz ve yerinde duruyor."

    return res

# %%
def auto_restore_quarantined_files(steam_path: str, bundled_dir: str = None) -> tuple:
    """
    Restores missing or quarantined SteamTools DLLs from bundled storage or upstream.
    Applies MessageBoxA silencing patch to OpenSteamTool.dll.
    Returns (success: bool, message: str).
    """
    if not steam_path or not os.path.isdir(steam_path):
        return False, "Geçerli bir Steam dizini bulunamadı."

    import shutil

    # 1. Resolve bundled steamtools_files folder
    if not bundled_dir:
        curr = os.path.dirname(os.path.abspath(__file__))
        cand1 = os.path.join(curr, "steamtools_files")
        cand1_parent = os.path.join(os.path.dirname(curr), "steamtools_files")
        cand2 = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "steamtools-auto", "steamtools_files")
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            cand0 = os.path.join(sys._MEIPASS, "steamtools_files")
            if os.path.isdir(cand0):
                bundled_dir = cand0
        if not bundled_dir and os.path.isdir(cand1):
            bundled_dir = cand1
        elif not bundled_dir and os.path.isdir(cand1_parent):
            bundled_dir = cand1_parent
        elif not bundled_dir and os.path.isdir(cand2):
            bundled_dir = cand2

    restored = []
    targets = ["xinput1_4.dll", "OpenSteamTool.dll"]

    # Terminate Steam first if running to release DLL locks
    was_running = is_steam_running()
    if was_running:
        kill_steam(steam_path)
        wait_for_steam_exit(timeout=6.0)

    # Check if Safe Mode is intentionally activated
    official_st_disabled = os.path.join(steam_path, "xinput1_4.dll.disabled")
    if os.path.isfile(official_st_disabled) and os.path.getsize(official_st_disabled) > 50000:
        logger.info("[auto_restore] Safe Mode (VAC Safe) is active. Skipping hook restoration.")
        return True, "Güvenli mod devrede, kanca dosyaları korundu."

    for f in targets:
        dst = os.path.join(steam_path, f)
        src = os.path.join(bundled_dir, f) if bundled_dir else ""
        min_sz = 50000 if f == "xinput1_4.dll" else 500000
        needs_restore = not os.path.isfile(dst) or os.path.getsize(dst) < min_sz

        if needs_restore:
            if src and os.path.isfile(src):
                try:
                    shutil.copy2(src, dst)
                    restored.append(f)
                    logger.info(f"[auto_restore] Restored {f} from bundled files.")
                except Exception as ce:
                    logger.warning(f"[auto_restore] Could not copy {f}: {ce}")
            else:
                try:
                    import urllib.request
                    url = f"https://raw.githubusercontent.com/mythoscd/SteaMRogue/main/steamtools_files/{f}"
                    req = urllib.request.Request(url, headers={"User-Agent": "SteaMRogue"})
                    with urllib.request.urlopen(req, timeout=15.0) as resp:
                        content = resp.read()
                        if len(content) > 1000:
                            with open(dst, "wb") as out_f:
                                out_f.write(content)
                            restored.append(f)
                            logger.info(f"[auto_restore] Downloaded {f} from upstream.")
                except Exception as de:
                    logger.warning(f"[auto_restore] Download fallback failed for {f}: {de}")

    # Patch OpenSteamTool.dll MessageBoxA to prevent freeze
    ost_dll = os.path.join(steam_path, "OpenSteamTool.dll")
    if os.path.isfile(ost_dll):
        try:
            with open(ost_dll, "r+b") as f_ost:
                f_ost.seek(0x7423b)
                b_check = f_ost.read(6)
                if b_check == bytes.fromhex("ff15d7d60700"):
                    f_ost.seek(0x7423b)
                    f_ost.write(bytes.fromhex("909090909090"))
                    logger.info("[auto_restore] OpenSteamTool.dll MessageBoxA silenced.")
        except Exception:
            pass

    # Ensure signatures
    try:
        ensure_opensteamtool_signatures(steam_path)
    except Exception:
        pass

    q_check = check_security_quarantine(steam_path)
    if not q_check["is_quarantined"]:
        msg = f"Karantinaya alınan/eksik dosyalar ({', '.join(restored) if restored else 'tümü'}) başarıyla geri yüklendi ve korumaya alındı."
        return True, msg
    else:
        return False, f"Bazı dosyalar ({', '.join(q_check['missing_files'])}) geri yüklenemedi. Antivirüsünüzün gerçek zamanlı korumasından dışlama ekleyin."



