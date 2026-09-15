# %% [markdown]
# # Web GUI Backend & Wrapper
# Starts a Flask server for API communications and serves static assets.
# Integrates with pywebview for a desktop application experience.

# %%
import os
import sys
import json
import time
import threading
import subprocess
import webbrowser
from typing import Dict, Any
import re
import requests

from flask import Flask, jsonify, request, send_from_directory, redirect
from logger import logger, setup_logger
from config import config
import validator
from steam_api import SteamAPI
from manifest_finder import ManifestFinder
from file_manager import FileManager, VdfParser
from exceptions import SteamToolsException
import updater

# %%
# Initialize Flask
if hasattr(sys, "_MEIPASS"):
    web_dir = os.path.join(sys._MEIPASS, "web")
else:
    web_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")

app = Flask(__name__, static_folder=web_dir)

def get_appdata_dir():
    appdata = os.environ.get("APPDATA")
    if appdata:
        pdir = os.path.join(appdata, "SteaMRogue")
    else:
        pdir = os.path.expanduser("~/.steamrogue")
    os.makedirs(pdir, exist_ok=True)
    return pdir

def get_covers_cache_dir():
    cdir = os.path.join(get_appdata_dir(), "cache", "covers")
    os.makedirs(cdir, exist_ok=True)
    return cdir

@app.after_request
def add_header(response):
    path = request.path
    # Aggressive browser caching for static assets, covers and images (instant 0ms reloads)
    if path.startswith("/api/cover/") or any(path.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.ico', '.css', '.js', '.woff2', '.ttf', '.svg']):
        response.headers["Cache-Control"] = "public, max-age=2592000, immutable"
        if "Pragma" in response.headers:
            del response.headers["Pragma"]
        if "Expires" in response.headers:
            del response.headers["Expires"]
    else:
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

APP_VERSION = "1.0.9"

# Global dictionary to track add/download task status
task_statuses: Dict[str, Dict[str, Any]] = {}
task_lock = threading.Lock()

# %%
# Health Check Endpoint
@app.route("/api/health")
def health_check():
    return jsonify({"status": "ok", "app": "SteaMRogue", "version": APP_VERSION})

# %%
# API Endpoint: GET /api/component_update_status
# Returns the current state of the startup updater (repo SHAs + SteamTools hash)
@app.route("/api/component_update_status", methods=["GET"])
def component_update_status():
    return jsonify(updater.get_status())

# %%
# API Endpoint: POST /api/run_startup_checks
# Manually triggers the startup updater (force=true re-downloads even if hash unchanged)
@app.route("/api/run_startup_checks", methods=["POST"])
def run_startup_checks():
    data = request.json or {}
    force = bool(data.get("force", False))
    updater.run_startup_checks(config.manifest_repos, config.steam_path, force=force)
    return jsonify({"success": True, "message": "Startup checks triggered in background"})

# %%
# API Endpoint: POST /api/check_steamtools_update
# Checks & updates ONLY SteamTools DLLs
@app.route("/api/check_steamtools_update", methods=["POST"])
def check_steamtools_update():
    data = request.json or {}
    force = bool(data.get("force", False))
    result = updater.check_and_update_steamtools(config.steam_path, force=force)
    return jsonify(result)


# Serving Static Assets
@app.route("/")
def index():
    return send_from_directory(web_dir, "index.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(web_dir, path)

# %%
# API Endpoint: GET /api/config & POST /api/config
@app.route("/api/config", methods=["GET", "POST"])
def manage_config():
    if request.method == "POST":
        data = request.json or {}
        steam_path = data.get("steam_path", "").strip()
        if steam_path:
            try:
                config.steam_path = validator.validate_steam_path(steam_path)
                config.save()
                return jsonify({"success": True})
            except SteamToolsException as e:
                return jsonify({"success": False, "error": str(e)})
        return jsonify({"success": False, "error": "Steam path cannot be empty"})
    
    return jsonify({
        "steam_path": config.steam_path,
        "manifest_repos": config.manifest_repos
    })

# %%
# API Endpoint: GET /api/logs
@app.route("/api/logs", methods=["GET"])
def get_logs():
    log_file = os.path.join("logs", "steamtools_auto.log")
    if not os.path.exists(log_file):
        return jsonify({"logs": "No log entries yet."})
        
    try:
        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            tail = lines[-100:]  # Get last 100 lines
            return jsonify({"logs": "".join(tail)})
    except Exception as e:
        return jsonify({"logs": f"Failed to retrieve log data: {e}"})

def find_local_cover(steam_path, appid, prefer_header=False):
    if not steam_path:
        return None
    aid_str = str(appid)
    lc_dir = os.path.join(steam_path, "appcache", "librarycache")
    if not os.path.isdir(lc_dir):
        return None

    if not prefer_header:
        flat_600 = os.path.join(lc_dir, f"{aid_str}_library_600x900.jpg")
        if os.path.isfile(flat_600) and os.path.getsize(flat_600) > 15000:
            return flat_600

    app_dir = os.path.join(lc_dir, aid_str)
    if os.path.isdir(app_dir):
        capsules = []
        headers = []
        heroes = []
        for root, _, files in os.walk(app_dir):
            for f in files:
                f_lower = f.lower()
                full_path = os.path.join(root, f)
                try:
                    size = os.path.getsize(full_path)
                except Exception:
                    continue
                # Skip small thumbnails/icons (< 12KB)
                if size < 12000:
                    continue
                if f_lower == "library_600x900.jpg":
                    if not prefer_header:
                        return full_path
                    capsules.append((size, full_path))
                elif f_lower == "library_capsule.jpg":
                    capsules.append((size, full_path))
                elif f_lower in ["library_header.jpg", "header.jpg"]:
                    headers.append((size, full_path))
                elif f_lower == "library_hero.jpg":
                    heroes.append((size, full_path))

        if prefer_header:
            if headers:
                headers.sort(key=lambda x: x[0], reverse=True)
                return headers[0][1]
            if heroes:
                heroes.sort(key=lambda x: x[0], reverse=True)
                return heroes[0][1]
            if capsules:
                capsules.sort(key=lambda x: x[0], reverse=True)
                return capsules[0][1]
        else:
            if capsules:
                capsules.sort(key=lambda x: x[0], reverse=True)
                return capsules[0][1]
            if headers:
                headers.sort(key=lambda x: x[0], reverse=True)
                return headers[0][1]
            if heroes:
                heroes.sort(key=lambda x: x[0], reverse=True)
                return heroes[0][1]

    flat_header = os.path.join(lc_dir, f"{aid_str}_header.jpg")
    if os.path.isfile(flat_header) and os.path.getsize(flat_header) > 12000:
        return flat_header

    return None

_local_cover_cache = {}

@app.route("/api/cover/<appid>", methods=["GET"])
def get_game_cover(appid):
    """Ultra-fast local cover server with multi-tier disk caching and browser caching."""
    prefer_header = request.args.get("type") == "header"
    cache_key = f"{appid}_header" if prefer_header else str(appid)

    # Tier 1: In-memory cache
    if cache_key in _local_cover_cache:
        cached_path = _local_cover_cache[cache_key]
        if cached_path and os.path.isfile(cached_path):
            resp = send_from_directory(os.path.dirname(cached_path), os.path.basename(cached_path))
            resp.headers["Cache-Control"] = "public, max-age=2592000, immutable"
            return resp

    # Tier 2: Check Steam's native appcache on disk (instant NVMe/SSD read)
    try:
        if config.steam_path:
            local_path = find_local_cover(config.steam_path, appid, prefer_header=prefer_header)
            if local_path and os.path.isfile(local_path):
                _local_cover_cache[cache_key] = local_path
                resp = send_from_directory(os.path.dirname(local_path), os.path.basename(local_path))
                resp.headers["Cache-Control"] = "public, max-age=2592000, immutable"
                return resp
    except Exception as e:
        logger.debug(f"Error finding local cover for appid {appid}: {e}")

    # Tier 3: Direct Steam CDN redirect as fallback (0ms, non-blocking)
    _local_cover_cache[cache_key] = None
    if prefer_header:
        cdn_url = f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/header.jpg"
    else:
        cdn_url = f"https://shared.cloudflare.steamstatic.com/store_item_assets/steam/apps/{appid}/library_600x900.jpg"
    return redirect(cdn_url)

# %%
# Discount Leak Helper Methods and API
GENRES_CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_genres_cache.json")
genres_cache = {}

DEFAULT_GENRES = {
    "2950790": ["Action", "Simulation"],
    "334940": ["Adventure", "Indie"],
    "268420": ["Adventure", "RPG"],
    "960910": ["Adventure", "RPG"],
    "1144200": ["Action"],
    "4450620": ["Indie", "Adventure"],
    "1623730": ["RPG", "Action"],
    "2651280": ["Action", "Adventure"],
    "Kathy Rain": ["Adventure", "Indie"],
    "Dungeon Siege": ["RPG", "Action"],
    "Fahrenheit: Indigo Prophecy Remastered": ["Adventure"],
    "Peggle Deluxe": ["Indie", "Casual"],
    "Dungeons of Dreadrock": ["Adventure", "Indie"],
    "Quantum Conundrum": ["Indie", "Adventure"],
    "140": ["Indie", "Action"],
    "Divide By Sheep": ["Indie", "Strategy"],
    "Under The Waves": ["Adventure", "Indie"],
    "Dustborn": ["Action", "Adventure"],
    "Where The Water Tastes Like Wine": ["Adventure", "Indie"],
    "Rogue Legacy": ["Action", "RPG", "Indie"],
    "LIMBO": ["Adventure", "Indie"],
    "Lacuna": ["Adventure", "Indie"],
    "Gerda: A Flame in Winter": ["RPG", "Indie"],
    "Just Cause 2": ["Action", "Adventure"],
    "King of Seas": ["Action", "RPG", "Indie"],
    "INSIDE": ["Adventure", "Indie"],
    "Lil Guardsman": ["Adventure", "Indie"],
    "Darkest Hour": ["Strategy"],
    "Dawn of Andromeda": ["Strategy", "Simulation"]
}

if os.path.exists(GENRES_CACHE_FILE):
    try:
        with open(GENRES_CACHE_FILE, "r", encoding="utf-8") as f:
            genres_cache = json.load(f)
    except Exception:
        pass

for k, v in DEFAULT_GENRES.items():
    if k not in genres_cache:
        genres_cache[k] = v

def guess_genres_by_title(title):
    title_lower = title.lower()
    guessed = []
    
    if "beyond" in title_lower or "rain" in title_lower or "fahrenheit" in title_lower or "detroit" in title_lower or "human" in title_lower or "limbo" in title_lower or "inside" in title_lower or "story" in title_lower or "interactive" in title_lower:
        return ["Adventure", "RPG"]
        
    if any(x in title_lower for x in ["simulat", "tycoon", "farm", "manager", "build", "world", "truck"]):
        guessed.append("Simulation")
    if any(x in title_lower for x in ["rpg", "role", "fantasy", "quest", "soul", "scrolls"]):
        guessed.append("RPG")
    if any(x in title_lower for x in ["action", "shoot", "fight", "combat", "war", "battle", "strike", "dead", "kill", "cod", "halo"]):
        guessed.append("Action")
    if any(x in title_lower for x in ["adventur", "journey", "explore", "lost", "tomb", "island", "croft"]):
        guessed.append("Adventure")
    if any(x in title_lower for x in ["strateg", "tact", "command", "conquer", "defense", "tower", "civiliz"]):
        guessed.append("Strategy")
    if any(x in title_lower for x in ["sport", "foot", "soccer", "rac", "drive", "car", "golf", "tennis", "f1", "fifa"]):
        guessed.append("Sports")
    if len(guessed) == 0:
        guessed.append("Indie")
    return guessed

_exchange_rate_cache = {"rate": 33.0, "timestamp": 0}
EXCHANGE_RATE_TTL = 43200  # 12 hours

def get_exchange_rate():
    now = time.time()
    if _exchange_rate_cache["timestamp"] > 0 and (now - _exchange_rate_cache["timestamp"]) < EXCHANGE_RATE_TTL:
        return _exchange_rate_cache["rate"]
        
    def _fetch_rate():
        try:
            r = requests.get("https://open.er-api.com/v6/latest/USD", timeout=3.0)
            if r.ok:
                data = r.json()
                rate = data.get("rates", {}).get("TRY")
                if rate:
                    _exchange_rate_cache["rate"] = float(rate)
                    _exchange_rate_cache["timestamp"] = time.time()
        except Exception:
            pass
            
    if _exchange_rate_cache["timestamp"] == 0 or (now - _exchange_rate_cache["timestamp"]) >= EXCHANGE_RATE_TTL:
        _exchange_rate_cache["timestamp"] = now  # cooldown
        threading.Thread(target=_fetch_rate, daemon=True).start()
        
    return _exchange_rate_cache["rate"]

def fetch_genres_in_background(appids):
    def worker():
        for appid in appids:
            if appid in genres_cache:
                continue
            try:
                details = SteamAPI.get_app_details(appid)
                if details and "genres" in details:
                    genre_names = [g["description"] for g in details["genres"]]
                    genres_cache[appid] = genre_names
                    with open(GENRES_CACHE_FILE, "w", encoding="utf-8") as f:
                        json.dump(genres_cache, f, indent=4)
                time.sleep(1.0)
            except Exception:
                pass
    threading.Thread(target=worker, daemon=True).start()



# Server-side deals cache — 10 minute TTL
_deals_cache = {"data": None, "timestamp": 0}
DEALS_CACHE_TTL = 600

@app.route("/api/deals", methods=["GET"])
def get_deals():
    """Fetches Steam deals directly from the Steam Store API for Turkey (cc=tr), resolving regional pricing."""
    from bs4 import BeautifulSoup
    import concurrent.futures
    import time as _time

    title_query = request.args.get("title", "").strip()
    exchange_rate = get_exchange_rate()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    # Helper function to scrape and parse a search results page
    def fetch_steam_search_page(params):
        try:
            r = requests.get(
                "https://store.steampowered.com/search/results/",
                params=params,
                headers=headers,
                timeout=10.0
            )
            if not r.ok:
                return []
            
            soup = BeautifulSoup(r.text, "html.parser")
            rows = soup.find_all("a", class_="search_result_row")
            parsed_deals = []
            
            for row in rows:
                appid_raw = row.get("data-ds-appid")
                if not appid_raw:
                    continue
                appid = appid_raw.split(",")[0].strip()
                
                title_el = row.find("span", class_="title")
                title = title_el.get_text(strip=True) if title_el else "Unknown"
                
                # Image
                img_el = row.find("div", class_="search_capsule")
                img_url = ""
                if img_el:
                    img_tag = img_el.find("img")
                    if img_tag and img_tag.has_attr("src"):
                        img_url = img_tag["src"]
                
                # Prices & Discount info
                final_el = row.find("div", class_="discount_final_price")
                orig_el = row.find("div", class_="discount_original_price")
                pct_el = row.find("div", class_="discount_pct")
                
                price_usd = 0.0
                normal_usd = 0.0
                savings = 0
                
                if final_el:
                    final_text = final_el.get_text(strip=True).replace("$", "").replace(",", ".").replace(" ", "")
                    try:
                        price_usd = float(final_text)
                    except ValueError:
                        pass
                        
                if orig_el:
                    orig_text = orig_el.get_text(strip=True).replace("$", "").replace(",", ".").replace(" ", "")
                    try:
                        normal_usd = float(orig_text)
                    except ValueError:
                        pass
                else:
                    normal_usd = price_usd
                    
                if pct_el:
                    pct_text = pct_el.get_text(strip=True).replace("-", "").replace("%", "").strip()
                    if pct_text.isdigit():
                        savings = int(pct_text)
                
                # Map genres
                genres = genres_cache.get(appid)
                if not genres:
                    genres = guess_genres_by_title(title)
                
                # Fast Cloudflare image URLs: small capsule (~15KB) for landscape cards, cover for details
                small_capsule = img_url or f"https://shared.cloudflare.steamstatic.com/store_item_assets/steam/apps/{appid}/header.jpg"
                
                parsed_deals.append({
                    "appid": appid,
                    "title": title,
                    "price_usd": price_usd,
                    "price_tl": round(price_usd * exchange_rate, 2),
                    "normal_usd": normal_usd,
                    "normal_tl": round(normal_usd * exchange_rate, 2),
                    "savings": savings,
                    "genres": genres,
                    "cover_url": f"https://shared.cloudflare.steamstatic.com/store_item_assets/steam/apps/{appid}/header.jpg",
                    "capsule_url": small_capsule
                })
            return parsed_deals
        except Exception as e:
            logger.warning(f"Error scraping Steam search page: {e}")
            return []

    # If it is a specific title query, search Steam directly
    if title_query:
        try:
            params = {
                "term": title_query,
                "cc": "tr",
                "l": "english"
            }
            formatted_deals = fetch_steam_search_page(params)
            
            # Queue missing genres for resolution in background
            appids_to_resolve = [d["appid"] for d in formatted_deals if d["appid"] not in genres_cache]
            if appids_to_resolve:
                fetch_genres_in_background(appids_to_resolve)
                
            return jsonify({"success": True, "deals": formatted_deals, "rate": exchange_rate})
        except Exception as ex:
            logger.error(f"Error searching Steam specials by title: {ex}")
            return jsonify({"success": False, "error": str(ex)})

    # Else, fetch general specials list (from in-memory cache, disk cache, or Steam scraper)
    now = _time.time()
    force_refresh = request.args.get("refresh") == "1" or request.args.get("refresh") == "true"
    deals_disk_cache = os.path.join(get_appdata_dir(), "deals_cache.json")
    
    # 1. In-memory cache (0ms)
    if not force_refresh and _deals_cache["data"] is not None and (now - _deals_cache["timestamp"]) < DEALS_CACHE_TTL:
        return jsonify({"success": True, "deals": _deals_cache["data"]["deals"], "rate": _deals_cache["data"]["rate"]})

    # 2. Persistent disk cache (1ms instant response on cold start)
    if not force_refresh and os.path.exists(deals_disk_cache) and os.path.getsize(deals_disk_cache) > 200:
        try:
            with open(deals_disk_cache, "r", encoding="utf-8") as f:
                disk_data = json.load(f)
            cached_time = disk_data.get("timestamp", 0)
            cached_deals = disk_data.get("deals", [])
            # Fresh disk cache (< 30 minutes)
            if cached_deals and (now - cached_time) < 1800:
                _deals_cache["data"] = disk_data
                _deals_cache["timestamp"] = cached_time
                return jsonify({"success": True, "deals": cached_deals, "rate": disk_data.get("rate", exchange_rate)})
        except Exception as e:
            logger.debug(f"Error reading disk deals cache: {e}")

    try:
        # Fetch 4 pages in parallel (200 specials total)
        pages_params = [
            {"specials": "1", "cc": "tr", "l": "english", "start": str(i * 50), "count": "50"}
            for i in range(4)
        ]
        
        all_deals = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            results = executor.map(fetch_steam_search_page, pages_params)
            for page_deals in results:
                all_deals.extend(page_deals)
        
        # Filter duplicates and ensure valid AppIDs
        seen_appids = set()
        unique_deals = []
        appids_to_resolve = []
        
        for deal in all_deals:
            appid = deal["appid"]
            if appid in seen_appids:
                continue
            seen_appids.add(appid)
            unique_deals.append(deal)
            if appid not in genres_cache:
                appids_to_resolve.append(appid)
                
        if appids_to_resolve:
            fetch_genres_in_background(appids_to_resolve)
            
        cache_data = {"deals": unique_deals, "rate": exchange_rate, "timestamp": now}
        _deals_cache["data"] = cache_data
        _deals_cache["timestamp"] = now
        
        # Save to disk cache for instant startup
        try:
            with open(deals_disk_cache, "w", encoding="utf-8") as f:
                json.dump(cache_data, f)
        except Exception:
            pass
        
        return jsonify({"success": True, "deals": unique_deals, "rate": exchange_rate})
    except Exception as e:
        logger.error(f"Error fetching Steam specials: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)})




# %%
_names_cache_lock = threading.Lock()

def resolve_names_in_background(appids, cache_path):
    """Resolves Steam App IDs in the background to avoid blocking the main server threads."""
    logger.info(f"Starting background name resolution for {len(appids)} apps...")
    
    # Reload names cache
    names_cache = {}
    with _names_cache_lock:
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    names_cache = json.load(f)
            except Exception:
                pass

    for appid in appids:
        # Check if already resolved by another request
        cached_val = names_cache.get(appid)
        if cached_val:
            if isinstance(cached_val, dict):
                if cached_val.get("name") != f"Steam App {appid}":
                    continue
            else:
                # Legacy string cache
                continue
                
        try:
            details = SteamAPI.get_app_details(appid)
            if details:
                name = details.get("name", f"Steam App {appid}")
                app_type = details.get("type", "game").lower()
                
                with _names_cache_lock:
                    current_cache = {}
                    if os.path.exists(cache_path) and os.path.getsize(cache_path) > 0:
                        try:
                            with open(cache_path, "r", encoding="utf-8") as f:
                                current_cache = json.load(f)
                        except Exception:
                            pass
                    current_cache[appid] = {"name": name, "type": app_type}
                    save_cache_atomic(cache_path, current_cache)
                logger.info(f"Background resolved AppID {appid} -> {name} ({app_type})")
            else:
                # Store fallback temporarily to prevent duplicate lookups
                with _names_cache_lock:
                    current_cache = {}
                    if os.path.exists(cache_path) and os.path.getsize(cache_path) > 0:
                        try:
                            with open(cache_path, "r", encoding="utf-8") as f:
                                current_cache = json.load(f)
                        except Exception:
                            pass
                    current_cache[appid] = {"name": f"Steam App {appid}", "type": "game"}
                    save_cache_atomic(cache_path, current_cache)
        except Exception as e:
            logger.warning(f"Error in background resolution for AppID {appid}: {e}")
            
        time.sleep(0.5)

# %%
def save_cache_atomic(cache_path, data):
    tmp_path = cache_path + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        os.replace(tmp_path, cache_path)
    except Exception as e:
        logger.error(f"Failed to save cache atomically: {e}")
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass

_merged_on_startup = False
_target_cache_path = None
_names_cache_mem = None
_library_cache = {"data": None, "timestamp": 0}

RE_ACF_APPID = re.compile(r'"appid"\s+"(\d+)"')
RE_ACF_NAME = re.compile(r'"name"\s+"([^"]+)"')
RE_ACF_BUILDID = re.compile(r'"buildid"\s+"([^"]+)"')
RE_ACF_LIGHTNING = re.compile(r'"ProjectLightning"\s+"1"')

def get_cache_path():
    global _merged_on_startup, _target_cache_path
    if _target_cache_path:
        return _target_cache_path

    appdata = os.environ.get("APPDATA")
    if appdata:
        pdir = os.path.join(appdata, "SteaMRogue")
    else:
        pdir = os.path.expanduser("~/.steamrogue")
    os.makedirs(pdir, exist_ok=True)
    target_path = os.path.join(pdir, "app_names_cache.json")
    _target_cache_path = target_path
    
    # Merge bundled cache with persistent cache on startup ONCE
    if not _merged_on_startup:
        _merged_on_startup = True
        local_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_names_cache.json")
        if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
            try:
                with open(local_path, "r", encoding="utf-8") as f:
                    bundled_data = json.load(f)
                
                persistent_data = {}
                if os.path.exists(target_path) and os.path.getsize(target_path) > 0:
                    try:
                        with open(target_path, "r", encoding="utf-8") as f:
                            persistent_data = json.load(f)
                    except Exception:
                        pass
                
                merged = False
                for k, v in bundled_data.items():
                    if k not in persistent_data or not isinstance(persistent_data[k], dict) or persistent_data[k].get("name") == f"Steam App {k}":
                        persistent_data[k] = v
                        merged = True
                
                if merged or not os.path.exists(target_path):
                    save_cache_atomic(target_path, persistent_data)
            except Exception as e:
                logger.warning(f"Error merging cache files on startup: {e}")
                
    return target_path

def get_in_memory_names_cache():
    global _names_cache_mem
    if _names_cache_mem is not None:
        return _names_cache_mem
    cache_path = get_cache_path()
    with _names_cache_lock:
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    _names_cache_mem = json.load(f)
                    return _names_cache_mem
            except Exception:
                pass
        _names_cache_mem = {}
        return _names_cache_mem

# API Endpoint: GET /api/library
@app.route("/api/library", methods=["GET"])
def get_library():
    """Scans stplug-in for all unlocked games, merges with ACF manifests, and returns full library list with ultrafast caching."""
    if not config.steam_path:
        return jsonify({"games": []})

    now = time.time()
    if _library_cache["data"] is not None and (now - _library_cache["timestamp"]) < 3.0:
        return jsonify({"games": _library_cache["data"]})
        
    games_dict = {}  # appid -> game_data
    try:
        # 1. Scan stplug-in and lua folders for all unlocked AppIDs
        unlocked_appids = set()
        for folder_name in ["stplug-in", "lua"]:
            plugin_folder = os.path.join(config.steam_path, "config", folder_name)
            if os.path.isdir(plugin_folder):
                for file in os.listdir(plugin_folder):
                    if file.lower().endswith(".lua"):
                        try:
                            name_part = os.path.splitext(file)[0]
                            if name_part.isdigit():
                                unlocked_appids.add(name_part)
                        except Exception:
                            pass
                        
        # 2. In-memory names cache (zero disk lag)
        cache_path = get_cache_path()
        names_cache = get_in_memory_names_cache()

        # 3. Fast regex scan of ACF manifest files across all library folders
        libraries = FileManager.get_library_folders(config.steam_path)
        blacklist_ids = {228980, 250820, 1002, 211, 1113740, 228989, 228990}
        tool_keywords = ("steamworks", "redistributable", "sdk", "dedicated server", "tool", "development", "compiler", "beta", "steamvr", "common redist")

        for _, lib_path in libraries:
            apps_dir = os.path.join(lib_path, "steamapps")
            if not os.path.isdir(apps_dir):
                continue
                
            for filename in os.listdir(apps_dir):
                if filename.startswith("appmanifest_") and filename.endswith(".acf"):
                    acf_path = os.path.join(apps_dir, filename)
                    try:
                        with open(acf_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        
                        m_id = RE_ACF_APPID.search(content)
                        if not m_id:
                            continue
                        appid = m_id.group(1)
                        appid_int = int(appid)
                        
                        if appid_int in blacklist_ids:
                            continue
                            
                        m_name = RE_ACF_NAME.search(content)
                        name = m_name.group(1) if m_name else f"Steam App {appid}"
                        name_lower = name.lower()
                        if any(k in name_lower for k in tool_keywords):
                            continue
                            
                        m_bid = RE_ACF_BUILDID.search(content)
                        buildid = m_bid.group(1) if m_bid else ""
                        
                        is_custom = bool(RE_ACF_LIGHTNING.search(content))
                        is_dummy_build = (buildid == "12345678")
                        is_unlocked = (appid in unlocked_appids)
                        
                        if is_custom or is_dummy_build or is_unlocked:
                            games_dict[appid] = {
                                "appid": appid,
                                "name": name,
                                "library_path": lib_path,
                                "installed": True
                            }
                    except Exception as e:
                        logger.debug(f"Failed parsing ACF {filename}: {e}")

        # 4. Include unlocked AppIDs that are missing their ACF files (marked as not installed)
        appids_to_resolve = []
        for appid in unlocked_appids:
            if appid not in games_dict:
                appid_int = int(appid) if appid.isdigit() else 0
                if appid_int in blacklist_ids:
                    continue
                
                # Check cache first
                name = f"Steam App {appid}"
                app_type = "game"
                cached = names_cache.get(appid)
                
                is_fallback = False
                if cached:
                    if isinstance(cached, dict):
                        name = cached.get("name", name)
                        app_type = cached.get("type", "game")
                        if name == f"Steam App {appid}":
                            is_fallback = True
                    else:
                        name = cached
                        app_type = "game"
                        
                if not cached or is_fallback:
                    appids_to_resolve.append(appid)
                    
                if app_type not in ["game", "demo"]:
                    continue
                    
                games_dict[appid] = {
                    "appid": appid,
                    "name": name,
                    "library_path": config.steam_path,
                    "installed": False
                }
                
        if appids_to_resolve:
            threading.Thread(
                target=resolve_names_in_background,
                args=(appids_to_resolve, cache_path),
                daemon=True
            ).start()

        games_list = list(games_dict.values())
        _library_cache["data"] = games_list
        _library_cache["timestamp"] = time.time()

        # Background pre-fetch covers for library games so they are instant on disk
        def prefetch_library_covers(games):
            covers_dir = get_covers_cache_dir()
            for g in games:
                aid = g.get("appid")
                if not aid:
                    continue
                if find_local_cover(config.steam_path, aid):
                    continue
                dest = os.path.join(covers_dir, f"{aid}.jpg")
                if os.path.isfile(dest) and os.path.getsize(dest) > 500:
                    continue
                try:
                    url = f"https://shared.cloudflare.steamstatic.com/store_item_assets/steam/apps/{aid}/library_600x900.jpg"
                    r = requests.get(url, timeout=3.0, headers={"User-Agent": "Mozilla/5.0"})
                    if r.status_code == 200 and len(r.content) > 500:
                        with open(dest, "wb") as f:
                            f.write(r.content)
                    time.sleep(0.04)
                except Exception:
                    pass

        threading.Thread(target=prefetch_library_covers, args=(games_list,), daemon=True).start()

        return jsonify({"games": games_list})
    except Exception as e:
        logger.error(f"Error fetching library catalog: {e}")
        return jsonify({"games": []})

# %%
# API Endpoint: POST /api/remove
@app.route("/api/remove", methods=["POST"])
def remove_game():
    data = request.json or {}
    appid = data.get("appid", "").strip()
    
    if not appid:
        return jsonify({"success": False, "error": "AppID is required"})
        
    try:
        valid_id = validator.validate_appid(appid)
        
        # Clean game files and VDF directly without terminating Steam
        FileManager.clean_game_files(config.steam_path, valid_id)
        FileManager.remove_from_library_folders(config.steam_path, valid_id)
        _library_cache["timestamp"] = 0
        
        logger.info(f"Removed game AppID {valid_id} from library files. Steam was kept running.")
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Failed to remove game: {e}")
        return jsonify({"success": False, "error": str(e)})

# %%
# API Endpoint: POST /api/restart_steam
@app.route("/api/restart_steam", methods=["POST"])
def restart_steam():
    # 1. Resolve steam.exe path accurately
    steam_exe = None
    if config.steam_path and os.path.isdir(config.steam_path):
        cand = os.path.join(config.steam_path, "steam.exe")
        if os.path.isfile(cand):
            steam_exe = cand
            
    if not steam_exe:
        # Check Windows registry
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as key:
                val, _ = winreg.QueryValueEx(key, "SteamExe")
                if val and os.path.isfile(val):
                    steam_exe = os.path.normpath(val)
        except Exception:
            pass

    if not steam_exe:
        # Check common paths
        for p in [r"C:\Program Files (x86)\Steam\steam.exe", r"C:\Program Files\Steam\steam.exe"]:
            if os.path.isfile(p):
                steam_exe = p
                break

    if not steam_exe or not os.path.isfile(steam_exe):
        return jsonify({"success": False, "error": "steam.exe bulunamadı"})

    try:
        # 2. Terminate Steam processes cleanly if running
        if validator.is_steam_running():
            logger.info("Closing Steam and child processes for restart...")
            validator.kill_steam()
            
            # Wait up to 5 seconds until steam.exe has truly stopped
            for _ in range(25):
                time.sleep(0.2)
                if not validator.is_steam_running():
                    break
            time.sleep(0.6)  # Give Windows OS time to release file locks & sockets

        # Reset ghost ActiveProcess in registry so Steam doesn't get blocked by orphaned PIDs
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam\ActiveProcess", 0, winreg.KEY_SET_VALUE) as k:
                winreg.SetValueEx(k, "pid", 0, winreg.REG_DWORD, 0)
                winreg.SetValueEx(k, "ActiveUser", 0, winreg.REG_DWORD, 0)
        except Exception:
            pass

        # 3. Launch Steam cleanly via native Windows Shell with Steam working directory
        steam_dir = os.path.dirname(steam_exe)
        logger.info(f"Launching Steam: {steam_exe} (cwd: {steam_dir})")
        started = False
        try:
            import ctypes
            res = ctypes.windll.shell32.ShellExecuteW(
                None, "open", steam_exe, "-cef-disable-gpu steam://open/games", steam_dir, 1
            )
            started = (res > 32)
        except Exception as sh_err:
            logger.warning(f"ShellExecuteW failed: {sh_err}")

        if not started:
            try:
                proc = subprocess.Popen(
                    [steam_exe, "-cef-disable-gpu", "steam://open/games"],
                    cwd=steam_dir,
                    creationflags=subprocess.DETACHED_PROCESS | 0x08000000,
                    close_fds=True
                )
                started = proc.poll() is None
            except Exception as popen_err:
                logger.error(f"Popen failed: {popen_err}")

        if started:
            logger.info("Restarted Steam client successfully.")
            return jsonify({"success": True, "message": "Steam başarıyla yeniden başlatıldı."})
        else:
            return jsonify({"success": False, "error": "Steam başlatılamadı."})

    except Exception as e:
        logger.error(f"Failed to restart Steam: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)})

# %%
# API Endpoint: POST /api/minimize
@app.route("/api/minimize", methods=["POST"])
def minimize_window():
    try:
        import webview
        active_window = webview.active_window()
        if active_window:
            active_window.minimize()
            return jsonify({"success": True})
    except Exception:
        pass
    return jsonify({"success": False})

# %%
# API Endpoint: POST /api/close
@app.route("/api/close", methods=["POST"])
def close_window():
    logger.info("Close request received. Shutting down backend.")
    try:
        updater.run_shutdown_checks(config.manifest_repos, config.steam_path)
    except Exception:
        pass
    os._exit(0)

# %%
# API Endpoint: GET /api/search_store
@app.route("/api/search_store", methods=["GET"])
def search_store():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"results": []})
        
    extracted_id = validator.extract_appid(query)
    if extracted_id.isdigit():
        details = SteamAPI.get_app_details(extracted_id)
        if details:
            return jsonify({
                "results": [{
                    "id": str(extracted_id),
                    "name": details.get("name", f"Steam App {extracted_id}"),
                    "tiny_image": f"https://cdn.cloudflare.steamstatic.com/steam/apps/{extracted_id}/capsule_sm_120.jpg",
                    "price": details.get("price_overview", {}).get("final_formatted", "")
                }]
            })
            
    results = SteamAPI.search_store(query)
    return jsonify({"results": results})

# %%
# API Endpoint: GET /api/details
@app.route("/api/details", methods=["GET"])
def get_game_details():
    raw_appid = request.args.get("appid", "").strip()
    appid = validator.extract_appid(raw_appid)
    if not appid:
        return jsonify({"success": False, "error": "AppID is required"})
    details = SteamAPI.get_app_details(appid)
    if details:
        return jsonify({"success": True, "details": details})
    return jsonify({"success": False, "error": "Details not found"})

# %%
# API Endpoint: GET /api/bypass_status
@app.route("/api/bypass_status", methods=["GET"])
def get_bypass_status():
    if not config.steam_path or not os.path.isdir(config.steam_path):
        return jsonify({"status": "INACTIVE", "installed": False, "dlls": [], "has_plugins": False})
    
    dlls = ["dwmapi.dll", "xinput1_4.dll", "OpenSteamTool.dll"]
    installed_dlls = []
    for dll in dlls:
        if os.path.isfile(os.path.join(config.steam_path, dll)):
            installed_dlls.append(dll)
            
    st_plugin = os.path.join(config.steam_path, "config", "stplug-in")
    has_plugins = os.path.isdir(st_plugin) and len(os.listdir(st_plugin)) > 0 if os.path.isdir(st_plugin) else False
    
    installed = len(installed_dlls) > 0
    return jsonify({
        "installed": installed,
        "dlls": installed_dlls,
        "has_plugins": has_plugins,
        "status": "ACTIVE" if installed else "INACTIVE"
    })

def get_bundled_steamtools_dir():
    """Returns the path to bundled steamtools_files if available."""
    if getattr(sys, 'frozen', False):
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    st_dir = os.path.join(base_dir, "steamtools_files")
    if os.path.isdir(st_dir):
        return st_dir
    local_st = os.path.join(os.path.dirname(os.path.abspath(__file__)), "steamtools_files")
    if os.path.isdir(local_st):
        return local_st
    return None

def check_steamtools_installed():
    """Checks if SteamTools hook DLLs are present in Steam directory."""
    if not config.steam_path or not os.path.isdir(config.steam_path):
        return False, []
    target_files = ["dwmapi.dll", "xinput1_4.dll", "opensteamtool.dll"]
    present = []
    for f in os.listdir(config.steam_path):
        if f.lower() in target_files:
            present.append(f)
    is_installed = len(present) >= len(target_files)
    return is_installed, present

def ensure_steamtools_installed_auto():
    """Guaranteed auto-install on startup/initial run."""
    try:
        if not config.steam_path or not os.path.isdir(config.steam_path):
            return False
        is_installed, present = check_steamtools_installed()
        if is_installed:
            logger.info("[SteamTools Auto-Setup] SteamTools is already installed and verified.")
            return True

        st_dir = get_bundled_steamtools_dir()
        if not st_dir:
            logger.info("[SteamTools Auto-Setup] Bundled steamtools_files folder not found, skipping local copy.")
            return False

        import shutil
        target_files = ["dwmapi.dll", "xinput1_4.dll", "OpenSteamTool.dll"]
        installed_count = 0
        for f in target_files:
            src = os.path.join(st_dir, f)
            dst = os.path.join(config.steam_path, f)
            if os.path.isfile(src) and not os.path.isfile(dst):
                try:
                    shutil.copy2(src, dst)
                    installed_count += 1
                    logger.info(f"[SteamTools Auto-Setup] Auto-installed {f} to {dst}")
                except Exception as e:
                    logger.warning(f"[SteamTools Auto-Setup] Failed to copy {f}: {e}")
        logger.info(f"[SteamTools Auto-Setup] Auto-setup complete ({installed_count} files installed).")
        return True
    except Exception as e:
        logger.error(f"[SteamTools Auto-Setup] Error during auto-setup: {e}")
        return False

# %%
# API Endpoint: POST /api/install_steamtools
@app.route("/api/install_steamtools", methods=["POST"])
def install_steamtools():
    if not config.steam_path or not os.path.isdir(config.steam_path):
        return jsonify({"success": False, "error": "Steam kurulum dizini bulunamadı veya geçersiz."})

    # Check if already installed
    is_installed, present = check_steamtools_installed()
    if is_installed:
        return jsonify({
            "success": True,
            "already_installed": True,
            "message": "SteamTools zaten kurulu ve Steam üzerinde aktif durumda!"
        })

    # 1. Try installing from bundled files first (0ms, 100% offline guaranteed)
    st_dir = get_bundled_steamtools_dir()
    if st_dir:
        try:
            import shutil
            target_files = ["dwmapi.dll", "xinput1_4.dll", "OpenSteamTool.dll"]
            copied = 0
            for f in target_files:
                src = os.path.join(st_dir, f)
                dst = os.path.join(config.steam_path, f)
                if os.path.isfile(src):
                    shutil.copy2(src, dst)
                    copied += 1
            if copied > 0:
                logger.info(f"SteamTools successfully installed from bundled files ({copied} files).")
                return jsonify({
                    "success": True,
                    "already_installed": False,
                    "message": "SteamTools kancası başarıyla kuruldu ve aktifleştirildi!"
                })
        except Exception as err:
            logger.warning(f"Bundled copy failed, falling back to download: {err}")

    # 2. Fallback to download from Dropbox if bundled files not found
    try:
        url = "https://www.dropbox.com/scl/fo/kd6qy4kca8qgx679o2g18/AJD_YjPCPRyLsMUCKZTkcfE?rlkey=tkdu1ytkp23ml7ibbkzrcekm8&st=kq2z32bt&dl=1"
        headers = {"User-Agent": "Mozilla/5.0"}
        logger.info("Downloading SteamTools plugins ZIP from Dropbox...")
        
        try:
            response = requests.get(url, headers=headers, timeout=45)
        except requests.exceptions.SSLError:
            response = requests.get(url, headers=headers, timeout=45, verify=False)
            
        if response.status_code != 200:
            return jsonify({"success": False, "error": f"Download failed (HTTP {response.status_code})"})
            
        import tempfile
        import zipfile
        
        temp_zip = os.path.join(tempfile.gettempdir(), "steamtools.zip")
        with open(temp_zip, "wb") as f:
            f.write(response.content)
            
        logger.info("Extracting SteamTools DLLs...")
        target_files = {"dwmapi.dll", "xinput1_4.dll", "opensteamtool.dll"}
        extracted_count = 0
        
        with zipfile.ZipFile(temp_zip, "r") as zip_ref:
            for member in zip_ref.namelist():
                basename = os.path.basename(member).lower()
                if basename in target_files:
                    dest_path = os.path.join(config.steam_path, os.path.basename(member))
                    with zip_ref.open(member) as source, open(dest_path, "wb") as target:
                        target.write(source.read())
                    logger.info(f"Extracted {basename} to {dest_path}")
                    extracted_count += 1
                elif basename.endswith(".zip"):
                    inner_temp_dir = os.path.join(tempfile.gettempdir(), "steamtools_inner")
                    os.makedirs(inner_temp_dir, exist_ok=True)
                    zip_ref.extract(member, inner_temp_dir)
                    inner_zip_path = os.path.join(inner_temp_dir, member)
                    
                    with zipfile.ZipFile(inner_zip_path, "r") as inner_zip:
                        for inner_member in inner_zip.namelist():
                            inner_basename = os.path.basename(inner_member).lower()
                            if inner_basename in target_files:
                                dest_path = os.path.join(config.steam_path, os.path.basename(inner_member))
                                with inner_zip.open(inner_member) as source, open(dest_path, "wb") as target:
                                    target.write(source.read())
                                logger.info(f"Extracted inner {inner_basename} to {dest_path}")
                                extracted_count += 1
                                
        try:
            os.remove(temp_zip)
        except Exception:
            pass
            
        if extracted_count > 0:
            return jsonify({"success": True, "already_installed": False, "message": f"SteamTools başarıyla kuruldu ({extracted_count} dosya)!"})
        else:
            return jsonify({"success": False, "error": "Paket içerisinde SteamTools DLL dosyaları bulunamadı."})
            
    except Exception as e:
        logger.error(f"Failed to install SteamTools: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)})

# %%
# API Endpoint: POST /api/uninstall_steamtools
@app.route("/api/uninstall_steamtools", methods=["POST"])
def uninstall_steamtools():
    if not config.steam_path or not os.path.isdir(config.steam_path):
        return jsonify({"success": False, "error": "Steam path is not configured or invalid"})
        
    try:
        files_to_remove = ["dwmapi.dll", "xinput1_4.dll", "OpenSteamTool.dll", "hid.dll", "steam.cfg"]
        removed = []
        for file in files_to_remove:
            file_path = os.path.join(config.steam_path, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
                removed.append(file)
        return jsonify({"success": True, "removed": removed})
    except Exception as e:
        logger.error(f"Failed to uninstall SteamTools: {e}")
        return jsonify({"success": False, "error": str(e)})

def _clean_game_fix_directory(game_dir):
    """Restores original files from .bak and removes applied crack/fix files in a game folder."""
    if not os.path.isdir(game_dir):
        return
    
    crack_patterns = [
        "onlinefix.ini", "onlinefix64.dll", "onlinefix.dll", "steamoverlay64.dll", "steamoverlay.dll",
        "anadius.cfg", "anadius64.dll", "anadius32.dll", "anadius.dll",
        "cream_api.ini", "smokeapi.config.json"
    ]
    
    try:
        import shutil
        for root, dirs, files in os.walk(game_dir):
            for file in files:
                lower = file.lower()
                # 1. Restore backups
                if lower.endswith(".bak"):
                    orig_name = file[:-4]
                    orig_path = os.path.join(root, orig_name)
                    bak_path = os.path.join(root, file)
                    try:
                        shutil.copy2(bak_path, orig_path)
                        os.remove(bak_path)
                        logger.info(f"[Nuke] Restored backup: {orig_path}")
                    except Exception as e:
                        logger.warning(f"[Nuke] Failed to restore {bak_path}: {e}")
                # 2. Remove crack files
                elif lower in crack_patterns or lower.startswith("denuvoticket"):
                    fpath = os.path.join(root, file)
                    try:
                        os.remove(fpath)
                        logger.info(f"[Nuke] Removed fix file: {fpath}")
                    except Exception as e:
                        logger.warning(f"[Nuke] Failed to remove {fpath}: {e}")
    except Exception as e:
        logger.warning(f"[Nuke] Error cleaning game directory {game_dir}: {e}")

# %%
# API Endpoint: POST /api/self_destruct
@app.route("/api/self_destruct", methods=["POST"])
def api_self_destruct():
    """
    Nukes all modifications made by SteaMRogue:
    1. Removes all added games (LUA configs in stplug-in)
    2. Removes SteamTools hook DLLs & steam.cfg
    3. Cleans all applied bypass fixes & restores original backups in games
    4. Cleans app data, cache, logs, shortcuts
    5. Self-deletes and removes SteaMRogue from the system
    """
    logger.warning("[Nuke] !!! INITIATING SYSTEM SELF-DESTRUCT AND CLEANUP !!!")
    
    # 1. Close Steam if running so files are not locked
    if os.name == 'nt':
        try:
            subprocess.run(["taskkill", "/F", "/IM", "steam.exe"], capture_output=True, creationflags=0x08000000)
        except Exception:
            pass

    # 2. Clean SteamTools hooks and added games
    if config.steam_path and os.path.isdir(config.steam_path):
        # Remove hook DLLs
        for f in ["dwmapi.dll", "xinput1_4.dll", "OpenSteamTool.dll", "hid.dll", "steam.cfg"]:
            p = os.path.join(config.steam_path, f)
            if os.path.isfile(p):
                try:
                    os.remove(p)
                    logger.info(f"[Nuke] Removed Steam hook file: {p}")
                except Exception as e:
                    logger.warning(f"[Nuke] Failed to remove {p}: {e}")

        # Clean stplug-in (.lua game manifests)
        st_plugin = os.path.join(config.steam_path, "config", "stplug-in")
        if os.path.isdir(st_plugin):
            try:
                import shutil
                for item in os.listdir(st_plugin):
                    item_path = os.path.join(st_plugin, item)
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path, ignore_errors=True)
                logger.info(f"[Nuke] Cleaned stplug-in directory: {st_plugin}")
            except Exception as e:
                logger.warning(f"[Nuke] Error cleaning stplug-in: {e}")

        # Clean stconfig.vdf
        st_config = os.path.join(config.steam_path, "config", "stconfig.vdf")
        if os.path.isfile(st_config):
            try:
                os.remove(st_config)
            except Exception:
                pass

    # 3. Clean all applied bypass / onlinefix files
    try:
        # Check applied_fixes.json
        fixes_file = os.path.join(get_appdata_dir(), "applied_fixes.json")
        if os.path.isfile(fixes_file):
            try:
                with open(fixes_file, "r", encoding="utf-8") as f:
                    records = json.load(f)
                for r in records:
                    d = r.get("dest_dir")
                    if d and os.path.isdir(d):
                        _clean_game_fix_directory(d)
            except Exception as e:
                logger.warning(f"[Nuke] Error processing applied_fixes.json: {e}")

        # Also scan library folders for any common game directories
        try:
            libs = get_all_steam_libraries()
            for lib in libs:
                common_dir = os.path.join(lib, "steamapps", "common")
                if os.path.isdir(common_dir):
                    for game_folder in os.listdir(common_dir):
                        full_game_dir = os.path.join(common_dir, game_folder)
                        if os.path.isdir(full_game_dir):
                            _clean_game_fix_directory(full_game_dir)
        except Exception as e:
            logger.warning(f"[Nuke] Error scanning libraries during nuke: {e}")
    except Exception as e:
        logger.warning(f"[Nuke] Error cleaning game fixes: {e}")

    # 4. Generate detached self-destruct batch script
    import tempfile
    bat_path = os.path.join(tempfile.gettempdir(), "steamrogue_nuke.bat")
    
    local_app_dir = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "steamtools-auto")
    appdata_sr = os.path.join(os.environ.get("APPDATA", ""), "SteaMRogue")
    appdata_st = os.path.join(os.environ.get("APPDATA", ""), "steamtools-auto")
    user_prof = os.environ.get("USERPROFILE", "")
    
    bat_content = f"""@echo off
chcp 65001 > nul
timeout /t 2 /nobreak > nul

taskkill /f /im SteamTools_Auto_Backend.exe > nul 2>&1
taskkill /f /im SteaMRogue.exe > nul 2>&1
taskkill /f /im electron.exe > nul 2>&1
timeout /t 1 /nobreak > nul

rmdir /s /q "{local_app_dir}" > nul 2>&1
rmdir /s /q "{appdata_sr}" > nul 2>&1
rmdir /s /q "{appdata_st}" > nul 2>&1

del /f /q "{user_prof}\\Desktop\\SteaMRogue.lnk" > nul 2>&1
del /f /q "{user_prof}\\Desktop\\SteaMRogue Setup *.exe" > nul 2>&1
del /f /q "{user_prof}\\OneDrive\\Desktop\\SteaMRogue.lnk" > nul 2>&1
del /f /q "{user_prof}\\OneDrive\\Desktop\\SteaMRogue Setup *.exe" > nul 2>&1
del /f /q "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\SteaMRogue.lnk" > nul 2>&1

reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\steamtools-auto" /f > nul 2>&1

(goto) 2>nul & del "%~f0"
"""

    with open(bat_path, "w", encoding="utf-8") as f:
        f.write(bat_content)

    logger.info(f"[Nuke] Created self-destruct batch: {bat_path}")

    # Launch detached batch script
    subprocess.Popen(["cmd.exe", "/c", bat_path], creationflags=subprocess.DETACHED_PROCESS | 0x08000000, close_fds=True)

    return jsonify({
        "success": True,
        "message": "Sistem imha işlemi ve kaldırma süreci başarıyla başlatıldı."
    })


# %%
# API Endpoint: POST /api/play
@app.route("/api/play", methods=["POST"])
def play_game():
    data = request.json or {}
    appid = data.get("appid", "").strip()
    if not appid:
        return jsonify({"success": False, "error": "AppID is required"})
    try:
        url = f"steam://run/{appid}"
        webbrowser.open(url)
        logger.info(f"Launched game AppID {appid} via steam://run/")
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Failed to play game {appid}: {e}")
        return jsonify({"success": False, "error": str(e)})



# %%
# API Endpoint: POST /api/import
@app.route("/api/import", methods=["POST"])
def import_files():
    """Handles manual upload/import of .lua, .manifest, or .zip files."""
    if not config.steam_path:
        return jsonify({"success": False, "error": "Steam path not configured"})
        
    uploaded_files = request.files.getlist("files")
    if not uploaded_files:
        return jsonify({"success": False, "error": "No files provided"})
        
    try:
        # Create temp folder for files
        import tempfile
        temp_dir = tempfile.mkdtemp(prefix="lightning-import")
        
        files_payload = []
        for file in uploaded_files:
            file_path = os.path.join(temp_dir, file.filename)
            file.save(file_path)
            files_payload.append({
                "path": file_path,
                "name": file.filename
            })
            
        # Call the file manager's import logic
        # We need to adapt importDroppedFiles javascript logic into Python
        plugin_folder = os.path.join(config.steam_path, "config", "stplug-in")
        depotcache_folder = os.path.join(config.steam_path, "config", "depotcache")
        lua_folder = os.path.join(config.steam_path, "config", "lua")
        official_depotcache = os.path.join(config.steam_path, "depotcache")
        
        for folder in [plugin_folder, depotcache_folder, lua_folder, official_depotcache]:
            os.makedirs(folder, exist_ok=True)
            
        imported_count = 0
        ignored_count = 0
        
        import zipfile
        for item in files_payload:
            name = item["name"]
            path = item["path"]
            ext = os.path.splitext(name)[1].lower()
            
            if ext == ".lua":
                shutil.copy2(path, os.path.join(plugin_folder, name))
                shutil.copy2(path, os.path.join(lua_folder, name))
                imported_count += 1
            elif ext == ".manifest":
                shutil.copy2(path, os.path.join(depotcache_folder, name))
                shutil.copy2(path, os.path.join(official_depotcache, name))
                imported_count += 1
            elif ext == ".zip":
                # Unpack and scan
                with zipfile.ZipFile(path) as z:
                    for z_info in z.infolist():
                        if z_info.is_dir():
                            continue
                        z_name = os.path.basename(z_info.filename)
                        z_ext = os.path.splitext(z_name)[1].lower()
                        
                        if z_ext == ".lua":
                            with open(os.path.join(plugin_folder, z_name), "wb") as out_f:
                                out_f.write(z.read(z_info.filename))
                            with open(os.path.join(lua_folder, z_name), "wb") as out_f:
                                out_f.write(z.read(z_info.filename))
                            imported_count += 1
                        elif z_ext == ".manifest":
                            content = z.read(z_info.filename)
                            with open(os.path.join(depotcache_folder, z_name), "wb") as out_f:
                                out_f.write(content)
                            with open(os.path.join(official_depotcache, z_name), "wb") as out_f:
                                out_f.write(content)
                            imported_count += 1
            else:
                ignored_count += 1
                
        # Clean temp folder
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        return jsonify({
            "success": True, 
            "importedCount": imported_count,
            "ignoredCount": ignored_count
        })
        
    except Exception as e:
        logger.error(f"Failed to import files: {e}")
        return jsonify({"success": False, "error": str(e)})

# %%
# Background Addition worker
def add_game_thread_worker(appid: str):
    """Executes the game addition logic in a background thread."""
    global task_statuses
    
    def update_status(msg: str, progress: int):
        with task_lock:
            task_statuses[appid] = {
                "status": "running",
                "message": msg,
                "progress": progress
            }
        logger.info(f"[AppID {appid}] {msg} ({progress}%)")

    try:
        # Check Steam Path
        if not config.steam_path:
            raise SteamToolsException("Steam path not configured.")
            
        update_status("Validating AppID...", 20)
        valid_id = validator.validate_appid(appid)
            
        # 1. Fetch Store API details
        update_status("Retrieving game information from Steam API...", 30)
        game_details = SteamAPI.get_app_details(valid_id)
        game_name = game_details["name"] if game_details else f"Steam App {valid_id}"
        
        # 2. Search Manifest
        update_status("Searching manifest repositories...", 40)
        
        def download_progress_cb(downloaded, total, status_text):
            pct = 40 + int((downloaded / max(1, total)) * 30)  # spans 40% to 70%
            update_status(status_text, pct)
            
        found_data = ManifestFinder.find_online(valid_id, config.manifest_repos, progress_callback=download_progress_cb)
        
        manifests = []
        luas = []
        
        if found_data:
            manifests = found_data["manifests"]
            luas = found_data["luas"]
        else:
            update_status("Scanning local cache database...", 72)
            local_manifests = ManifestFinder.scan_local_depotcache(config.steam_path, valid_id)
            if local_manifests:
                manifests = local_manifests
                
        # If no manifest and no lua was found, inform the user clearly that this game cannot be added
        if not manifests and not luas:
            raise SteamToolsException(
                f"'{game_name}' (AppID: {valid_id}) için sunucularda veya yerel önbellekte indirilebilir manifest/yapılandırma dosyası bulunamadı.\n\n"
                "Bu oyun için gerekli dosyalar topluluk depolarında mevcut olmadığı için kütüphaneye eklenemiyor."
            )

        # 3. Save manifest & bypass configuration files
        update_status("Copying manifest & bypass configuration files...", 85)
        FileManager.write_steamtools_files(config.steam_path, manifests, luas)
            
        # 4. Clean any existing dummy ACF manifest or libraryfolders entries
        # SteamTools allows the game to appear in Steam library naturally.
        # By NOT pre-generating a dummy appmanifest.acf or pre-registering in libraryfolders.vdf,
        # Steam's native install dialog ("ŞURAYA YÜKLE: C: / D:") lets the user choose their own drive in Steam!
        update_status("Finalizing game configuration...", 95)
        FileManager.clean_acf_manifests(config.steam_path, valid_id)
        FileManager.remove_from_library_folders(config.steam_path, valid_id)
        _library_cache["timestamp"] = 0
        
        # Success state
        with task_lock:
            task_statuses[appid] = {
                "status": "success",
                "message": "Game successfully added!",
                "progress": 100
            }
            
    except Exception as e:
        logger.error(f"Error adding game {appid}: {e}", exc_info=True)
        with task_lock:
            task_statuses[appid] = {
                "status": "failed",
                "error": str(e),
                "progress": 100
            }

# %%
# API Endpoint: POST /api/add
@app.route("/api/add", methods=["POST"])
def add_game():
    data = request.json or {}
    raw_appid = data.get("appid", "").strip()
    appid = validator.extract_appid(raw_appid)
    
    if not appid:
        return jsonify({"success": False, "error": "AppID veya geçerli Steam linki gereklidir"})
        
    try:
        # Check validation of AppID first
        appid = validator.validate_appid(appid)
    except SteamToolsException as e:
        return jsonify({"success": False, "error": str(e)})
        
    # Start background task
    with task_lock:
        task_statuses[appid] = {
            "status": "running",
            "message": "Initializing addition task...",
            "progress": 0
        }
        
    thread = threading.Thread(target=add_game_thread_worker, args=(appid,), daemon=True)
    thread.start()
    
    return jsonify({"success": True})

# %%
# API Endpoint: GET /api/add_status
@app.route("/api/add_status", methods=["GET"])
def add_game_status():
    appid = request.args.get("appid", "").strip()
    if not appid:
        return jsonify({"status": "idle"})
        
    with task_lock:
        status_info = task_statuses.get(appid, {"status": "idle"})
        res_info = dict(status_info)
        
        # Keep completed / failed terminal state for 30s before deletion so frontend never misses it
        now = time.time()
        if status_info.get("status") in ["success", "failed"]:
            if "_finished_at" not in status_info:
                status_info["_finished_at"] = now
            elif now - status_info["_finished_at"] > 30:
                del task_statuses[appid]
                
        return jsonify(res_info)

# %%
# OnlineFix Automation Endpoints and Helpers
onlinefix_download_statuses = {}
onlinefix_lock = threading.Lock()
onlinefix_cancelled_tasks = set()
onlinefix_cancel_lock = threading.Lock()

_cached_gofile_salt = None
_gofile_salt_expiry = 0
_cached_gofile_token = None
_gofile_token_lock = threading.Lock()

def get_gofile_salt() -> str:
    global _cached_gofile_salt, _gofile_salt_expiry
    fallback_salt = "12af056dacea0b"
    
    # Suppress SSL verification warnings
    try:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    except Exception:
        pass
        
    # Cache salt for 4 hours to avoid querying GitHub on every request
    current_time = time.time()
    if _cached_gofile_salt and current_time < _gofile_salt_expiry:
        return _cached_gofile_salt
        
    # 1. Try to fetch from martadams89/gofile-dl on GitHub (highly active, updated salt)
    try:
        url = "https://raw.githubusercontent.com/martadams89/gofile-dl/main/run.py"
        resp = requests.get(url, timeout=5, verify=False)
        if resp.status_code == 200:
            match = re.search(r'GOFILE_WT_SALT.*?\"([a-zA-Z0-9]{10,20})\"', resp.text)
            if match:
                salt = match.group(1).strip()
                if salt:
                    _cached_gofile_salt = salt
                    _gofile_salt_expiry = current_time + 14400 # 4 hours
                    logger.info(f"Dynamically resolved Gofile salt from gofile-dl: {salt}")
                    return salt
    except Exception as e:
        logger.warning(f"Failed to fetch Gofile salt from gofile-dl GitHub: {e}")
        
    # 2. Try to fetch from gallery-dl repository on GitHub
    try:
        url = "https://raw.githubusercontent.com/mikf/gallery-dl/master/gallery_dl/extractor/gofile.py"
        resp = requests.get(url, timeout=5, verify=False)
        if resp.status_code == 200:
            match = re.search(r'14400\)\}\s*::"\s*\n?\s*f?"([^"]+)"', resp.text)
            if match:
                salt = match.group(1).strip()
                if salt:
                    _cached_gofile_salt = salt
                    _gofile_salt_expiry = current_time + 14400 # 4 hours
                    logger.info(f"Dynamically resolved Gofile salt from gallery-dl: {salt}")
                    return salt
    except Exception as e:
        logger.warning(f"Failed to fetch Gofile salt from gallery-dl GitHub: {e}")
        
    # 3. Try to fetch from Gofile's wt.obf.js directly (using new URL js/wt.obf.js)
    try:
        url = "https://gofile.io/js/wt.obf.js"
        headers = {"User-Agent": USER_AGENT}
        resp = requests.get(url, headers=headers, timeout=5, verify=False)
        if resp.status_code == 200:
            matches = re.findall(r'"([a-zA-Z0-9]{10,20})"', resp.text)
            for m in matches:
                if any(c.isdigit() for c in m) and any(c.isalpha() for c in m):
                    _cached_gofile_salt = m
                    _gofile_salt_expiry = current_time + 14400
                    logger.info(f"Dynamically resolved Gofile salt from wt.obf.js: {m}")
                    return m
    except Exception as e:
        logger.warning(f"Failed to fetch Gofile salt from wt.obf.js: {e}")

    # Fall back to hardcoded salt
    _cached_gofile_salt = fallback_salt
    _gofile_salt_expiry = current_time + 600 # Try again in 10 minutes
    logger.info(f"Using fallback Gofile salt: {fallback_salt}")
    return fallback_salt

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def create_guest_account() -> str:
    url = "https://api.gofile.io/accounts"
    try:
        resp = requests.post(url, json={}, headers={"User-Agent": USER_AGENT}, timeout=15, verify=False)
        if resp.status_code == 429:
            raise Exception("Gofile istek limitine ulaşıldı (Rate Limit). IP koruması nedeniyle lütfen birkaç dakika bekleyin.")
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "ok":
            raise RuntimeError(f"Gofile hesabı oluşturulamadı: {data.get('status')}")
        return data["data"]["token"]
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 429:
            raise Exception("Gofile istek limitine ulaşıldı (Rate Limit). IP koruması nedeniyle lütfen birkaç dakika bekleyin.")
        raise

def get_gofile_token() -> str:
    global _cached_gofile_token
    with _gofile_token_lock:
        if _cached_gofile_token:
            return _cached_gofile_token
        token = create_guest_account()
        _cached_gofile_token = token
        logger.info(f"Created new Gofile guest account: {token}")
        return token

def generate_website_token(account_token: str, salt: str = None) -> str:
    if salt is None:
        salt = get_gofile_salt()
    from hashlib import sha256
    time_slot = int(time.time()) // 14400
    raw = f"{USER_AGENT}::en-US::{account_token}::{time_slot}::{salt}"
    return sha256(raw.encode()).hexdigest()

def get_folder_contents(folder_id: str, account_token: str, website_token: str) -> dict:
    url = f"https://api.gofile.io/contents/{folder_id}"
    headers = {
        "Authorization": f"Bearer {account_token}",
        "User-Agent": USER_AGENT,
        "Origin": "https://gofile.io",
        "Referer": f"https://gofile.io/d/{folder_id}",
        "X-Website-Token": website_token,
        "X-BL": "en-US",
    }
    params = {
        "contentFilter": "",
        "page": 1,
        "pageSize": 1000,
        "sortField": "createTime",
        "sortDirection": -1,
    }
    resp = requests.get(url, headers=headers, params=params, timeout=15, verify=False)
    if resp.status_code == 429:
        raise Exception("Gofile istek limitine ulaşıldı (Rate Limit). Lütfen birkaç dakika bekleyin.")
    resp.raise_for_status()
    return resp.json()

@app.route("/api/onlinefix/search", methods=["GET"])
def onlinefix_search():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"results": []})
    
    import urllib.parse
    from bs4 import BeautifulSoup
    
    try:
        try:
            encoded_term = urllib.parse.quote_plus(query.encode('windows-1251'))
        except UnicodeEncodeError:
            encoded_term = urllib.parse.quote_plus(query.encode('windows-1251', errors='replace'))

        url = f"https://online-fix.me/index.php?do=search&subaction=search&story={encoded_term}"
        headers = {"User-Agent": USER_AGENT}
        
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'windows-1251'
        soup = BeautifulSoup(response.text, "html.parser")
        
        news_items = soup.find_all(class_="news-search")
        if not news_items:
            news_items = soup.find_all(class_="news")
            
        results = []
        for item in news_items:
            title_el = item.find(class_="title")
            if title_el:
                title = title_el.get_text(strip=True)
                a = title_el.find_parent("a") or title_el.find("a")
                if not a:
                    a = item.find("a", href=lambda h: h and "/games/" in h)
                if a:
                    href = a["href"]
                    if href.startswith("/"):
                        href = "https://online-fix.me" + href
                    results.append({
                        "title": title,
                        "url": href
                    })
        return jsonify({"success": True, "results": results})
    except Exception as e:
        logger.error(f"OnlineFix search error: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)})

def find_game_install_dir(steam_path, appid):
    """Finds the local installation folder of a game using its AppID."""
    try:
        libraries = FileManager.get_library_folders(steam_path)
        for _, lib_path in libraries:
            acf_path = os.path.join(lib_path, "steamapps", f"appmanifest_{appid}.acf")
            if os.path.isfile(acf_path):
                with open(acf_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                parsed = VdfParser.parse(content)
                install_dir_name = parsed.get("AppState", {}).get("installdir")
                if install_dir_name:
                    game_dir = os.path.join(lib_path, "steamapps", "common", install_dir_name)
                    if os.path.isdir(game_dir):
                        return game_dir
    except Exception as e:
        logger.error(f"Error finding install dir for appid {appid}: {e}")
    return None

last_onlinefix_downloaded_file = None

def get_desktop_dir():
    desktop_dir = None
    if os.name == 'nt':
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders")
            path, _ = winreg.QueryValueEx(key, "Desktop")
            winreg.CloseKey(key)
            resolved = os.path.expandvars(path)
            if os.path.isdir(resolved):
                desktop_dir = resolved
        except Exception:
            pass

    if not desktop_dir:
        onedrive_desktop = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop")
        if os.path.isdir(onedrive_desktop):
            desktop_dir = onedrive_desktop
        else:
            desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
    return desktop_dir

def find_archiver_gui():
    """Finds WinRAR or 7-Zip GUI executable on the user's system."""
    if os.name == 'nt':
        import winreg
        # 1. Try WinRAR from App Paths
        for root_key in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
            try:
                key = winreg.OpenKey(root_key, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\WinRAR.exe")
                val, _ = winreg.QueryValueEx(key, "")
                winreg.CloseKey(key)
                if val and os.path.isfile(val):
                    return ("winrar", val)
            except Exception:
                pass

        # 2. Try 7-Zip from App Paths
        for root_key in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
            try:
                key = winreg.OpenKey(root_key, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\7zFM.exe")
                val, _ = winreg.QueryValueEx(key, "")
                winreg.CloseKey(key)
                if val and os.path.isfile(val):
                    return ("7zip", val)
            except Exception:
                pass

    winrar_paths = [
        r"C:\Program Files\WinRAR\WinRAR.exe",
        r"C:\Program Files (x86)\WinRAR\WinRAR.exe",
    ]
    for p in winrar_paths:
        if os.path.isfile(p):
            return ("winrar", p)

    sevenzip_paths = [
        r"C:\Program Files\7-Zip\7zFM.exe",
        r"C:\Program Files (x86)\7-Zip\7zFM.exe",
    ]
    for p in sevenzip_paths:
        if os.path.isfile(p):
            return ("7zip", p)

    import shutil
    resolved = shutil.which("winrar")
    if resolved and os.path.isfile(resolved):
        return ("winrar", resolved)
    resolved_7z = shutil.which("7zFM")
    if resolved_7z and os.path.isfile(resolved_7z):
        return ("7zip", resolved_7z)

    return (None, None)

def find_extractor():
    paths = [
        r"C:\Program Files\WinRAR\UnRAR.exe",
        r"C:\Program Files\WinRAR\WinRAR.exe",
        r"C:\Program Files\7-Zip\7z.exe",
        r"C:\Program Files (x86)\7-Zip\7z.exe",
    ]
    for p in paths:
        if os.path.isfile(p):
            return p
    # Fallback to PATH check
    import shutil
    for cmd in ["unrar", "7z"]:
        resolved = shutil.which(cmd)
        if resolved:
            return resolved
    return None

def extract_archive(archive_path, extract_dir, password="online-fix.me"):
    extractor = find_extractor()
    if not extractor:
        raise Exception("WinRAR veya 7-Zip sistemi üzerinde bulunamadı! Lütfen arşiv çıkarıcı bir program kurun.")
        
    os.makedirs(extract_dir, exist_ok=True)
    
    import subprocess
    cmd = []
    if "7z" in extractor.lower():
        cmd = [extractor, "x", f"-p{password}", "-y", f"-o{extract_dir}", archive_path]
    else:  # WinRAR or UnRAR
        cmd = [extractor, "x", f"-p{password}", "-y", archive_path, extract_dir + os.sep]
        
    logger.info(f"Running archive extraction command: {cmd}")
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    
    if res.returncode != 0:
        logger.error(f"Extraction failed: {res.stderr}\nStdout: {res.stdout}")
        raise Exception(f"Arşiv dosyası açılamadı (Şifre yanlış olabilir veya dosya bozuk). Hata Kodu: {res.returncode}")
    return True

def copy_and_overwrite(source_dir, dest_dir):
    """Copies all files/folders from source_dir to dest_dir, overwriting existing files."""
    import shutil
    src_root = source_dir
    for root, dirs, files in os.walk(src_root):
        rel_path = os.path.relpath(root, src_root)
        target_root = dest_dir if rel_path == "." else os.path.join(dest_dir, rel_path)
        os.makedirs(target_root, exist_ok=True)
        
        for file in files:
            src_file = os.path.join(root, file)
            dest_file = os.path.join(target_root, file)
            try:
                # Remove read-only permissions if present to prevent permission error
                if os.path.isfile(dest_file):
                    os.chmod(dest_file, 0o777)
                shutil.copy2(src_file, dest_file)
            except Exception as e:
                logger.warning(f"Could not copy {file} to {dest_file}: {e}")

def onlinefix_download_worker(task_id: str, detail_url: str, mode="desktop", appid=None):
    global onlinefix_download_statuses
    from bs4 import BeautifulSoup
    import json
    import tempfile
    
    gofile_folder_url = None
    
    def update_status(msg: str, progress: int, status="running", file_name=None, speed="", bytes_downloaded=0, total_bytes=0, file_path=None):
        with onlinefix_lock:
            curr = onlinefix_download_statuses.get(task_id, {})
            onlinefix_download_statuses[task_id] = {
                "status": status,
                "message": msg,
                "progress": progress,
                "file_name": file_name or curr.get("file_name"),
                "file_path": file_path or curr.get("file_path"),
                "speed": speed,
                "bytes_downloaded": bytes_downloaded,
                "total_bytes": total_bytes,
                "gofile_url": gofile_folder_url or curr.get("gofile_url"),
                "detail_url": detail_url
            }
        logger.info(f"[OnlineFix Download {task_id}] {msg} ({progress}%)")
    try:
        # Pre-validate game folder existence early if in integration mode
        if mode == "integrate":
            if not appid:
                raise Exception("Entegrasyon için AppID belirtilmedi.")
            game_dir = find_game_install_dir(config.steam_path, appid)
            if not game_dir or not os.path.isdir(game_dir):
                raise Exception("Oyun bilgisayarınızda yüklü bulunamadı. Lütfen önce oyunu kurun.")

        # 1. Fetch details page
        update_status("Oyun detayları çözümleniyor...", 10)
        headers = {"User-Agent": USER_AGENT}
        res = requests.get(detail_url, headers=headers, timeout=15)
        res.encoding = 'windows-1251'
        soup = BeautifulSoup(res.text, "html.parser")
        
        hosters_url = None
        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = a.get_text(strip=True)
            if "hosters" in href or "hosters" in text.lower():
                hosters_url = href
                break
                
        if not hosters_url:
            raise Exception("Bu oyun için Online-Fix sayfasında indirme bağlantısı / buton bulunamadı.")
            
        # 2. Fetch hosters page
        update_status("İndirme paneli çözümleniyor...", 25)
        hosters_headers = {
            "User-Agent": USER_AGENT,
            "Referer": "https://online-fix.me/"
        }
        res_hosters = requests.get(hosters_url, headers=hosters_headers, timeout=15)
        soup_hosters = BeautifulSoup(res_hosters.text, "html.parser")
        
        # 3. Parse available hosters and download links
        update_status("İndirme bağlantıları taranıyor...", 35)
        parsed_hosters = {}
        for el in soup_hosters.find_all(attrs={"data-links": True}):
            hname = el.get_text(strip=True).lower()
            try:
                parsed_hosters[hname] = json.loads(el["data-links"])
            except Exception:
                pass
                
        if not parsed_hosters:
            raise Exception("Bu oyun için hiçbir indirme sunucusu bağlantısı bulunamadı.")
            
        # Preference priority: Pixeldrain (fastest direct API), Gofile, FileDitch
        preferred_order = ["pixeldrain", "gofile", "fileditch"]
        # Also include any other available hosters
        for h in parsed_hosters:
            if h not in preferred_order:
                preferred_order.append(h)
                
        direct_download_url = None
        dl_headers = {"User-Agent": USER_AGENT}
        filename = None
        gofile_folder_url = None
        
        # Helper to pick target fix file from link list
        def pick_target_file(files_list):
            for finfo in files_list:
                fname = finfo.get("file_name", "")
                fn_lower = fname.lower()
                if (fn_lower.endswith(".rar") or fn_lower.endswith(".zip")) and ("fix" in fn_lower or "repair" in fn_lower):
                    return finfo
            return files_list[0] if files_list else None
            
        # Try hosters in preference order
        for hoster_name in preferred_order:
            if hoster_name not in parsed_hosters:
                continue
            files = parsed_hosters[hoster_name]
            fmatch = pick_target_file(files)
            if not fmatch:
                continue
                
            raw_link = fmatch.get("direct_link", "")
            raw_filename = fmatch.get("file_name", "")
            
            # --- HOST: PIXELDRAIN ---
            if "pixeldrain" in hoster_name or "pixeldrain.com" in raw_link:
                try:
                    update_status("Pixeldrain indirme sunucusu hazırlanıyor...", 45)
                    # Extract file id from URL (e.g. https://pixeldrain.com/u/kaJrZNZE)
                    fid = raw_link.split("/u/")[-1].strip()
                    api_dl = f"https://pixeldrain.com/api/file/{fid}"
                    # Test head / stream
                    test_r = requests.head(api_dl, headers={"User-Agent": USER_AGENT}, timeout=10)
                    if test_r.status_code == 200:
                        direct_download_url = api_dl
                        filename = raw_filename or f"Fix_Repair_Steam_Generic.rar"
                        dl_headers = {"User-Agent": USER_AGENT}
                        logger.info(f"Selected Pixeldrain download: {direct_download_url} ({filename})")
                        break
                except Exception as p_ex:
                    logger.warning(f"Pixeldrain probe failed: {p_ex}")

            # --- HOST: GOFILE ---
            elif "gofile" in hoster_name or "gofile.io" in raw_link:
                try:
                    update_status("Gofile indirme sunucusu çözümleniyor...", 45)
                    gofile_folder_url = raw_link
                    m = re.search(r'/d/([a-zA-Z0-9]+)', gofile_folder_url)
                    if not m:
                        continue
                    folder_id = m.group(1)
                    
                    global _cached_gofile_token
                    guest_token = get_gofile_token()
                    web_token = generate_website_token(guest_token)
                    
                    contents = get_folder_contents(folder_id, guest_token, web_token)
                    if contents.get("status") != "ok":
                        _cached_gofile_token = None
                        guest_token = get_gofile_token()
                        web_token = generate_website_token(guest_token)
                        contents = get_folder_contents(folder_id, guest_token, web_token)
                        
                    if contents.get("status") == "ok":
                        children = contents.get("data", {}).get("children", {})
                        g_url = None
                        for child_id, info in children.items():
                            if info.get("name") == raw_filename:
                                g_url = info.get("link")
                                break
                        if not g_url:
                            for child_id, info in children.items():
                                child_name = info.get("name", "")
                                cn_lower = child_name.lower()
                                if (cn_lower.endswith(".rar") or cn_lower.endswith(".zip")) and ("fix" in cn_lower or "repair" in cn_lower):
                                    g_url = info.get("link")
                                    raw_filename = child_name
                                    break
                        if not g_url and children:
                            first_child = list(children.values())[0]
                            g_url = first_child.get("link")
                            raw_filename = first_child.get("name")
                            
                        if g_url:
                            direct_download_url = g_url
                            filename = raw_filename
                            dl_headers = {
                                "User-Agent": USER_AGENT,
                                "Referer": "https://gofile.io/",
                                "Cookie": f"accountToken={guest_token}"
                            }
                            logger.info(f"Selected Gofile download: {direct_download_url} ({filename})")
                            break
                except Exception as g_ex:
                    logger.warning(f"Gofile probe failed: {g_ex}")
                    
            # --- HOST: FILEDITCH ---
            elif "fileditch" in hoster_name or "fileditchfiles" in raw_link:
                try:
                    update_status("FileDitch indirme sunucusu hazırlanıyor...", 45)
                    test_r = requests.head(raw_link, headers={"User-Agent": USER_AGENT}, timeout=10)
                    if test_r.status_code == 200:
                        direct_download_url = raw_link
                        filename = raw_filename or f"Fix_Repair_Steam_Generic.rar"
                        dl_headers = {"User-Agent": USER_AGENT}
                        logger.info(f"Selected FileDitch download: {direct_download_url} ({filename})")
                        break
                except Exception as fd_ex:
                    logger.warning(f"FileDitch probe failed: {fd_ex}")

        if not direct_download_url or not filename:
            raise Exception("İndirme bağlantısı çözümlenemedi (Mevcut indirme sunucuları yanıt vermiyor veya dosya silinmiş).")
            
        # 6. Determine Download Path based on mode
        download_dir = None
        if mode == "integrate":
            download_dir = tempfile.gettempdir()
        else:
            # Desktop Path resolution
            if os.name == 'nt':
                try:
                    import winreg
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders")
                    path, _ = winreg.QueryValueEx(key, "Desktop")
                    winreg.CloseKey(key)
                    resolved = os.path.expandvars(path)
                    if os.path.isdir(resolved):
                        download_dir = resolved
                except Exception:
                    pass

            if not download_dir:
                onedrive_desktop = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop")
                if os.path.isdir(onedrive_desktop):
                    download_dir = onedrive_desktop
                else:
                    download_dir = os.path.join(os.path.expanduser("~"), "Desktop")
                    
        dest_path = os.path.join(download_dir, filename)
        update_status("İndirme başlatılıyor...", 65, file_name=filename)
        
        r = requests.get(direct_download_url, headers=dl_headers, stream=True, timeout=30, verify=False)
        r.raise_for_status()
        total_size = int(r.headers.get('content-length', 0))
        
        downloaded = 0
        start_time = time.time()
        last_update_time = start_time
        
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=65536):
                # Check for cancellation
                with onlinefix_cancel_lock:
                    if task_id in onlinefix_cancelled_tasks:
                        r.close()
                        f.close()
                        try:
                            os.remove(dest_path)
                        except Exception:
                            pass
                        onlinefix_cancelled_tasks.remove(task_id)
                        update_status("İndirme kullanıcı tarafından iptal edildi.", 0, status="failed")
                        return
 
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    current_time = time.time()
                    if current_time - last_update_time >= 0.5:
                        elapsed = current_time - start_time
                        speed_val = downloaded / max(0.01, elapsed)
                        if speed_val > 1024 * 1024:
                            speed_str = f"{speed_val / (1024 * 1024):.2f} MB/s"
                        else:
                            speed_str = f"{speed_val / 1024:.2f} KB/s"
                            
                        progress_pct = 65 + int((downloaded / max(1, total_size)) * 25) # Download portion goes up to 90%
                        progress_pct = min(89, progress_pct)
                        
                        update_status(
                            "Dosya indiriliyor..." if mode == "integrate" else "Masaüstüne indiriliyor...",
                            progress_pct,
                            file_name=filename,
                            speed=speed_str,
                            bytes_downloaded=downloaded,
                            total_bytes=total_size
                        )
                        last_update_time = current_time
                        
        if mode == "integrate":
            update_status("Arşiv açılıyor (online-fix.me)...", 90, file_name=filename)
            extract_dir = os.path.join(tempfile.gettempdir(), f"onlinefix_extract_{task_id}")
            
            try:
                # Extract archive
                extract_archive(dest_path, extract_dir, password="online-fix.me")
                
                # Copy to game directory
                update_status("Dosyalar oyuna entegre ediliyor...", 95, file_name=filename)
                game_dir = find_game_install_dir(config.steam_path, appid)
                copy_and_overwrite(extract_dir, game_dir)
                
                # Cleanup temp files
                update_status("Geçici dosyalar temizleniyor...", 99, file_name=filename)
                try:
                    if os.path.isfile(dest_path):
                        os.remove(dest_path)
                    if os.path.isdir(extract_dir):
                        shutil.rmtree(extract_dir)
                except Exception as ex:
                    logger.warning(f"Cleanup warning: {ex}")
                    
                update_status(
                    "Çok oyunculu yama oyuna başarıyla entegre edildi!",
                    100,
                    status="success",
                    file_name=filename,
                    total_bytes=total_size,
                    bytes_downloaded=total_size
                )
            except Exception as extract_ex:
                # Cleanup if failed
                try:
                    if os.path.isfile(dest_path):
                        os.remove(dest_path)
                    if os.path.isdir(extract_dir):
                        shutil.rmtree(extract_dir)
                except Exception:
                    pass
                raise extract_ex
        else:
            global last_onlinefix_downloaded_file
            last_onlinefix_downloaded_file = dest_path
            update_status(
                "İndirme başarıyla tamamlandı! Dosya Masaüstünüze kaydedildi.",
                100,
                status="success",
                file_name=filename,
                file_path=dest_path,
                total_bytes=total_size,
                bytes_downloaded=total_size
            )
        
    except Exception as e:
        logger.error(f"Error in onlinefix_download_worker: {e}", exc_info=True)
        err_msg = str(e)
        if "401" in err_msg or "unauthorized" in err_msg.lower():
            user_msg = "Gofile güvenlik doğrulaması başarısız oldu (Oturum reddedildi). Lütfen birkaç dakika sonra tekrar deneyin."
        elif "429" in err_msg or "too many requests" in err_msg.lower() or "rate" in err_msg.lower():
            user_msg = "Gofile istek sınırına ulaşıldı (Rate Limit). IP koruması nedeniyle indirme geçici olarak bekletiliyor. Lütfen 5-10 dakika sonra tekrar deneyin."
        elif "timeout" in err_msg.lower() or "timed out" in err_msg.lower():
            user_msg = "Gofile sunucusuna bağlanırken zaman aşımı oluştu. İnternet bağlantınızı kontrol edip tekrar deneyin."
        elif "max retries" in err_msg.lower():
            user_msg = "Gofile sunucusu yanıt vermiyor veya istekleri geçici olarak engelliyor."
        else:
            user_msg = err_msg
        update_status(user_msg, 100, status="failed")

@app.route("/api/onlinefix/download", methods=["POST"])
def onlinefix_download():
    data = request.json or {}
    url = data.get("url", "").strip()
    mode = data.get("mode", "desktop").strip()
    appid = data.get("appid", "").strip()
    
    if not url:
        return jsonify({"success": False, "error": "URL is required"})
        
    import uuid
    task_id = str(uuid.uuid4())
    
    with onlinefix_lock:
        onlinefix_download_statuses[task_id] = {
            "status": "running",
            "message": "Initializing download task...",
            "progress": 0,
            "file_name": None,
            "speed": "",
            "bytes_downloaded": 0,
            "total_bytes": 0
        }
        
    thread = threading.Thread(target=onlinefix_download_worker, args=(task_id, url, mode, appid), daemon=True)
    thread.start()
    return jsonify({"success": True, "task_id": task_id})

@app.route("/api/onlinefix/status", methods=["GET"])
def onlinefix_status():
    task_id = request.args.get("task_id", "").strip()
    if not task_id:
        return jsonify({"status": "idle"})
        
    with onlinefix_lock:
        status_info = onlinefix_download_statuses.get(task_id, {"status": "idle"})
        res_info = dict(status_info)
        # If terminal state, keep in memory for 30 seconds before cleanup so client never misses it
        now = time.time()
        if status_info.get("status") in ["success", "failed"]:
            if "_finished_at" not in status_info:
                status_info["_finished_at"] = now
            elif now - status_info["_finished_at"] > 30:
                del onlinefix_download_statuses[task_id]
        return jsonify(res_info)

@app.route("/api/onlinefix/cancel", methods=["POST"])
def onlinefix_cancel():
    data = request.json or {}
    task_id = data.get("task_id", "").strip()
    if not task_id:
        return jsonify({"success": False, "error": "Task ID is required"})
        
    with onlinefix_cancel_lock:
        onlinefix_cancelled_tasks.add(task_id)
        
    return jsonify({"success": True})

@app.route("/api/onlinefix/open_desktop", methods=["POST"])
def onlinefix_open_desktop():
    global last_onlinefix_downloaded_file
    try:
        data = request.json or {}
        task_id = data.get("task_id")
        
        file_path = None
        if task_id and task_id in onlinefix_download_statuses:
            file_path = onlinefix_download_statuses[task_id].get("file_path")
        if not file_path or not os.path.isfile(file_path):
            file_path = last_onlinefix_downloaded_file

        desktop_dir = get_desktop_dir()

        # If downloaded archive file exists, open with WinRAR GUI directly (NO CMD WINDOW, NO AUTO-EXTRACTION)
        if file_path and os.path.isfile(file_path):
            try:
                arch_type, arch_gui = find_archiver_gui()
                flags = 0x08000000 | 0x00000008 if os.name == 'nt' else 0  # CREATE_NO_WINDOW | DETACHED_PROCESS
                if arch_type == "winrar":
                    subprocess.Popen([arch_gui, "-ponline-fix.me", file_path], creationflags=flags)
                    return jsonify({"success": True, "file": file_path})
                elif arch_type == "7zip":
                    subprocess.Popen([arch_gui, file_path], creationflags=flags)
                    return jsonify({"success": True, "file": file_path})
                else:
                    # If neither WinRAR nor 7-Zip detected, launch the file via native Windows Shell
                    os.startfile(file_path)
                    return jsonify({"success": True, "file": file_path})
            except Exception as e:
                logger.error(f"Error opening archive: {e}", exc_info=True)
                try:
                    os.startfile(file_path)
                    return jsonify({"success": True, "file": file_path})
                except Exception:
                    pass

        if desktop_dir and os.path.exists(desktop_dir):
            if os.name == 'nt':
                os.startfile(desktop_dir)
            else:
                subprocess.Popen(['explorer' if sys.platform == 'win32' else 'xdg-open', desktop_dir])
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Desktop directory not found"})
    except Exception as e:
        logger.error(f"Error opening desktop folder: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/open_browser", methods=["POST"])
def api_open_browser():
    data = request.json or {}
    url = data.get("url", "").strip()
    if url:
        import webbrowser
        try:
            webbrowser.open(url)
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)})
    return jsonify({"success": False, "error": "URL is required"})

@app.route("/api/add_exclusion", methods=["POST"])
def api_add_exclusion():
    if os.name != 'nt':
        return jsonify({"success": False, "error": "Sadece Windows sistemlerde desteklenir."})
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        local_app_dir = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "steamtools-auto")
        steam_dir = config.steam_path

        paths = [current_dir]
        if os.path.isdir(local_app_dir):
            paths.append(local_app_dir)
        if steam_dir and os.path.isdir(steam_dir):
            paths.append(steam_dir)

        path_args = ",".join([f"'{p}'" for p in set(paths)])
        ps_cmd = f"Add-MpPreference -ExclusionPath {path_args} -ExclusionProcess 'SteaMRogue.exe','SteamTools_Auto_Backend.exe'"
        elevate_cmd = f"Start-Process powershell -Verb RunAs -ArgumentList '-WindowStyle Hidden -NoProfile -Command {ps_cmd}'"
        
        subprocess.run(["powershell", "-WindowStyle", "Hidden", "-NoProfile", "-Command", elevate_cmd], creationflags=0x08000000)
        return jsonify({"success": True, "message": "Windows Defender dışlama isteği gönderildi."})
    except Exception as e:
        logger.error(f"Error adding exclusion: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)})

def get_all_steam_libraries():
    """Tüm sürücülerdeki (C:, D:, E: vb.) Steam kütüphane klasörlerini keşfeder."""
    libraries = []
    steam_path = getattr(config, 'steam_path', '')
    if steam_path and os.path.isdir(steam_path):
        libraries.append(os.path.normpath(steam_path))

    if steam_path:
        vdf_path = os.path.join(steam_path, 'steamapps', 'libraryfolders.vdf')
        if os.path.exists(vdf_path):
            try:
                with open(vdf_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                for match in re.finditer(r'"path"\s+"([^"]+)"', content, re.IGNORECASE):
                    p = match.group(1).replace('\\\\', '\\')
                    p = os.path.normpath(p)
                    if os.path.isdir(p) and p not in libraries:
                        libraries.append(p)
            except Exception as e:
                logger.error(f"[get_all_steam_libraries] VDF okuma hatası: {e}")

    # C'den Z'ye tüm bağlı diskleri tara
    for drive in 'CDEFGHIJKLMNOPQRSTUVWXYZ':
        d = f'{drive}:\\'
        if os.path.exists(d):
            candidates = [
                os.path.join(d, 'SteamLibrary'),
                os.path.join(d, 'Steam'),
                os.path.join(d, 'Program Files (x86)', 'Steam'),
                os.path.join(d, 'Program Files', 'Steam'),
                os.path.join(d, 'Games', 'SteamLibrary')
            ]
            for c in candidates:
                c_norm = os.path.normpath(c)
                if os.path.isdir(c_norm) and c_norm not in libraries:
                    if os.path.isdir(os.path.join(c_norm, 'steamapps', 'common')):
                        libraries.append(c_norm)

    return libraries

def get_best_common_folder():
    """Taranan kütüphanelerden en uygun steamapps/common klasörünü döndürür."""
    libs = get_all_steam_libraries()
    for lib in libs:
        common = os.path.join(lib, 'steamapps', 'common')
        if os.path.isdir(common):
            return common
    return r"C:\Program Files (x86)\Steam\steamapps\common"

def find_game_folder_auto(appid, game_name=""):
    """
    Oyunun kurulu olduğu klasörü Steam kütüphanelerinde (manifest ve klasör adı ile) hassas şekilde arar.
    Yanlış klasör seçilmemesi için sıkı doğrulama yapar.
    """
    appid = str(appid).strip()
    libraries = get_all_steam_libraries()

    # 1. Aşama: Kesin doğruluk için appmanifest_<appid>.acf kontrolü
    if appid:
        for lib in libraries:
            steamapps = os.path.join(lib, 'steamapps')
            manifest_file = os.path.join(steamapps, f'appmanifest_{appid}.acf')
            if os.path.isfile(manifest_file):
                try:
                    with open(manifest_file, 'r', encoding='utf-8', errors='ignore') as f:
                        m_content = f.read()
                    m = re.search(r'"installdir"\s+"([^"]+)"', m_content, re.IGNORECASE)
                    if m:
                        installdir_name = m.group(1).strip()
                        full_path = os.path.join(steamapps, 'common', installdir_name)
                        if os.path.isdir(full_path) and os.listdir(full_path):
                            logger.info(f"[find_game_folder_auto] Oyun appmanifest üzerinden bulundu: {full_path}")
                            return full_path
                except Exception as e:
                    logger.error(f"[find_game_folder_auto] Manifest okuma hatası ({manifest_file}): {e}")

    # 2. Aşama: steamapps/common altındaki klasör isimleri ile eşleştirme
    if game_name:
        clean_name = re.sub(r'[:\*\?\"<>\|™®♥]', '', game_name).strip().lower()
        clean_name = re.sub(r'\s*-\s*bypass.*', '', clean_name).strip()
        clean_name = re.sub(r'\s*-\s*zen mode.*', '', clean_name).strip()

        for lib in libraries:
            common_dir = os.path.join(lib, 'steamapps', 'common')
            if not os.path.isdir(common_dir):
                continue
            try:
                for item in os.listdir(common_dir):
                    item_path = os.path.join(common_dir, item)
                    if not os.path.isdir(item_path):
                        continue
                    item_clean = re.sub(r'[:\*\?\"<>\|™®♥]', '', item).strip().lower()

                    # Birebir isim eşleşmesi veya yüksek benzerlik kontrolü (yanlış yere atmayı önlemek için)
                    if clean_name and len(clean_name) >= 4:
                        if clean_name == item_clean:
                            if os.listdir(item_path):
                                logger.info(f"[find_game_folder_auto] Oyun klasör adı tam eşleşti: {item_path}")
                                return item_path
                        elif (clean_name in item_clean and len(clean_name) / max(1, len(item_clean)) > 0.6) or \
                             (item_clean in clean_name and len(item_clean) / max(1, len(clean_name)) > 0.6):
                            if os.listdir(item_path):
                                logger.info(f"[find_game_folder_auto] Oyun klasör adı yakın eşleşti: {item_path}")
                                return item_path
            except Exception as e:
                logger.error(f"[find_game_folder_auto] Common klasörü taranırken hata: {e}")

    return None

# ---- BYPASS: Oyun Klasörünü Otomatik Bul ----
@app.route("/api/find_game_folder", methods=["POST"])
def api_find_game_folder():
    """Tüm diskleri ve kütüphaneleri tarayarak oyunun kurulu olduğu klasörü otomatik bulur."""
    try:
        data = request.json or {}
        appid = str(data.get("appid", "")).strip()
        game_name = str(data.get("name", "")).strip()

        path = find_game_folder_auto(appid, game_name)
        default_common = get_best_common_folder()

        if path:
            return jsonify({
                "ok": True,
                "path": path,
                "default_common": os.path.dirname(path)
            })
        else:
            return jsonify({
                "ok": False,
                "path": None,
                "default_common": default_common,
                "message": "Oyun kurulu bulunamadı veya Steam kütüphanelerinde tespit edilemedi."
            })
    except Exception as e:
        logger.error(f"[api_find_game_folder] Error: {e}", exc_info=True)
        return jsonify({"ok": False, "path": None, "default_common": get_best_common_folder(), "error": str(e)})

# ---- BYPASS: Klasör Seç ----
@app.route("/api/select_folder", methods=["POST"])
def api_select_folder():
    """Tkinter ile klasör seçim dialogu açar, seçilen yolu döndürür."""
    try:
        data = request.json or {}
        title = request.args.get("title") or data.get("title") or "Oyun klasörünü seç"
        initialdir = request.args.get("initialdir") or data.get("initialdir")

        if not initialdir or not os.path.isdir(initialdir):
            initialdir = get_best_common_folder()

        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.wm_attributes("-topmost", True)
        selected = filedialog.askdirectory(title=title, parent=root, initialdir=initialdir)
        root.destroy()
        if selected:
            return jsonify({"ok": True, "path": selected})
        return jsonify({"ok": False, "path": None})
    except Exception as e:
        logger.error(f"[select_folder] Error: {e}", exc_info=True)
        return jsonify({"ok": False, "path": None, "error": str(e)})

def get_7z_binary():
    """Finds 7z.exe from bundled or standard locations."""
    candidates = [
        getattr(sys, '_MEIPASS', None) and os.path.join(sys._MEIPASS, '7z.exe'),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '7z.exe'),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '7z.exe'),
        r"C:\Users\mytho\AppData\Roaming\ProjectLightningV5\resources\binaries\win\7z.exe",
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "steamtools-auto", "resources", "7z.exe"),
        r"C:\Program Files\7-Zip\7z.exe",
        r"C:\Program Files (x86)\7-Zip\7z.exe"
    ]
    for c in candidates:
        if c and os.path.isfile(c):
            return c
    return None

def fetch_nexus_fix_files(appid):
    """Queries Cloudflare Nexus API mirrors for fix files."""
    import urllib.request
    import urllib.parse
    import json

    mirrors = [
        'https://nexus-images.pages.dev/api',
        'https://nexus-images-2.pages.dev/api',
        'https://nexus-worker-mirror.pages.dev/api',
        'https://nexus-worker-mirror.pages.dev'
    ]

    for base_url in mirrors:
        try:
            sep = '&' if '?' in base_url else '?'
            req_url = f"{base_url}{sep}appid={appid}&type=fix"
            req = urllib.request.Request(req_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req, timeout=12) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode('utf-8'))
                    if data.get('success') and data.get('files'):
                        return data.get('files')
        except Exception as e:
            logger.warning(f"[fetch_nexus_fix_files] Failed for {base_url}: {e}")
            continue
    return None

# ---- BYPASS: Fix Uygula ----
@app.route("/api/apply_fix", methods=["POST"])
def api_apply_fix():
    """
    Nexus API üzerinden fix dosyalarını çeker, indirir ve 7-Zip ile hedef klasöre çıkartır.
    """
    import zipfile, shutil, tempfile, urllib.request, subprocess
    data = request.json or {}
    appid = str(data.get("appid", "")).strip()
    dest_dir = data.get("dest_dir", "").strip()
    game = data.get("game", {})

    if not appid:
        return jsonify({"ok": False, "message": "AppID eksik."})
    if not dest_dir or not os.path.isdir(dest_dir):
        return jsonify({"ok": False, "message": "Geçersiz hedef klasör."})

    logger.info(f"[apply_fix] Starting fix application for appid: {appid} -> {dest_dir}")

    # 1. Cloudflare Nexus API'den fix dosyalarını sorgula
    files = fetch_nexus_fix_files(appid)

    # 2. Eğer Nexus API dosya döndürmediyse fallback kontrolleri yap
    if not files:
        fix_url = game.get("fix_url") or game.get("download_url") or game.get("url")
        web_url = game.get("web_url") or game.get("link")

        if web_url and not fix_url:
            try:
                import webbrowser
                webbrowser.open(web_url)
                return jsonify({"ok": True, "message": "Rehber tarayıcıda açıldı.", "method": "browser"})
            except Exception as e:
                return jsonify({"ok": False, "message": f"Tarayıcı açılamadı: {e}"})

        if not fix_url:
            return jsonify({
                "ok": False,
                "message": "Bu oyun için henüz otomatik fix sunucularda hazır değil veya eklenme aşamasında.",
                "reason": "no_files"
            })

        # Tekil fix_url varsa dosyalar listesine dönüştür
        filename = fix_url.split("/")[-1].split("?")[0] or "fix.zip"
        files = [{"name": filename, "download_url": fix_url}]

    # 3. Dosyaları geçici klasöre indir
    temp_dir = tempfile.mkdtemp(prefix=f"bypass_{appid}_")
    downloaded_paths = []
    try:
        for item in files:
            fname = item.get("name")
            durl = item.get("download_url")
            if not fname or not durl:
                continue

            target_local = os.path.join(temp_dir, fname)
            logger.info(f"[apply_fix] Downloading {fname} from {durl}...")

            req = urllib.request.Request(durl, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req, timeout=300) as resp, open(target_local, 'wb') as out_f:
                shutil.copyfileobj(resp, out_f)

            downloaded_paths.append(target_local)

        if not downloaded_paths:
            return jsonify({"ok": False, "message": "Fix dosyaları indirilemedi."})

        # 4. Ana arşivi seç (.zip, .7z, .rar, .001, .exe)
        # Çok parçalı zip'te (örn: .z01 ve .zip) .zip ana dosyadır!
        archive_candidates = []
        for p in downloaded_paths:
            ext = os.path.splitext(p)[1].lower()
            if ext == '.zip':
                archive_candidates.append((10, p))
            elif ext == '.7z':
                archive_candidates.append((9, p))
            elif ext == '.rar':
                archive_candidates.append((8, p))
            elif ext == '.001':
                archive_candidates.append((7, p))
            elif ext == '.exe':
                archive_candidates.append((5, p))

        seven_zip = get_7z_binary()

        if archive_candidates and seven_zip:
            archive_candidates.sort(key=lambda x: x[0], reverse=True)
            main_archive = archive_candidates[0][1]
            logger.info(f"[apply_fix] Extracting {main_archive} using 7z to {dest_dir}")
            
            cmd = [seven_zip, 'x', main_archive, f'-o{dest_dir}', '-y', '-aoa', '-mmt=on']
            flags = 0x08000000 if os.name == 'nt' else 0
            proc = subprocess.run(cmd, creationflags=flags, capture_output=True, text=True)
            if proc.returncode not in (0, 1):
                raise RuntimeError(f"7z extraction failed with code {proc.returncode}: {proc.stderr}")

        elif archive_candidates and not seven_zip:
            # Fallback to python zipfile if only zip
            archive_candidates.sort(key=lambda x: x[0], reverse=True)
            main_archive = archive_candidates[0][1]
            if main_archive.lower().endswith('.zip') and zipfile.is_zipfile(main_archive):
                logger.info(f"[apply_fix] Extracting {main_archive} using python zipfile to {dest_dir}")
                with zipfile.ZipFile(main_archive, 'r') as zf:
                    zf.extractall(dest_dir)
            else:
                raise RuntimeError("7-Zip aracı bulunamadı ve arşiv python ile açılamadı.")
        else:
            # Arşiv değilse dosyaları doğrudan hedef klasöre kopyala
            logger.info(f"[apply_fix] No archive found. Copying {len(downloaded_paths)} files directly to {dest_dir}")
            for p in downloaded_paths:
                dest_file = os.path.join(dest_dir, os.path.basename(p))
                shutil.copy2(p, dest_file)

        logger.info(f"[apply_fix] Successfully applied fix for {appid}")

        # Save applied fix to applied_fixes.json
        try:
            fixes_file = os.path.join(get_appdata_dir(), "applied_fixes.json")
            existing_fixes = []
            if os.path.isfile(fixes_file):
                with open(fixes_file, "r", encoding="utf-8") as f:
                    existing_fixes = json.load(f)
            existing_fixes = [x for x in existing_fixes if str(x.get("appid")) != str(appid)]
            existing_fixes.append({
                "appid": str(appid),
                "dest_dir": dest_dir,
                "game_name": game.get("name") or game.get("title") or f"AppID {appid}",
                "timestamp": time.time()
            })
            with open(fixes_file, "w", encoding="utf-8") as f:
                json.dump(existing_fixes, f, indent=2)
        except Exception as err:
            logger.warning(f"[apply_fix] Could not save applied fix tracking: {err}")

        return jsonify({"ok": True, "message": "Fix başarıyla uygulandı!"})

    except Exception as e:
        logger.error(f"[apply_fix] Error applying fix: {e}", exc_info=True)
        return jsonify({"ok": False, "message": f"Fix uygulama hatası: {str(e)}"})
    finally:
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass

# %%

def is_process_active(pid: int) -> bool:
    if os.name != 'nt':
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False
            
    import ctypes
    PROCESS_QUERY_INFORMATION = 0x0400
    STILL_ACTIVE = 259
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION, False, pid)
    if not handle:
        return False
    exit_code = ctypes.c_ulong()
    success = kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
    kernel32.CloseHandle(handle)
    return success and (exit_code.value == STILL_ACTIVE)

def parent_monitor_worker():
    try:
        parent_pid = os.getppid()
    except Exception:
        parent_pid = None
        
    if not parent_pid or parent_pid <= 1:
        logger.info("[Watcher] No valid parent PID found. Watchdog disabled.")
        return
        
    logger.info(f"[Watcher] Started monitoring parent process (PID: {parent_pid}).")
    while True:
        time.sleep(2)
        if not is_process_active(parent_pid):
            logger.info(f"[Watcher] Parent process {parent_pid} terminated. Exiting backend...")
            os._exit(0)

def start_server():
    """Starts the Flask server in a local port."""
    # Ensure SteamTools is installed automatically at startup (guaranteed setup)
    try:
        ensure_steamtools_installed_auto()
    except Exception as e:
        logger.warning(f"Initial SteamTools auto-check failed: {e}")

    # Start parent monitor thread
    monitor_thread = threading.Thread(target=parent_monitor_worker, daemon=True)
    monitor_thread.start()

    # Run startup component checks in background (repos + SteamTools)
    updater.run_startup_checks(config.manifest_repos, config.steam_path)
    
    app.run(host="127.0.0.1", port=65012, debug=False, use_reloader=False)


# %%
if __name__ == "__main__":
    setup_logger()
    logger.info("Starting SteamTools Auto Flask API Server...")
    start_server()
