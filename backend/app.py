# %% [markdown]
# # Web GUI Backend & Wrapper
# Starts a Flask server for API communications and serves static assets.
# Integrates with pywebview for a desktop application experience.

# %%
import os
import sys

# Critical fix for Windows PyInstaller windowed/GUI mode (console=False):
# In windowed mode, sys.stdout / sys.stderr have invalid file descriptors and cause
# OSError: [Errno 22] Invalid argument in click.echo / Flask show_server_banner
class SafeStream:
    def write(self, s):
        pass
    def flush(self):
        pass
    def isatty(self):
        return False
    def readable(self):
        return False
    def writable(self):
        return True
    def seekable(self):
        return False

try:
    if sys.stdout is None or not hasattr(sys.stdout, "write"):
        sys.stdout = SafeStream()
    else:
        sys.stdout.write("")
        sys.stdout.flush()
except Exception:
    sys.stdout = SafeStream()

try:
    if sys.stderr is None or not hasattr(sys.stderr, "write"):
        sys.stderr = SafeStream()
    else:
        sys.stderr.write("")
        sys.stderr.flush()
except Exception:
    sys.stderr = SafeStream()

try:
    import click
    def _safe_click_echo(message=None, file=None, nl=True, err=False, color=None):
        pass
    click.echo = _safe_click_echo
    click.secho = lambda message=None, **kwargs: None
except Exception:
    pass

try:
    import flask.cli
    flask.cli.show_server_banner = lambda *args, **kwargs: None
except Exception:
    pass

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
# Initialize Flask & Base Directory Resolution
if hasattr(sys, "_MEIPASS"):
    BASE_DIR = sys._MEIPASS
    web_dir = os.path.join(sys._MEIPASS, "web")
else:
    _file_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.isdir(os.path.join(_file_dir, "web")):
        BASE_DIR = _file_dir
    else:
        BASE_DIR = os.path.dirname(_file_dir)
    web_dir = os.path.join(BASE_DIR, "web")

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

APP_VERSION = "1.1.5"

# Global dictionary to track add/download task status
task_statuses: Dict[str, Dict[str, Any]] = {}
task_lock = threading.Lock()

# %%
# Health Check Endpoint
@app.route("/api/health")
@app.route("/api/status")
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

# %%
# API Endpoint: POST /api/check_components_now
# Synchronously checks and updates manifest repos, SteamTools, OnlineFix bypasses, and library manifests
@app.route("/api/check_components_now", methods=["POST"])
def check_components_now():
    data = request.json or {}
    force = bool(data.get("force", False))
    result = updater.run_full_update_now(config.manifest_repos, config.steam_path, force=force)
    return jsonify(result)



# Serving Static Assets
@app.route("/")
def index():
    return send_from_directory(web_dir, "index.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(web_dir, path)

@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

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
GENRES_CACHE_FILE = os.path.join(BASE_DIR, "app_genres_cache.json")
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
        dirty = False
        count = 0
        for appid in appids:
            if appid in genres_cache:
                continue
            try:
                details = SteamAPI.get_app_details(appid)
                if details and "genres" in details:
                    genre_names = [g["description"] for g in details["genres"]]
                    genres_cache[appid] = genre_names
                    dirty = True
                    count += 1
                    if count % 10 == 0:
                        try:
                            with open(GENRES_CACHE_FILE, "w", encoding="utf-8") as f:
                                json.dump(genres_cache, f, indent=4)
                        except Exception:
                            pass
                time.sleep(1.0)
            except Exception:
                pass
        if dirty:
            try:
                with open(GENRES_CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump(genres_cache, f, indent=4)
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
    
    names_cache = {}
    with _names_cache_lock:
        if os.path.exists(cache_path) and os.path.getsize(cache_path) > 0:
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    names_cache = json.load(f)
            except Exception:
                pass

    dirty = False
    for appid in appids:
        cached_val = names_cache.get(appid)
        if cached_val:
            if isinstance(cached_val, dict):
                if cached_val.get("resolved") or cached_val.get("name") != f"Steam App {appid}":
                    continue
            else:
                continue

        try:
            details = SteamAPI.get_app_details(appid)
            if details:
                name = details.get("name", f"Steam App {appid}")
                app_type = details.get("type", "game").lower()
                names_cache[appid] = {"name": name, "type": app_type, "resolved": True}
                dirty = True
                logger.info(f"Background resolved AppID {appid} -> {name} ({app_type})")
            else:
                names_cache[appid] = {"name": f"Steam App {appid}", "type": "game", "resolved": True}
                dirty = True
        except Exception as e:
            logger.warning(f"Error in background resolution for AppID {appid}: {e}")
            
        time.sleep(0.3)

    if dirty:
        with _names_cache_lock:
            current_cache = {}
            if os.path.exists(cache_path) and os.path.getsize(cache_path) > 0:
                try:
                    with open(cache_path, "r", encoding="utf-8") as f:
                        current_cache = json.load(f)
                except Exception:
                    pass
            current_cache.update(names_cache)
            save_cache_atomic(cache_path, current_cache)

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
_prefetch_lock = threading.Lock()
_prefetch_active = False

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
        local_path = os.path.join(BASE_DIR, "app_names_cache.json")
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
        blacklist_ids = {480, 228980, 250820, 1002, 211, 1113740, 228989, 228990}
        tool_keywords = ("steamworks", "redistributable", "sdk", "dedicated server", "tool", "development", "compiler", "beta", "steamvr", "common redist", "spacewar")

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
                        if name == f"Steam App {appid}" and not cached.get("resolved"):
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

        games_list = [
            g for g in games_dict.values()
            if (int(g.get("appid", 0)) if str(g.get("appid", "")).isdigit() else 0) not in blacklist_ids
            and str(g.get("appid", "")).strip() != "480"
            and "spacewar" not in str(g.get("name", "")).lower()
        ]
        _library_cache["data"] = games_list
        _library_cache["timestamp"] = time.time()

        # Background pre-fetch covers for library games with low-end CPU throttling
        def prefetch_library_covers(games):
            global _prefetch_active
            with _prefetch_lock:
                if _prefetch_active:
                    return
                _prefetch_active = True
            try:
                covers_dir = get_covers_cache_dir()
                processed = 0
                for g in games:
                    if processed >= 40:
                        break
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
                            processed += 1
                        time.sleep(0.08) # gentle pacing to prevent 100% CPU on low-spec systems
                    except Exception:
                        pass
            finally:
                with _prefetch_lock:
                    _prefetch_active = False

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
    steam_exe = validator.resolve_steam_exe(config.steam_path)
    if not steam_exe or not os.path.isfile(steam_exe):
        return jsonify({"success": False, "error": "steam.exe bulunamadı"})

    try:
        # 2. Terminate Steam processes cleanly if running
        if validator.is_steam_running():
            logger.info("Closing Steam and child processes for restart...")
            validator.kill_steam(config.steam_path)
            validator.wait_for_steam_exit(timeout=10.0)
            time.sleep(2.0)  # Critical for Windows OS to release named mutexes, IPC sockets & file handles

        # 3. Auto-repair LUA manifest pinning, sync depotcache manifests, sync ACFs & adapt signatures
        if config.steam_path and os.path.isdir(config.steam_path):
            FileManager.repair_stplugin_luas(config.steam_path)
            sync_depotcache_manifests(config.steam_path)
            ensure_all_unlocked_acfs(config.steam_path)
            validator.ensure_opensteamtool_signatures(config.steam_path)

        # 4. Launch Steam cleanly with interactive GUI
        started = validator.launch_steam(steam_exe)

        if started:
            logger.info("Restarted Steam client successfully with GUI.")
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
        return jsonify({
            "status": "INACTIVE",
            "installed": False,
            "dlls": [],
            "has_plugins": False,
            "steam_running": False,
            "hook_loaded": False
        })
    
    dlls = ["xinput1_4.dll", "OpenSteamTool.dll"]
    installed_dlls = []
    for dll in dlls:
        dll_path = os.path.join(config.steam_path, dll)
        if os.path.isfile(dll_path):
            installed_dlls.append(dll)
            
    st_plugin = os.path.join(config.steam_path, "config", "stplug-in")
    has_plugins = os.path.isdir(st_plugin) and len(os.listdir(st_plugin)) > 0 if os.path.isdir(st_plugin) else False
    
    # SteamTools is installed if OpenSteamTool.dll is present AND proxy dll (xinput1_4) is present
    has_ost = any(d.lower() == "opensteamtool.dll" for d in installed_dlls)
    has_proxy = any(d.lower() == "xinput1_4.dll" for d in installed_dlls)
    installed = has_ost and has_proxy

    steam_running = validator.is_steam_running()
    hook_loaded = False
    
    if steam_running and installed:
        try:
            output = subprocess.check_output('tasklist /m xinput1_4.dll /fo csv /nh', shell=True, encoding="utf-8", errors="ignore")
            if "steam.exe" in output.lower():
                hook_loaded = True
            else:
                output2 = subprocess.check_output('tasklist /m OpenSteamTool.dll /fo csv /nh', shell=True, encoding="utf-8", errors="ignore")
                if "steam.exe" in output2.lower():
                    hook_loaded = True
        except Exception:
            # If tasklist inspection is blocked or restricted, assume true since files are in place and steam is running
            hook_loaded = True
            
    return jsonify({
        "installed": installed,
        "dlls": installed_dlls,
        "has_plugins": has_plugins,
        "steam_running": steam_running,
        "hook_loaded": hook_loaded,
        "status": "ACTIVE" if installed else "INACTIVE"
    })

def get_bundled_steamtools_dir():
    """Returns the path to bundled steamtools_files if available."""
    candidates = []
    if getattr(sys, 'frozen', False):
        if hasattr(sys, '_MEIPASS'):
            candidates.append(os.path.join(sys._MEIPASS, "steamtools_files"))
        exe_dir = os.path.dirname(sys.executable)
        candidates.append(os.path.join(exe_dir, "steamtools_files"))
        candidates.append(os.path.join(exe_dir, "..", "steamtools_files"))
        candidates.append(os.path.join(exe_dir, "resources", "steamtools_files"))
    else:
        base_dir = BASE_DIR
        candidates.append(os.path.join(base_dir, "steamtools_files"))
    
    local_st = os.path.join(BASE_DIR, "steamtools_files")
    candidates.append(local_st)
    
    for c in candidates:
        if os.path.isdir(c) and os.path.isfile(os.path.join(c, "OpenSteamTool.dll")):
            return c
    for c in candidates:
        if os.path.isdir(c):
            return c
    return None

def check_steamtools_installed():
    """Checks if SteamTools hook DLLs are present in Steam directory."""
    if not config.steam_path or not os.path.isdir(config.steam_path):
        return False, []
    present = []
    try:
        for f in os.listdir(config.steam_path):
            if f.lower() in ["xinput1_4.dll", "opensteamtool.dll"]:
                present.append(f)
    except Exception:
        return False, []
    has_ost = any(f.lower() == "opensteamtool.dll" for f in present)
    has_proxy = any(f.lower() == "xinput1_4.dll" for f in present)
    is_installed = has_ost and has_proxy
    return is_installed, present

def ensure_steamtools_installed_auto():
    """Guaranteed auto-install on startup/initial run."""
    try:
        if not config.steam_path or not os.path.isdir(config.steam_path):
            return False
        # Always ensure depotcache manifests are synced between config/depotcache and depotcache
        try:
            sync_depotcache_manifests(config.steam_path)
        except Exception:
            pass

        is_installed, present = check_steamtools_installed()
        if is_installed:
            logger.info("[SteamTools Auto-Setup] SteamTools is already installed and verified.")
            validator.ensure_opensteamtool_signatures(config.steam_path)
            return True

        st_dir = get_bundled_steamtools_dir()
        import shutil
        target_files = ["xinput1_4.dll", "OpenSteamTool.dll"]
        installed_count = 0
        
        # Always remove dwmapi.dll to prevent VGUI_Setup failed crash
        dwmapi_bad = os.path.join(config.steam_path, "dwmapi.dll")
        if os.path.isfile(dwmapi_bad):
            try:
                os.remove(dwmapi_bad)
            except Exception:
                pass

        if st_dir:
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
            
            # Recursively copy opensteamtool signature files
            opensteamtool_src = os.path.join(st_dir, "opensteamtool")
            opensteamtool_dst = os.path.join(config.steam_path, "opensteamtool")
            if os.path.isdir(opensteamtool_src):
                try:
                    os.makedirs(opensteamtool_dst, exist_ok=True)
                    for root, _, files in os.walk(opensteamtool_src):
                        for f in files:
                            if f.endswith(".toml"):
                                src_f = os.path.join(root, f)
                                rel_path = os.path.relpath(src_f, opensteamtool_src)
                                dst_f = os.path.join(opensteamtool_dst, rel_path)
                                os.makedirs(os.path.dirname(dst_f), exist_ok=True)
                                shutil.copy2(src_f, dst_f)
                except Exception as e:
                    logger.warning(f"[SteamTools Auto-Setup] Failed to copy opensteamtool signature files: {e}")
        
        # If OpenSteamTool.dll or others are still missing, fetch directly from GitHub
        for f in target_files:
            dst = os.path.join(config.steam_path, f)
            if not os.path.isfile(dst) or os.path.getsize(dst) < 10000:
                try:
                    url = f"https://raw.githubusercontent.com/mythoscd/SteaMRogue/main/steamtools_files/{f}"
                    r = requests.get(url, headers={"User-Agent": "SteaMRogue"}, timeout=20)
                    if r.status_code == 200 and len(r.content) > 10000:
                        with open(dst, "wb") as out_f:
                            out_f.write(r.content)
                        installed_count += 1
                        logger.info(f"[SteamTools Auto-Setup] Auto-downloaded {f} from GitHub to {dst}")
                except Exception as ex:
                    logger.warning(f"[SteamTools Auto-Setup] Failed downloading {f}: {ex}")

        # Ensure required Steam folders exist for stplug-in
        os.makedirs(os.path.join(config.steam_path, "config", "lua"), exist_ok=True)
        os.makedirs(os.path.join(config.steam_path, "config", "depotcache"), exist_ok=True)
        os.makedirs(os.path.join(config.steam_path, "depotcache"), exist_ok=True)

        logger.info(f"[SteamTools Auto-Setup] Auto-setup complete ({installed_count} files installed).")
        return True
    except Exception as e:
        logger.error(f"[SteamTools Auto-Setup] Error during auto-setup: {e}")
        return False

# %%
def run_self_healing_routine(force: bool = False) -> Dict[str, Any]:
    """
    Comprehensive self-healing routine for SteaMRogue:
    1. Verifies/discovers Steam installation path.
    2. Cleans Steam CEF crash residues (.crash flags and corrupted htmlcache).
    3. Checks and repairs SteamTools DLLs (OpenSteamTool.dll, dwmapi.dll, xinput1_4.dll) and TOML signatures.
    4. Ensures Spacewar (AppID 480) LUA is present in config/stplug-in and config/lua.
    5. Repairs unpinned manifests in LUA configs (setManifestid injection).
    6. Synchronizes depotcache manifests between config/depotcache and depotcache.
    7. Verifies and repairs 7-Zip binary (7z.exe & 7z.dll).
    8. Validates applied fixes from applied_fixes.json.
    """
    actions = []
    steam_path = config.steam_path
    
    # 1. Steam path discovery
    if not steam_path or not os.path.isdir(steam_path):
        discovered = config.discover_steam_path()
        if discovered:
            config.steam_path = discovered
            config.save()
            steam_path = discovered
            actions.append(f"Steam dizini otomatik olarak tespit edildi: {steam_path}")
        else:
            return {
                "ok": False,
                "error": "Steam kurulum dizini bulunamadı. Lütfen Ayarlar sekmesinden Steam klasörünü seçin.",
                "actions": actions
            }

    # 2. CEF crash / invisible window residue cleanup
    try:
        cleaned_crash = validator.cleanup_steam_crashes(steam_path)
        if cleaned_crash:
            actions.append("Steam kilitlenme bayrakları (.crash) ve bozuk önbellek temizlendi.")
    except Exception as ce:
        logger.debug(f"[Self-Heal] Crash cleanup: {ce}")

    # 3. SteamTools DLLs and signatures verification/repair
    try:
        is_installed, present = check_steamtools_installed()
        needs_st_repair = force or not is_installed or any(
            not os.path.isfile(os.path.join(steam_path, f)) or os.path.getsize(os.path.join(steam_path, f)) < 1000
            for f in ["OpenSteamTool.dll"]
        )
        if needs_st_repair:
            st_dir = get_bundled_steamtools_dir()
            target_files = ["xinput1_4.dll", "OpenSteamTool.dll"]
            installed_count = 0
            
            dwmapi_bad = os.path.join(steam_path, "dwmapi.dll")
            if os.path.isfile(dwmapi_bad):
                try:
                    os.remove(dwmapi_bad)
                except Exception:
                    pass

            if st_dir:
                for f in target_files:
                    src = os.path.join(st_dir, f)
                    dst = os.path.join(steam_path, f)
                    if os.path.isfile(src) and (force or not os.path.isfile(dst) or os.path.getsize(dst) < 1000):
                        try:
                            shutil.copy2(src, dst)
                            installed_count += 1
                        except Exception:
                            pass
                
                # Signatures
                opensteamtool_src = os.path.join(st_dir, "opensteamtool")
                opensteamtool_dst = os.path.join(steam_path, "opensteamtool")
                if os.path.isdir(opensteamtool_src):
                    try:
                        os.makedirs(opensteamtool_dst, exist_ok=True)
                        for root, _, files in os.walk(opensteamtool_src):
                            for f in files:
                                if f.endswith(".toml"):
                                    src_f = os.path.join(root, f)
                                    rel_path = os.path.relpath(src_f, opensteamtool_src)
                                    dst_f = os.path.join(opensteamtool_dst, rel_path)
                                    os.makedirs(os.path.dirname(dst_f), exist_ok=True)
                                    shutil.copy2(src_f, dst_f)
                    except Exception:
                        pass
                        
            # Fallback download from GitHub if still missing
            for f in target_files:
                dst = os.path.join(steam_path, f)
                if not os.path.isfile(dst) or os.path.getsize(dst) < 1000:
                    try:
                        url = f"https://raw.githubusercontent.com/mythoscd/SteaMRogue/main/steamtools_files/{f}"
                        r = requests.get(url, headers={"User-Agent": "SteaMRogue"}, timeout=15)
                        if r.status_code == 200 and len(r.content) > 1000:
                            with open(dst, "wb") as out_f:
                                out_f.write(r.content)
                            installed_count += 1
                    except Exception:
                        pass
                        
            if installed_count > 0:
                actions.append(f"SteamTools kilit açıcı dosyaları ve imzaları onarıldı ({installed_count} dosya).")
            else:
                actions.append("SteamTools kilit açıcı dosyaları doğrulandı ve sağlam.")
        else:
            actions.append("SteamTools kanca dosyaları doğrulandı.")
    except Exception as ste:
        logger.warning(f"[Self-Heal] SteamTools repair failed: {ste}")

    # 4. Spacewar (AppID 480) & LUA repair
    try:
        plugin_folder = os.path.join(steam_path, "config", "stplug-in")
        lua_folder = os.path.join(steam_path, "config", "lua")
        os.makedirs(plugin_folder, exist_ok=True)
        os.makedirs(lua_folder, exist_ok=True)
        
        # Ensure 480.lua
        added_480 = False
        lua_code = b"addappid(480, 1)\n"
        for folder in [plugin_folder, lua_folder]:
            f_480 = os.path.join(folder, "480.lua")
            if not os.path.isfile(f_480) or os.path.getsize(f_480) < 5:
                with open(f_480, "wb") as lf:
                    lf.write(lua_code)
                added_480 = True
        if added_480:
            actions.append("Spacewar (AppID 480) çok oyunculu çevrimiçi kaydı oluşturuldu.")

        # Pin manifests to LUAs
        fixed_luas = FileManager.repair_stplugin_luas(steam_path)
        if fixed_luas > 0:
            actions.append(f"{fixed_luas} adet oyun LUA yapılandırmasına manifest kimlikleri otomatik sabitlendi.")
    except Exception as le:
        logger.warning(f"[Self-Heal] LUA repair failed: {le}")

    # 5. Depotcache manifests synchronization
    try:
        synced_count = sync_depotcache_manifests(steam_path)
        if synced_count > 0:
            actions.append(f"{synced_count} adet depot manifesti Steam depotcache dizinine eşitlendi.")
    except Exception as me:
        logger.warning(f"[Self-Heal] Manifest sync failed: {me}")

    # 6. 7-Zip Tooling Repair
    try:
        seven_zip = get_7z_binary()
        if seven_zip and os.path.isfile(seven_zip):
            actions.append(f"7-Zip arşivleme motoru doğrulandı ({os.path.basename(seven_zip)}).")
        else:
            actions.append("7-Zip aracı tespit edilemedi, otomatik indirme mekanizması hazır bekletiliyor.")
    except Exception as ze:
        logger.debug(f"[Self-Heal] 7z check: {ze}")

    # 7. Applied Fixes Health Check
    try:
        fixes_file = os.path.join(get_appdata_dir(), "applied_fixes.json")
        if os.path.isfile(fixes_file):
            with open(fixes_file, "r", encoding="utf-8") as ff:
                applied = json.load(ff)
            verified_count = 0
            for item in applied:
                d = item.get("dest_dir")
                if d and os.path.isdir(d):
                    crit = verify_critical_fix_files(d)
                    if crit:
                        verified_count += 1
            if applied:
                actions.append(f"Kayıtlı {len(applied)} adet bypass fixinin {verified_count} tanesi diskte doğrulandı.")
    except Exception as fe:
        logger.debug(f"[Self-Heal] Fixes check: {fe}")

    # 8. OpenSteamTool signature adaptation for new Steam builds
    try:
        if validator.ensure_opensteamtool_signatures(steam_path):
            actions.append("Steam sürüm güncellemesi için OpenSteamTool imza dosyaları otomatik uyarlandı.")
    except Exception as oe:
        logger.debug(f"[Self-Heal] OST signatures: {oe}")

    # 9. Clean up any dummy uninstalled ACF manifests to unlock Steam native drive picker
    try:
        cleaned_acfs = cleanup_dummy_uninstalled_acfs(steam_path)
        if cleaned_acfs > 0:
            actions.append(f"{cleaned_acfs} adet kilitli sahte kütüphane kaydı temizlendi (Steam sürücü seçim diyaloğu etkinleştirildi).")
    except Exception as acf_err:
        logger.debug(f"[Self-Heal] ACF cleanup: {acf_err}")

    # 10. Visual C++ Redistributable check & auto-installation
    try:
        vc_status = validator.check_vcredist_installed()
        if not vc_status.get("all_installed", False):
            logger.info("[Self-Heal] Missing VC++ runtimes detected, installing silently...")
            ok_vc, msg_vc = validator.install_vcredist_silently("all")
            if ok_vc:
                actions.append("Eksik Microsoft Visual C++ 2015-2022 (x86 & x64) çalışma zamanı paketleri otomatik kuruldu.")
            else:
                actions.append(f"Visual C++ kurulum uyarısı: {msg_vc}")
    except Exception as vc_err:
        logger.debug(f"[Self-Heal] VC++ check error: {vc_err}")

    # 11. Security & quarantine self-healing
    try:
        q_check = validator.check_security_quarantine(steam_path)
        if q_check.get("is_quarantined", False):
            logger.info("[Self-Heal] Missing or quarantined DLLs detected, auto-restoring...")
            ok_q, msg_q = validator.auto_restore_quarantined_files(steam_path)
            if ok_q:
                actions.append("Karantinaya alınan/eksik SteamTools kilit açıcı dosyaları otomatik kurtarıldı.")
            else:
                actions.append(f"Antivirüs uyarısı: {msg_q}")
    except Exception as q_err:
        logger.debug(f"[Self-Heal] Quarantine restore error: {q_err}")

    return {
        "ok": True,
        "actions": actions,
        "steam_path": steam_path,
        "message": "Sistem sağlık kontrolü ve otomatik onarım başarıyla tamamlandı!"
    }

# %%
def diagnose_system_issues() -> List[str]:
    """Inspects the system and returns a list of detected issues for the startup warning modal."""
    issues = []
    steam_path = config.steam_path
    if not steam_path or not os.path.isdir(steam_path):
        discovered = config.discover_steam_path()
        if discovered:
            config.steam_path = discovered
            config.save()
            steam_path = discovered
        else:
            issues.append("Steam kurulum dizini bulunamadı.")
            return issues

    # 1. Obsolete dwmapi.dll presence (major crash cause: circular forwarder recursion)
    if os.path.isfile(os.path.join(steam_path, "dwmapi.dll")):
        issues.append("Steam klasöründe çökmeye ve VGUI hatasına neden olan 'dwmapi.dll' kancası tespit edildi.")

    # 2. Missing proxy or OpenSteamTool
    if not os.path.isfile(os.path.join(steam_path, "xinput1_4.dll")):
        issues.append("SteamTools kanca kütüphanesi (xinput1_4.dll) Steam klasöründe eksik.")
    
    ost_p = os.path.join(steam_path, "OpenSteamTool.dll")
    if not os.path.isfile(ost_p) or os.path.getsize(ost_p) < 100000:
        issues.append("OpenSteamTool kilit açıcı modülü eksik veya hasarlı.")

    # 3. Crash flag
    if os.path.isfile(os.path.join(steam_path, ".crash")):
        issues.append("Steam önceki oturumdan kalan kilitlenme durumunda (.crash).")

    # 4. Stale ActiveProcess PID
    try:
        if not validator.is_steam_running():
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam\ActiveProcess", 0, winreg.KEY_READ) as key:
                cur_pid, _ = winreg.QueryValueEx(key, "pid")
                if cur_pid != 0:
                    issues.append("Kayıt defterinde askıda kalmış Steam işlem kaydı (ActiveProcess) bulundu.")
    except Exception:
        pass

    # 5. Crashed CEF cache
    local_appdata = os.environ.get("LOCALAPPDATA", "")
    if local_appdata:
        cef_ls = os.path.join(local_appdata, "Steam", "htmlcache", "Local State")
        if os.path.isfile(cef_ls):
            try:
                with open(cef_ls, "r", encoding="utf-8", errors="ignore") as f:
                    c = f.read()
                    if '"crashed":true' in c or '"exit_type":"Crashed"' in c:
                        issues.append("Bozulmuş Steam arayüz önbelleği (CEF htmlcache) tespit edildi.")
            except Exception:
                pass

    # 6. Spacewar 480.lua missing
    f_480 = os.path.join(steam_path, "config", "stplug-in", "480.lua")
    if not os.path.isfile(f_480) or os.path.getsize(f_480) < 5:
        issues.append("Spacewar (AppID 480) çevrimiçi çok oyunculu kaydı eksik.")

    # 7. Check Visual C++ runtimes
    try:
        vc_status = validator.check_vcredist_installed()
        if not vc_status.get("all_installed", False):
            issues.append(f"Visual C++ Uyarısı: {vc_status.get('details', 'VC++ paketleri eksik.')}")
    except Exception:
        pass

    # 8. Check Antivirus Quarantine
    try:
        q_info = validator.check_security_quarantine(steam_path)
        if q_info.get("is_quarantined", False):
            issues.append(f"Antivirüs Uyarısı: {q_info.get('details')}")
    except Exception:
        pass

    return issues

# %%
# API Endpoint: GET /api/diagnose_system
@app.route("/api/diagnose_system", methods=["GET"])
def api_diagnose_system():
    """Returns detected issues for automatic startup health check."""
    issues = diagnose_system_issues()
    return jsonify({
        "has_issues": len(issues) > 0,
        "issues": issues
    })

# %%
# API Endpoints: Visual C++ Runtimes (x86 & x64) Status & Install
@app.route("/api/vcredist/status", methods=["GET"])
def api_vcredist_status():
    """Checks whether Microsoft Visual C++ 2015-2022 x86 and x64 runtimes are installed."""
    status = validator.check_vcredist_installed()
    return jsonify(status)

@app.route("/api/vcredist/install", methods=["POST"])
def api_vcredist_install():
    """Silently downloads and installs missing Visual C++ 2015-2022 runtimes."""
    data = request.json or {}
    arch = data.get("arch", "all")
    success, message = validator.install_vcredist_silently(arch)
    return jsonify({
        "success": success,
        "message": message,
        "status": validator.check_vcredist_installed()
    })


# %%
# API Endpoint: POST /api/self_heal
@app.route("/api/self_heal", methods=["POST"])
def api_self_heal():
    """Triggers the comprehensive self-healing routine on demand from the UI."""
    data = request.json or {}
    force = bool(data.get("force", True))
    
    restart_steam_flag = bool(data.get("restart_steam", False))
    was_running = validator.is_steam_running()
    if was_running and restart_steam_flag:
        validator.kill_steam(config.steam_path)
        validator.wait_for_steam_exit(timeout=8.0)
        time.sleep(1.5)

    result = run_self_healing_routine(force=force)

    if was_running and restart_steam_flag:
        steam_exe = validator.resolve_steam_exe(config.steam_path)
        if steam_exe:
            validator.launch_steam(steam_exe)
            result["actions"].append("Steam istemcisi güvenli şekilde yeniden başlatıldı.")

    return jsonify(result)

# %%
# API Endpoint: POST /api/install_steamtools
@app.route("/api/install_steamtools", methods=["POST"])
def install_steamtools():
    if not config.steam_path or not os.path.isdir(config.steam_path):
        discovered = config.discover_steam_path()
        if discovered:
            config.steam_path = discovered
            config.save()
        else:
            return jsonify({"success": False, "error": "Steam kurulum dizini bulunamadı. Lütfen Ayarlar sekmesinden Steam dizininizi seçin."})

    # If Steam is currently running, terminate it so DLL files are not locked by Windows OS
    was_steam_running = validator.is_steam_running()
    if was_steam_running:
        logger.info("[SteamTools Install] Steam is running. Terminating Steam gracefully before DLL installation...")
        try:
            validator.kill_steam()
            for _ in range(25):
                time.sleep(0.2)
                if not validator.is_steam_running():
                    break
            time.sleep(0.6)
        except Exception as e:
            logger.warning(f"[SteamTools Install] Could not terminate Steam: {e}")

    target_files = ["xinput1_4.dll", "OpenSteamTool.dll"]
    copied = 0

    # Remove obsolete dwmapi.dll to prevent VGUI_Setup failed crash
    dwmapi_bad = os.path.join(config.steam_path, "dwmapi.dll")
    if os.path.isfile(dwmapi_bad):
        try:
            os.remove(dwmapi_bad)
        except Exception:
            pass

    # 1. Try installing from bundled files first (0ms, 100% offline guaranteed)
    st_dir = get_bundled_steamtools_dir()
    if st_dir:
        try:
            import shutil
            for f in target_files:
                src = os.path.join(st_dir, f)
                dst = os.path.join(config.steam_path, f)
                if os.path.isfile(src):
                    try:
                        shutil.copy2(src, dst)
                        copied += 1
                    except Exception as copy_err:
                        logger.warning(f"Could not copy {f} from bundled: {copy_err}")
            
            # Copy signature files (opensteamtool)
            opensteamtool_src = os.path.join(st_dir, "opensteamtool")
            opensteamtool_dst = os.path.join(config.steam_path, "opensteamtool")
            if os.path.isdir(opensteamtool_src):
                os.makedirs(opensteamtool_dst, exist_ok=True)
                for root, _, files in os.walk(opensteamtool_src):
                    for f in files:
                        if f.endswith(".toml"):
                            src_f = os.path.join(root, f)
                            rel_path = os.path.relpath(src_f, opensteamtool_src)
                            dst_f = os.path.join(opensteamtool_dst, rel_path)
                            os.makedirs(os.path.dirname(dst_f), exist_ok=True)
                            try:
                                shutil.copy2(src_f, dst_f)
                            except Exception:
                                pass

            # Ensure required Steam folders exist
            os.makedirs(os.path.join(config.steam_path, "config", "lua"), exist_ok=True)
            os.makedirs(os.path.join(config.steam_path, "config", "depotcache"), exist_ok=True)
            os.makedirs(os.path.join(config.steam_path, "depotcache"), exist_ok=True)
        except Exception as err:
            logger.warning(f"Bundled copy encountered issue: {err}")

    # Verify if installed now
    is_installed, present = check_steamtools_installed()

    # 2. Fallback: Download complete DLL set from official GitHub repository if missing
    if not is_installed:
        try:
            logger.info("Some SteamTools DLLs missing, attempting fallback download from GitHub...")
            for f in target_files:
                dst = os.path.join(config.steam_path, f)
                if not os.path.isfile(dst) or os.path.getsize(dst) < 1000:
                    url = f"https://raw.githubusercontent.com/mythoscd/SteaMRogue/main/steamtools_files/{f}"
                    r = requests.get(url, headers={"User-Agent": "SteaMRogue"}, timeout=30)
                    if r.status_code == 200 and len(r.content) > 1000:
                        with open(dst, "wb") as out_f:
                            out_f.write(r.content)
                        copied += 1
                        logger.info(f"Downloaded {f} to {dst}")
        except Exception as e:
            logger.warning(f"Fallback download error: {e}")

    # Re-verify after all attempts
    is_installed, present = check_steamtools_installed()
    if is_installed:
        msg = "SteamTools kancası başarıyla kuruldu ve aktifleştirildi!"
        if was_steam_running:
            msg += "\n\nKancanın devreye girmesi için Steam kapatıldı. Lütfen Steam'i şimdi tekrar başlatın veya arayüzdeki 'Steam\\'i Yeniden Başlat' butonuna tıklayın."
        return jsonify({
            "success": True,
            "already_installed": False,
            "was_steam_running": was_steam_running,
            "message": msg
        })
    else:
        return jsonify({
            "success": False,
            "error": "SteamTools dosyaları Steam dizinine yerleştirilemedi. Lütfen Steam'in tamamen kapalı olduğundan ve antivirüsünüzün (Windows Defender) engellemediğinden emin olun."
        })

def sync_depotcache_manifests(steam_path: str) -> int:
    """Ensures all .manifest files in config/depotcache are safely mirrored to official depotcache."""
    if not steam_path or not os.path.isdir(steam_path):
        return 0
    config_depotcache = os.path.join(steam_path, "config", "depotcache")
    depotcache = os.path.join(steam_path, "depotcache")
    if not os.path.isdir(config_depotcache):
        return 0
    os.makedirs(depotcache, exist_ok=True)
    synced = 0
    import shutil
    for f in os.listdir(config_depotcache):
        if f.lower().endswith(".manifest"):
            src = os.path.join(config_depotcache, f)
            dst = os.path.join(depotcache, f)
            if not os.path.isfile(dst) or (os.path.getsize(dst) != os.path.getsize(src)):
                try:
                    shutil.copy2(src, dst)
                    synced += 1
                except Exception:
                    pass
    if synced > 0:
        logger.info(f"[depotcache] Synced {synced} manifest files to official depotcache.")
    return synced

def cleanup_dummy_uninstalled_acfs(steam_path: str) -> int:
    """Removes dummy uninstalled ACF manifests (StateFlags: 1, SizeOnDisk: 0) from all libraries
    and cleans their empty entries from libraryfolders.vdf.
    
    This ensures Steam always opens its native install dialog asking the user which drive
    (C:, D:, etc.) they want to install the game to, and displays the true required disk space
    instead of locking the location with 'YÜKLEME KLASÖRÜ DEĞİŞTİRİLEMEZ' and '0 B'.
    """
    if not steam_path or not os.path.isdir(steam_path):
        return 0
    cleaned = 0
    try:
        libs = FileManager.get_library_folders(steam_path)
        for _, lib_path in libs:
            steamapps = os.path.join(lib_path, "steamapps")
            if not os.path.isdir(steamapps):
                continue
            for f in os.listdir(steamapps):
                if f.startswith("appmanifest_") and f.endswith(".acf"):
                    p = os.path.join(steamapps, f)
                    try:
                        with open(p, "r", encoding="utf-8", errors="ignore") as fp:
                            txt = fp.read()
                        if '"StateFlags"\t\t"1"' in txt and '"SizeOnDisk"\t\t"0"' in txt:
                            m_aid = re.search(r'"appid"\s+"(\d+)"', txt)
                            m_dir = re.search(r'"installdir"\s+"([^"]+)"', txt)
                            idir = m_dir.group(1) if m_dir else ""
                            common_p = os.path.join(steamapps, "common", idir)
                            has_content = os.path.isdir(common_p) and len(os.listdir(common_p)) > 0 if idir else False
                            if not has_content:
                                os.remove(p)
                                bak_p = p + ".bak"
                                if os.path.isfile(bak_p):
                                    try:
                                        os.remove(bak_p)
                                    except Exception:
                                        pass
                                if m_aid:
                                    FileManager.remove_from_library_folders(steam_path, m_aid.group(1))
                                cleaned += 1
                                logger.info(f"[cleanup_dummy_uninstalled_acfs] Liberated {f} to enable Steam drive picker.")
                    except Exception as ex:
                        logger.debug(f"Error checking {f}: {ex}")
        if cleaned > 0:
            logger.info(f"[cleanup_dummy_uninstalled_acfs] Cleaned {cleaned} dummy ACFs. Steam drive picker restored.")
    except Exception as e:
        logger.warning(f"[cleanup_dummy_uninstalled_acfs] Error cleaning dummy ACFs: {e}")
    return cleaned

def ensure_all_unlocked_acfs(steam_path: str) -> int:
    """Backward compatibility alias that calls cleanup_dummy_uninstalled_acfs."""
    return cleanup_dummy_uninstalled_acfs(steam_path)

# %%
# API Endpoint: POST /api/clear_steam_cache
@app.route("/api/clear_steam_cache", methods=["POST"])
def clear_steam_cache():
    if not config.steam_path or not os.path.isdir(config.steam_path):
        return jsonify({"success": False, "error": "Steam kurulum dizini bulunamadı."})
    
    try:
        import shutil
        # 1. Kill steam if running
        was_running = validator.is_steam_running()
        if was_running:
            validator.kill_steam()
            for _ in range(25):
                time.sleep(0.2)
                if not validator.is_steam_running():
                    break
            time.sleep(0.8)

        cleared_items = 0

        # 2. Clear ONLY temporary ticket files (*.vdf) from depotcache - NEVER DELETE .manifest files!
        depotcache = os.path.join(config.steam_path, "depotcache")
        if os.path.isdir(depotcache):
            for f in os.listdir(depotcache):
                if f.lower().endswith(".vdf"):
                    try:
                        os.remove(os.path.join(depotcache, f))
                        cleared_items += 1
                    except Exception:
                        pass

        # 3. Clear appcache httpcache (corrupted HTTP chunk manifests)
        httpcache = os.path.join(config.steam_path, "appcache", "httpcache")
        if os.path.isdir(httpcache):
            try:
                shutil.rmtree(httpcache, ignore_errors=True)
                cleared_items += 1
            except Exception:
                pass

        # 4. Clear stuck downloading & temp directories (stuck 0-byte corrupt chunks cause "İnternet Yok")
        downloading_dir = os.path.join(config.steam_path, "steamapps", "downloading")
        if os.path.isdir(downloading_dir):
            try:
                for item in os.listdir(downloading_dir):
                    item_p = os.path.join(downloading_dir, item)
                    if os.path.isdir(item_p):
                        shutil.rmtree(item_p, ignore_errors=True)
                    else:
                        os.remove(item_p)
                cleared_items += 1
            except Exception:
                pass

        temp_dir = os.path.join(config.steam_path, "steamapps", "temp")
        if os.path.isdir(temp_dir):
            try:
                for item in os.listdir(temp_dir):
                    item_p = os.path.join(temp_dir, item)
                    if os.path.isdir(item_p):
                        shutil.rmtree(item_p, ignore_errors=True)
                    else:
                        os.remove(item_p)
                cleared_items += 1
            except Exception:
                pass

        # 5. GUARANTEE that all manifests in config/depotcache are restored into depotcache!
        synced_manifests = sync_depotcache_manifests(config.steam_path)

        # 6. Auto-repair and pin manifests in all existing LUAs
        repaired_luas = FileManager.repair_stplugin_luas(config.steam_path)

        # 7. Re-verify SteamTools DLLs and toml signatures in Steam folder
        ensure_steamtools_installed_auto()

        # 8. Clean steam restart with normal GUI
        steam_exe = os.path.join(config.steam_path, "steam.exe")
        started = False
        if os.path.isfile(steam_exe):
            validator.wait_for_steam_exit(timeout=6.0)
            time.sleep(1.5)
            started = validator.launch_steam(steam_exe)

        return jsonify({
            "success": True,
            "message": f"Steam indirme önbelleği temizlendi ({cleared_items} geçici öğe temizlendi, {synced_manifests} manifest eşitlendi, {repaired_luas} oyun ayarı onarıldı) ve Steam başarıyla açıldı!\n\nArtık oyunlarınızı sorunsuz indirebilirsiniz."
        })
    except Exception as e:
        logger.error(f"Failed to clear steam cache: {e}")
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
                
        if not manifests and config.steam_path:
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
            
        # 4. Clean any existing dummy ACF so Steam's native install dialog prompts for drive location
        # and displays the real download size instead of locking location to C:\ with "0 B".
        update_status("Kütüphane kayıtları düzenleniyor...", 95)
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
        return jsonify({"success": False, "error": "AppID, geçerli Steam linki veya oyun adı gereklidir"})
        
    resolved_name = f"Steam App {appid}"
    
    if not appid.isdigit():
        # Try to resolve name to AppID via Steam API
        results = SteamAPI.search_store(raw_appid)
        if results and len(results) > 0:
            appid = results[0]["id"]
            resolved_name = results[0]["name"]
        else:
            return jsonify({"success": False, "error": f"'{raw_appid}' aramasına uygun oyun bulunamadı."})
    else:
        # Try to get the name from cache or details
        cache_path = get_cache_path()
        with _names_cache_lock:
            current_cache = {}
            if os.path.exists(cache_path) and os.path.getsize(cache_path) > 0:
                try:
                    with open(cache_path, "r", encoding="utf-8") as f:
                        current_cache = json.load(f)
                except Exception:
                    pass
            cached = current_cache.get(appid)
            if cached and isinstance(cached, dict) and cached.get("name") != f"Steam App {appid}":
                resolved_name = cached.get("name")
            else:
                details = SteamAPI.get_app_details(appid)
                if details:
                    resolved_name = details.get("name", resolved_name)
                    
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
    
    return jsonify({"success": True, "appid": appid, "name": resolved_name})

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
    # 1. Bundled / localized 7z.exe (highest priority, always self-contained)
    bundled_7z = get_7z_binary()
    if bundled_7z and os.path.isfile(bundled_7z):
        return bundled_7z

    paths = [
        r"C:\Program Files\7-Zip\7z.exe",
        r"C:\Program Files (x86)\7-Zip\7z.exe",
        r"C:\Program Files\WinRAR\UnRAR.exe",
        r"C:\Program Files\WinRAR\WinRAR.exe",
    ]
    for p in paths:
        if os.path.isfile(p):
            return p
    # Fallback to PATH check
    import shutil
    for cmd in ["7z", "unrar"]:
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

# %%
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

# %%
@app.route("/api/add_exclusion", methods=["POST"])
def api_add_exclusion():
    """Adds SteaMRogue and all Steam libraries to Windows Defender exclusion list."""
    if os.name != 'nt':
        return jsonify({"success": False, "error": "Sadece Windows sistemlerde desteklenir."})
    try:
        current_dir = BASE_DIR
        local_app_dir = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "steamtools-auto")
        steam_dir = config.steam_path

        paths = [current_dir]
        if os.path.isdir(local_app_dir):
            paths.append(local_app_dir)
        if steam_dir and os.path.isdir(steam_dir):
            paths.append(steam_dir)

        try:
            for l in get_all_steam_libraries():
                if os.path.isdir(l):
                    paths.append(l)
        except Exception:
            pass

        norm_paths = sorted(list(set([os.path.normpath(p) for p in paths if p and os.path.isdir(p)])))
        path_args = ",".join([f"'{p}'" for p in norm_paths])
        ps_cmd = f"Add-MpPreference -ExclusionPath {path_args} -ExclusionProcess 'SteaMRogue.exe','SteamTools_Auto_Backend.exe','steam.exe'"
        elevate_cmd = f"Start-Process powershell -Verb RunAs -ArgumentList '-WindowStyle Hidden -NoProfile -Command \"{ps_cmd}\"'"
        
        subprocess.run(["powershell", "-WindowStyle", "Hidden", "-NoProfile", "-Command", elevate_cmd], creationflags=0x08000000)
        
        av_info = validator.get_system_antivirus_info()
        return jsonify({
            "success": True,
            "message": "Windows Defender dışlama isteği yönetici haklarıyla gönderildi.",
            "paths": norm_paths,
            "av_info": av_info
        })
    except Exception as e:
        logger.error(f"Error adding exclusion: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)})

# %%
@app.route("/api/security/status", methods=["GET"])
def api_security_status():
    """Returns detected antivirus software, quarantine status, and recommended exclusion paths."""
    steam_path = config.steam_path or config.discover_steam_path() or ""
    av_info = validator.get_system_antivirus_info()
    quarantine = validator.check_security_quarantine(steam_path)

    paths = []
    current_dir = BASE_DIR
    local_app_dir = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "steamtools-auto")
    if os.path.isdir(current_dir):
        paths.append(current_dir)
    if os.path.isdir(local_app_dir):
        paths.append(local_app_dir)
    if steam_path and os.path.isdir(steam_path):
        paths.append(steam_path)
    try:
        for l in get_all_steam_libraries():
            if os.path.isdir(l):
                paths.append(l)
    except Exception:
        pass

    return jsonify({
        "av_info": av_info,
        "quarantine": quarantine,
        "exclusion_paths": sorted(list(set([os.path.normpath(p) for p in paths if p and os.path.isdir(p)])))
    })

# %%
@app.route("/api/security/restore_quarantine", methods=["POST"])
def api_security_restore_quarantine():
    """Restores quarantined or missing SteamTools DLLs and ensures signature integrity."""
    steam_path = config.steam_path or config.discover_steam_path() or ""
    success, message = validator.auto_restore_quarantined_files(steam_path)
    return jsonify({
        "success": success,
        "message": message,
        "quarantine": validator.check_security_quarantine(steam_path)
    })

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
    """Finds 7z.exe from bundled or standard locations with automatic fallback."""
    candidates = []
    if getattr(sys, 'frozen', False):
        if hasattr(sys, '_MEIPASS'):
            candidates.append(os.path.join(sys._MEIPASS, '7z.exe'))
            candidates.append(os.path.join(sys._MEIPASS, 'resources', '7z.exe'))
        exe_dir = os.path.dirname(sys.executable)
        candidates.append(os.path.join(exe_dir, '7z.exe'))
        candidates.append(os.path.join(exe_dir, 'resources', '7z.exe'))
        candidates.append(os.path.join(exe_dir, '..', 'resources', '7z.exe'))

    base_dir = BASE_DIR
    candidates.append(os.path.join(base_dir, 'resources', '7z.exe'))
    candidates.append(os.path.join(base_dir, '7z.exe'))
    candidates.append(os.path.join(base_dir, 'node_modules', 'electron-winstaller', 'vendor', '7z.exe'))
    candidates.append(os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "steamtools-auto", "resources", "7z.exe"))
    candidates.append(r"C:\Program Files\7-Zip\7z.exe")
    candidates.append(r"C:\Program Files (x86)\7-Zip\7z.exe")

    for c in candidates:
        if c and os.path.isfile(c):
            return c

    # Fallback: Download 7z.exe and 7z.dll to AppData/SteaMRogue/bin if somehow missing
    try:
        bin_dir = os.path.join(get_appdata_dir(), "bin")
        os.makedirs(bin_dir, exist_ok=True)
        local_7z = os.path.join(bin_dir, "7z.exe")
        local_dll = os.path.join(bin_dir, "7z.dll")
        if not os.path.isfile(local_7z):
            logger.info("[7z] Downloading 7z.exe fallback from GitHub...")
            r1 = requests.get("https://raw.githubusercontent.com/mythoscd/SteaMRogue/main/resources/7z.exe", headers={"User-Agent": "SteaMRogue"}, timeout=30)
            if r1.status_code == 200 and len(r1.content) > 10000:
                with open(local_7z, "wb") as f:
                    f.write(r1.content)
        if not os.path.isfile(local_dll):
            logger.info("[7z] Downloading 7z.dll fallback from GitHub...")
            r2 = requests.get("https://raw.githubusercontent.com/mythoscd/SteaMRogue/main/resources/7z.dll", headers={"User-Agent": "SteaMRogue"}, timeout=30)
            if r2.status_code == 200 and len(r2.content) > 10000:
                with open(local_dll, "wb") as f:
                    f.write(r2.content)
        if os.path.isfile(local_7z):
            return local_7z
    except Exception as e:
        logger.warning(f"[7z] Fallback download failed: {e}")

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

def extract_archive_with_passwords(archive_path: str, extract_to: str, seven_zip: str = None) -> bool:
    """
    Extracts an archive (zip, 7z, rar, 001, etc.) into extract_to using 7-Zip or zipfile fallback.
    Automatically tries common OnlineFix passwords ('online-fix.me', '', 'online-fix', 'www.online-fix.me').
    """
    import subprocess
    import zipfile
    
    os.makedirs(extract_to, exist_ok=True)
    passwords = ["online-fix.me", "", "online-fix", "www.online-fix.me"]
    
    if seven_zip and os.path.isfile(seven_zip):
        flags = 0x08000000 if os.name == 'nt' else 0
        for pwd in passwords:
            cmd = [seven_zip, 'x', archive_path, f'-o{extract_to}', '-y', '-aoa', '-mmt=on']
            if pwd:
                cmd.append(f'-p{pwd}')
            else:
                cmd.append('-p-')
            try:
                proc = subprocess.run(cmd, creationflags=flags, capture_output=True, text=True, timeout=180)
                if os.path.exists(extract_to) and len(os.listdir(extract_to)) > 0:
                    logger.info(f"[extract_archive] Successfully extracted with password: '{pwd}'")
                    return True
            except Exception as pe:
                logger.debug(f"[extract_archive] Attempt with pwd '{pwd}' failed: {pe}")
                continue

    # Fallback to python zipfile if .zip
    if archive_path.lower().endswith('.zip') and zipfile.is_zipfile(archive_path):
        for pwd in passwords:
            try:
                pwd_bytes = pwd.encode('utf-8') if pwd else None
                with zipfile.ZipFile(archive_path, 'r') as zf:
                    zf.extractall(extract_to, pwd=pwd_bytes)
                if os.path.exists(extract_to) and len(os.listdir(extract_to)) > 0:
                    logger.info(f"[extract_archive] Extracted via zipfile with pwd: '{pwd}'")
                    return True
            except Exception:
                continue

    return os.path.exists(extract_to) and len(os.listdir(extract_to)) > 0


def flatten_extracted_dir(staging_path: str) -> str:
    """
    Detects if an archive was wrapped in a single top-level folder (e.g. 'GameName Fix/').
    If so, moves all contents up to staging_path and deletes the empty wrapper.
    Ignores and deletes OS junk like __MACOSX, .DS_Store, Thumbs.db.
    """
    import shutil
    
    # 1. Clean junk files/folders
    for junk in ["__MACOSX", ".DS_Store", "Thumbs.db"]:
        jp = os.path.join(staging_path, junk)
        if os.path.exists(jp):
            if os.path.isdir(jp):
                shutil.rmtree(jp, ignore_errors=True)
            else:
                try: os.remove(jp)
                except Exception: pass

    # 2. Flatten single wrappers
    while True:
        items = os.listdir(staging_path)
        if len(items) == 1:
            single = os.path.join(staging_path, items[0])
            if os.path.isdir(single):
                name_lower = items[0].lower()
                if name_lower in ("engine", "binaries", "plugins") or name_lower.endswith("_data"):
                    break
                for sub in os.listdir(single):
                    shutil.move(os.path.join(single, sub), os.path.join(staging_path, sub))
                try:
                    os.rmdir(single)
                except Exception:
                    pass
                continue
        break
    return staging_path


def find_game_steam_dll_locations(dest_dir: str) -> list:
    """
    Recursively searches dest_dir for existing steam_api64.dll or steam_api.dll,
    or key binary directories (Unreal Engine 'Binaries/Win64', Unity 'Plugins', 'bin').
    """
    locations = set()
    for root, dirs, files in os.walk(dest_dir):
        files_lower = [f.lower() for f in files]
        if 'steam_api64.dll' in files_lower or 'steam_api.dll' in files_lower:
            locations.add(os.path.abspath(root))
        if os.path.basename(root).lower() == 'win64' and os.path.basename(os.path.dirname(root)).lower() == 'binaries':
            locations.add(os.path.abspath(root))
        parts_lower = [p.lower() for p in root.split(os.sep)]
        if 'plugins' in parts_lower:
            for f in files_lower:
                if f.endswith('.dll') and 'steam' in f:
                    locations.add(os.path.abspath(root))
    return list(locations)


def install_fix_files(staging_path: str, dest_dir: str) -> list:
    """
    Copies all extracted fix files into dest_dir.
    Creates backups (.bak) for original DLL files before overwriting.
    Detects deep binary subdirectories (e.g. Binaries/Win64) and injects critical fix DLLs/INIs there as well.
    """
    import shutil
    copied_files = []
    critical_names = {
        'steam_api64.dll', 'steam_api.dll', 'onlinefix64.dll', 'onlinefix.dll',
        'onlinefix.ini', 'steamoverlay64.dll', 'steamoverlay.dll',
        'steamclient64.dll', 'steamclient.dll'
    }

    # 1. Merge staging directory tree into dest_dir
    for root, dirs, files in os.walk(staging_path):
        rel_path = os.path.relpath(root, staging_path)
        target_root = dest_dir if rel_path == '.' else os.path.join(dest_dir, rel_path)
        os.makedirs(target_root, exist_ok=True)
        for f in files:
            src_file = os.path.join(root, f)
            dest_file = os.path.join(target_root, f)
            if os.path.isfile(dest_file) and f.lower().endswith('.dll') and not f.lower().endswith('.bak'):
                bak_file = dest_file + '.bak'
                if not os.path.exists(bak_file):
                    try:
                        shutil.copy2(dest_file, bak_file)
                        logger.info(f"[install_fix] Created backup: {bak_file}")
                    except Exception as be:
                        logger.warning(f"[install_fix] Backup failed for {dest_file}: {be}")
            shutil.copy2(src_file, dest_file)
            copied_files.append(dest_file)

    # 2. Deep target injection for games with binaries in subfolders (e.g. Unreal/Unity)
    deep_targets = find_game_steam_dll_locations(dest_dir)
    critical_sources = {}
    for root, dirs, files in os.walk(staging_path):
        for f in files:
            if f.lower() in critical_names:
                critical_sources[f.lower()] = (f, os.path.join(root, f))

    for target_dir in deep_targets:
        if os.path.abspath(target_dir) == os.path.abspath(dest_dir):
            continue
        for lower_name, (orig_name, src_path) in critical_sources.items():
            dest_file = os.path.join(target_dir, orig_name)
            if os.path.isfile(dest_file) and lower_name.endswith('.dll'):
                bak_file = dest_file + '.bak'
                if not os.path.exists(bak_file):
                    try:
                        shutil.copy2(dest_file, bak_file)
                        logger.info(f"[install_fix] Created deep backup: {bak_file}")
                    except Exception:
                        pass
            shutil.copy2(src_path, dest_file)
            copied_files.append(dest_file)
            logger.info(f"[install_fix] Deep-injected fix file: {dest_file}")

    return list(dict.fromkeys(copied_files))


def verify_critical_fix_files(dest_dir: str) -> list:
    """
    Checks if critical fix files exist on disk inside dest_dir or its subdirectories.
    """
    critical_names = {
        'steam_api64.dll', 'steam_api.dll', 'onlinefix64.dll', 'onlinefix.dll',
        'onlinefix.ini', 'steamoverlay64.dll', 'steamoverlay.dll',
        'steamclient64.dll', 'steamclient.dll'
    }
    found = []
    for root, dirs, files in os.walk(dest_dir):
        for f in files:
            if f.lower() in critical_names:
                found.append(os.path.join(root, f))
    return found


def auto_register_fix_appids(dest_dir: str, default_appid: str, steam_path: str) -> list:
    """
    Ensures that default_appid, Spacewar (480), and any AppID specified in OnlineFix.ini
    are registered in SteamTools stplug-in and lua configuration files.
    """
    appids_to_register = set()
    if default_appid:
        appids_to_register.add(str(default_appid).strip())
    appids_to_register.add("480")

    for root, dirs, files in os.walk(dest_dir):
        for f in files:
            if f.lower().endswith(".ini"):
                ini_path = os.path.join(root, f)
                try:
                    with open(ini_path, "r", encoding="utf-8", errors="ignore") as inif:
                        for line in inif:
                            m = re.search(r"^\s*(?:FakeAppId|RealAppId|AppId)\s*=\s*(\d+)", line, re.IGNORECASE)
                            if m:
                                appids_to_register.add(m.group(1).strip())
                except Exception as ie:
                    logger.debug(f"[auto_register_fix_appids] Error reading {ini_path}: {ie}")

    registered = []
    if steam_path and os.path.isdir(steam_path):
        plugin_folder = os.path.join(steam_path, "config", "stplug-in")
        lua_folder = os.path.join(steam_path, "config", "lua")
        os.makedirs(plugin_folder, exist_ok=True)
        os.makedirs(lua_folder, exist_ok=True)

        for aid in appids_to_register:
            if not aid:
                continue
            lua_code = f"addappid({aid}, 1)\n".encode("utf-8")
            for folder in [plugin_folder, lua_folder]:
                lua_path = os.path.join(folder, f"{aid}.lua")
                if not os.path.isfile(lua_path):
                    with open(lua_path, "wb") as lf:
                        lf.write(lua_code)
                    logger.info(f"[auto_register_fix_appids] Created {lua_path}")
                else:
                    try:
                        with open(lua_path, "r", encoding="utf-8", errors="ignore") as lf:
                            text = lf.read()
                        if f"addappid({aid}" not in text:
                            with open(lua_path, "a", encoding="utf-8") as lf:
                                lf.write(f"\naddappid({aid}, 1)\n")
                    except Exception:
                        pass
            registered.append(aid)

        try:
            FileManager.repair_stplugin_luas(steam_path)
        except Exception as re:
            logger.debug(f"[auto_register_fix_appids] repair_stplugin_luas: {re}")

    return registered


# ---- BYPASS: Fix Uygula ----
@app.route("/api/apply_fix", methods=["POST"])
def api_apply_fix():
    """
    Nexus API üzerinden fix dosyalarını çeker, şifreli arşivleri ('online-fix.me') 7-Zip ile çözer,
    klasör hiyerarşisini düzleştirir, derin oyun dizinlerini (Binaries/Win64, Plugins) tespit edip
    enjekte eder, fiziksel dosya doğrulamasını yapar ve Spacewar (AppID 480) kaydını stplug-in'e ekler.
    """
    import shutil, tempfile, urllib.request
    data = request.json or {}
    appid = str(data.get("appid", "")).strip()
    dest_dir = data.get("dest_dir", "").strip()
    game = data.get("game", {})

    if not appid:
        return jsonify({"ok": False, "message": "AppID eksik."})
    if not dest_dir or not os.path.isdir(dest_dir):
        return jsonify({"ok": False, "message": "Geçersiz hedef klasör."})

    logger.info(f"[apply_fix] Starting overhaul fix application for appid: {appid} -> {dest_dir}")

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

        filename = fix_url.split("/")[-1].split("?")[0] or "fix.zip"
        files = [{"name": filename, "download_url": fix_url}]

    # 3. Dosyaları geçici klasöre indir
    temp_dir = tempfile.mkdtemp(prefix=f"bypass_{appid}_")
    staging_dir = os.path.join(temp_dir, "extracted")
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

        if archive_candidates:
            archive_candidates.sort(key=lambda x: x[0], reverse=True)
            main_archive = archive_candidates[0][1]
            logger.info(f"[apply_fix] Extracting archive: {main_archive}")
            
            extracted_ok = extract_archive_with_passwords(main_archive, staging_dir, seven_zip)
            if not extracted_ok:
                raise RuntimeError("Arşiv çıkartılamadı (şifre korumalı veya 7-Zip aracı başarısız oldu).")
        else:
            os.makedirs(staging_dir, exist_ok=True)
            for p in downloaded_paths:
                shutil.copy2(p, os.path.join(staging_dir, os.path.basename(p)))

        # 5. Klasör hiyerarşisini düzleştir (iç içe tek klasör sarmalayıcılarını kaldır)
        flatten_extracted_dir(staging_dir)

        # 6. Dosyaları hedef oyun klasörüne ve derin alt dizinlere (Binaries/Win64) enjekte et
        installed_files = install_fix_files(staging_dir, dest_dir)
        logger.info(f"[apply_fix] Installed {len(installed_files)} files into {dest_dir}")

        # 7. Fiziksel dosya doğrulaması yap
        verified_files = verify_critical_fix_files(dest_dir)
        is_verified = len(verified_files) > 0
        logger.info(f"[apply_fix] Verification result: {is_verified} (Found: {len(verified_files)} critical files)")

        # 8. Spacewar (AppID 480) ve FakeAppId'leri SteamTools stplug-in'e otomatik ekle
        registered_appids = auto_register_fix_appids(dest_dir, appid, config.steam_path)
        logger.info(f"[apply_fix] Auto-registered AppIDs in stplug-in: {registered_appids}")

        # 9. applied_fixes.json kaydı
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
                "timestamp": time.time(),
                "verified": is_verified,
                "verified_files_count": len(verified_files)
            })
            with open(fixes_file, "w", encoding="utf-8") as f:
                json.dump(existing_fixes, f, indent=2)
        except Exception as err:
            logger.warning(f"[apply_fix] Could not save applied fix tracking: {err}")

        success_msg = f"{game.get('name') or 'Oyun'} için fix başarıyla uygulandı ve Spacewar (480) çevrimiçi bağlantısı sağlandı!"
        if not is_verified:
            success_msg = f"Fix dosyaları {dest_dir} klasörüne kopyalandı. Lütfen oyunu başlatmayı deneyin."

        return jsonify({
            "ok": True,
            "message": success_msg,
            "verified": is_verified,
            "verified_files": [os.path.basename(f) for f in verified_files],
            "registered_appids": registered_appids
        })

    except Exception as e:
        logger.error(f"[apply_fix] Error applying fix: {e}", exc_info=True)
        return jsonify({"ok": False, "message": f"Fix uygulama hatası: {str(e)}"})
    finally:
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass

# %%
# Steam Achievement Manager (SAM) Integration

def find_sam_binary(filename: str) -> Optional[str]:
    """Locates a SAM executable or library across dev, PyInstaller, and installed Electron resources."""
    exe_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
    base_dir = os.path.abspath(os.path.dirname(__file__))

    candidates = [
        # PyInstaller bundled resources
        os.path.join(getattr(sys, '_MEIPASS', ''), 'resources', 'sam', filename),
        os.path.join(getattr(sys, '_MEIPASS', ''), 'resources', 'resources', 'sam', filename),
        # Current exe / script dir
        os.path.join(exe_dir, 'resources', 'sam', filename),
        os.path.join(exe_dir, 'resources', 'resources', 'sam', filename),
        # Parent of backend (when running in resources/ folder of Electron)
        os.path.join(exe_dir, '..', 'resources', 'sam', filename),
        os.path.join(exe_dir, '..', 'resources', 'resources', 'sam', filename),
        # Base dir
        os.path.join(BASE_DIR, 'resources', 'sam', filename),
        os.path.join(base_dir, 'resources', 'sam', filename),
        os.path.join(base_dir, 'resources', 'resources', 'sam', filename),
        # Installed AppData path
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "steamtools-auto", "resources", "sam", filename),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "steamtools-auto", "resources", "resources", "sam", filename)
    ]

    for p in candidates:
        if p and os.path.isfile(p):
            return os.path.abspath(p)
    return None

@app.route("/api/sam/status", methods=["GET"])
def sam_status():
    """Returns availability of SAM binaries and Steam Client connection status."""
    worker = find_sam_binary("SAMWorker.exe")
    game = find_sam_binary("SAM.Game.exe")
    api_dll = find_sam_binary("SAM.API.dll")
    steam_running = validator.is_steam_running()
    
    return jsonify({
        "success": True,
        "sam_available": bool(worker and game and api_dll),
        "steam_running": steam_running,
        "worker_found": bool(worker),
        "game_found": bool(game),
        "api_dll_found": bool(api_dll)
    })

@app.route("/api/sam/achievements/<appid>", methods=["GET"])
def sam_get_achievements(appid):
    """Retrieves achievements for an AppID directly using headless SAMWorker."""
    appid = str(appid).strip()
    if not appid.isdigit():
        return jsonify({"success": False, "error": "Geçersiz AppID formatı."}), 400

    if not validator.is_steam_running():
        return jsonify({
            "success": False,
            "error": "Steam açık değil. Başarımları görebilmek için lütfen önce Steam'i başlatın."
        }), 400

    worker_path = find_sam_binary("SAMWorker.exe")
    if not worker_path:
        return jsonify({"success": False, "error": "SAMWorker.exe bulunamadı."}), 404

    try:
        work_dir = os.path.dirname(worker_path)
        creationflags = 0x08000000 if os.name == 'nt' else 0  # CREATE_NO_WINDOW
        
        proc = subprocess.run(
            [worker_path, "get", appid],
            cwd=work_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=creationflags,
            timeout=15,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )
        out = (proc.stdout or "").strip()
        if not out:
            return jsonify({"success": False, "error": "Başarım servisi boş yanıt döndürdü."}), 500
        
        data = json.loads(out)
        return jsonify(data)
    except subprocess.TimeoutExpired:
        return jsonify({"success": False, "error": "Steam başarım verisi alma zaman aşımına uğradı."}), 504
    except Exception as ex:
        logger.error(f"[SAM Achievements] Error: {ex}", exc_info=True)
        return jsonify({"success": False, "error": str(ex)}), 500

@app.route("/api/sam/save", methods=["POST"])
def sam_save_achievements():
    """Saves unlocked/locked achievements directly to Steam via headless SAMWorker."""
    data = request.get_json(silent=True) or {}
    appid = str(data.get("appid", "")).strip()
    unlocked_ids = data.get("unlocked_ids", [])

    if not appid.isdigit():
        return jsonify({"success": False, "error": "Geçersiz AppID."}), 400

    if not validator.is_steam_running():
        return jsonify({
            "success": False,
            "error": "Steam açık değil. Başarımları kaydedebilmek için lütfen önce Steam'i başlatın."
        }), 400

    worker_path = find_sam_binary("SAMWorker.exe")
    if not worker_path:
        return jsonify({"success": False, "error": "SAMWorker.exe bulunamadı."}), 404

    try:
        work_dir = os.path.dirname(worker_path)
        creationflags = 0x08000000 if os.name == 'nt' else 0  # CREATE_NO_WINDOW
        payload = ",".join(str(i).strip() for i in unlocked_ids)

        proc = subprocess.run(
            [worker_path, "set", appid, "--stdin"],
            input=payload,
            cwd=work_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=creationflags,
            timeout=20,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )
        out = (proc.stdout or "").strip()
        if not out:
            return jsonify({"success": False, "error": "Kaydetme servisi yanıt vermedi."}), 500

        res = json.loads(out)
        return jsonify(res)
    except subprocess.TimeoutExpired:
        return jsonify({"success": False, "error": "Kaydetme işlemi zaman aşımına uğradı."}), 504
    except Exception as ex:
        logger.error(f"[SAM Save] Error: {ex}", exc_info=True)
        return jsonify({"success": False, "error": str(ex)}), 500

@app.route("/api/sam/launch", methods=["POST"])
def sam_launch():
    """Deprecated: Legacy launch handler redirects to notification."""
    return jsonify({
        "success": True,
        "message": "Başarımlar artık SteaMRogue içinde doğrudan açılıyor."
    })


_sam_library_cache = {"data": None, "timestamp": 0, "account_id": None}

def get_active_steam_account_id(steam_path: str) -> Optional[str]:
    """Dynamically resolves the 32-bit AccountID of the currently active Steam user on any machine."""
    if not steam_path or not os.path.isdir(steam_path):
        return None

    # 1. Windows Registry (live active Steam process)
    if os.name == 'nt':
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam\ActiveProcess") as key:
                active_user, _ = winreg.QueryValueEx(key, "ActiveUser")
                if active_user and int(active_user) > 0:
                    return str(active_user)
        except Exception:
            pass

    # 2. loginusers.vdf (most recent or highest timestamp user)
    loginusers_path = os.path.join(steam_path, "config", "loginusers.vdf")
    if os.path.exists(loginusers_path):
        try:
            with open(loginusers_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            user_blocks = re.findall(r'"(\d{16,20})"\s*\{([^}]+)\}', content, re.DOTALL)
            best_steamid = None
            highest_ts = -1
            for steamid64_str, body in user_blocks:
                if '"MostRecent"\t\t"1"' in body or '"MostRecent"\t"1"' in body or '"MostRecent" "1"' in body:
                    best_steamid = steamid64_str
                    break
                ts_match = re.search(r'"timestamp"\s+"?(\d+)"?', body)
                if ts_match:
                    ts = int(ts_match.group(1))
                    if ts > highest_ts:
                        highest_ts = ts
                        best_steamid = steamid64_str
            if best_steamid:
                return str(int(best_steamid) - 76561197960265728)
        except Exception:
            pass

    # 3. Fallback: newest modified directory in userdata
    userdata_dir = os.path.join(steam_path, "userdata")
    if os.path.exists(userdata_dir):
        try:
            subdirs = [os.path.join(userdata_dir, d) for d in os.listdir(userdata_dir) if d.isdigit() and int(d) > 0]
            if subdirs:
                subdirs.sort(key=lambda p: os.path.getmtime(p), reverse=True)
                return os.path.basename(subdirs[0])
        except Exception:
            pass

    return None

def extract_games_from_vdf(vdf_path: str) -> set:
    """Parses 'apps' or 'Apps' blocks from localconfig.vdf or sharedconfig.vdf."""
    app_ids = set()
    if not vdf_path or not os.path.exists(vdf_path):
        return app_ids
    try:
        with open(vdf_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        in_apps = False
        depth = 0
        apps_depth = -1
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if "{" in stripped:
                depth += stripped.count("{")
            if "}" in stripped:
                depth -= stripped.count("}")
                if in_apps and depth <= apps_depth:
                    in_apps = False
                    apps_depth = -1
                continue
            m = re.match(r'^"([^"]+)"', stripped)
            if m:
                key = m.group(1)
                if key.lower() == "apps" and not in_apps:
                    in_apps = True
                    apps_depth = depth
                elif in_apps and depth == apps_depth + 1:
                    if key.isdigit() and int(key) > 10:
                        app_ids.add(key)
    except Exception as e:
        logger.warning(f"[SAM Library] Error reading VDF {vdf_path}: {e}")
    return app_ids

def extract_games_from_localconfig(vdf_path: str) -> set:
    return extract_games_from_vdf(vdf_path)

@app.route("/api/sam/games", methods=["GET"])
def sam_games():
    """Returns ALL Steam games owned/played by the currently active Steam user on any machine."""
    global _sam_library_cache
    if not config.steam_path or not os.path.isdir(config.steam_path):
        return jsonify({"success": False, "error": "Steam dizini bulunamadı.", "games": []}), 404

    account_id = get_active_steam_account_id(config.steam_path)
    now = time.time()
    if (
        _sam_library_cache["data"] is not None
        and _sam_library_cache["account_id"] == account_id
        and (now - _sam_library_cache["timestamp"]) < 5.0
    ):
        return jsonify({
            "success": True,
            "account_id": account_id,
            "games": _sam_library_cache["data"],
            "cached": True
        })

    app_ids = set()
    acf_names = {}
    installed_appids = set()

    # 1. Parse localconfig.vdf & sharedconfig.vdf for active user
    userdata_dir = os.path.join(config.steam_path, "userdata")
    accounts_to_check = []
    if account_id:
        accounts_to_check.append(account_id)
    
    # If no account resolved or to ensure zero-loss fallback, also collect all userdata accounts
    if os.path.isdir(userdata_dir):
        try:
            user_dirs = [d for d in os.listdir(userdata_dir) if d.isdigit() and int(d) > 0]
            user_dirs.sort(key=lambda d: os.path.getmtime(os.path.join(userdata_dir, d)), reverse=True)
            for ud in user_dirs:
                if ud not in accounts_to_check:
                    accounts_to_check.append(ud)
        except Exception:
            pass

    # Extract games from userdata configs
    found_from_userdata = False
    for acc in accounts_to_check:
        lc_path = os.path.join(userdata_dir, acc, "config", "localconfig.vdf")
        sc_path = os.path.join(userdata_dir, acc, "7", "remote", "sharedconfig.vdf")
        apps1 = extract_games_from_vdf(lc_path)
        apps2 = extract_games_from_vdf(sc_path)
        if apps1 or apps2:
            app_ids.update(apps1)
            app_ids.update(apps2)
            found_from_userdata = True
            # If we were checking the primary active account and found games, prioritize it
            if acc == account_id:
                break

    # 2. Parse libraryfolders and appmanifest_*.acf (Installed Games on any drive)
    libraries = FileManager.get_library_folders(config.steam_path)
    for _, lib_path in libraries:
        apps_dir = os.path.join(lib_path, "steamapps")
        if not os.path.isdir(apps_dir):
            continue
        try:
            for filename in os.listdir(apps_dir):
                if filename.startswith("appmanifest_") and filename.endswith(".acf"):
                    acf_path = os.path.join(apps_dir, filename)
                    try:
                        with open(acf_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        m_id = RE_ACF_APPID.search(content)
                        if m_id:
                            aid = m_id.group(1)
                            app_ids.add(aid)
                            installed_appids.add(aid)
                            m_name = RE_ACF_NAME.search(content)
                            if m_name:
                                acf_names[aid] = m_name.group(1)
                    except Exception:
                        pass
        except Exception:
            pass

    # 3. Include unlocked AppIDs from stplug-in / lua
    for folder_name in ["stplug-in", "lua"]:
        plugin_folder = os.path.join(config.steam_path, "config", folder_name)
        if os.path.isdir(plugin_folder):
            try:
                for file in os.listdir(plugin_folder):
                    if file.lower().endswith(".lua"):
                        name_part = os.path.splitext(file)[0]
                        if name_part.isdigit():
                            app_ids.add(name_part)
            except Exception:
                pass

    # 4. Merge any games already in main library cache
    if _library_cache.get("data"):
        try:
            for g in _library_cache["data"]:
                gid = str(g.get("appid", ""))
                if gid and gid.isdigit():
                    app_ids.add(gid)
                    if g.get("name") and not gid in acf_names:
                        acf_names[gid] = g["name"]
        except Exception:
            pass

    # Always ensure Spacewar (480) is available for multiplayer / achievement testing
    app_ids.add("480")

    # Name Resolution
    raw_names_cache = get_in_memory_names_cache()
    KNOWN_APP_NAMES = {
        "730": "Counter-Strike 2",
        "440": "Team Fortress 2",
        "550": "Left 4 Dead 2",
        "400": "Portal",
        "620": "Portal 2",
        "480": "Spacewar",
        "4000": "Garry's Mod",
        "218620": "PAYDAY 2",
        "105600": "Terraria",
        "252490": "Rust",
        "271590": "Grand Theft Auto V",
        "227300": "Euro Truck Simulator 2",
        "570": "Dota 2",
        "230410": "Warframe",
        "107410": "Arma 3",
        "289070": "Sid Meier's Civilization VI",
        "359550": "Tom Clancy's Rainbow Six Siege",
        "292030": "The Witcher 3: Wild Hunt",
        "1172470": "Apex Legends",
        "1091500": "Cyberpunk 2077",
        "892970": "Valheim",
        "1245620": "ELDEN RING",
        "236390": "War Thunder",
        "252950": "Rocket League",
        "381210": "Dead by Daylight",
        "1086940": "Baldur's Gate 3",
    }

    FILTER_KEYWORDS = (
        "steamworks common redistributables",
        "steam linux runtime",
        "proton",
        "steamvr",
        "valve test application",
        "dedicated server",
        "compiler",
        "redistributable"
    )

    games_list = []
    appids_to_resolve = []

    for aid in app_ids:
        resolved_name = KNOWN_APP_NAMES.get(aid)
        if not resolved_name:
            acf_cand = acf_names.get(aid)
            if acf_cand and not acf_cand.startswith("appid_") and not acf_cand.startswith("Steam App "):
                resolved_name = acf_cand

        if not resolved_name:
            cached_val = raw_names_cache.get(aid)
            if isinstance(cached_val, dict):
                cand = cached_val.get("name")
                if cand and cand != f"Steam App {aid}":
                    resolved_name = cand
            elif isinstance(cached_val, str) and cached_val != f"Steam App {aid}":
                resolved_name = cached_val

        if not resolved_name:
            resolved_name = f"Steam Oyunu ({aid})"
            appids_to_resolve.append(aid)

        name_lower = resolved_name.lower()
        if any(kw in name_lower for kw in FILTER_KEYWORDS):
            continue

        games_list.append({
            "appid": int(aid) if aid.isdigit() else aid,
            "name": resolved_name,
            "installed": aid in installed_appids
        })

    # Sort installed games first, then alphabetically
    games_list.sort(key=lambda x: (not x["installed"], x["name"].lower()))

    # Trigger background name resolution for any unknown games
    if appids_to_resolve:
        try:
            cache_path = get_cache_path()
            threading.Thread(
                target=resolve_names_in_background,
                args=(appids_to_resolve, cache_path),
                daemon=True
            ).start()
        except Exception:
            pass

    _sam_library_cache["data"] = games_list
    _sam_library_cache["timestamp"] = now
    _sam_library_cache["account_id"] = account_id

    return jsonify({
        "success": True,
        "account_id": account_id,
        "games": games_list,
        "total": len(games_list)
    })

# %%


def is_process_active(pid: int) -> bool:
    if not pid or pid <= 1:
        return False
    if os.name != 'nt':
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False
            
    import ctypes
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    PROCESS_QUERY_INFORMATION = 0x0400
    STILL_ACTIVE = 259
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION | PROCESS_QUERY_INFORMATION, False, pid)
    if not handle:
        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        err = kernel32.GetLastError()
        # If ERROR_ACCESS_DENIED (5), process exists and is active
        if err == 5:
            return True
        return False
    exit_code = ctypes.c_ulong()
    success = kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
    kernel32.CloseHandle(handle)
    return bool(success and (exit_code.value == STILL_ACTIVE))

def parent_monitor_worker():
    try:
        parent_pid = os.getppid()
    except Exception:
        parent_pid = None
        
    if not parent_pid or parent_pid <= 1:
        logger.info("[Watcher] No valid parent PID found. Watchdog disabled.")
        return
        
    logger.info(f"[Watcher] Started monitoring parent process (PID: {parent_pid}).")
    miss_count = 0
    while True:
        time.sleep(3)
        if not is_process_active(parent_pid):
            miss_count += 1
            if miss_count >= 5:
                logger.info(f"[Watcher] Parent process {parent_pid} confirmed terminated (5 consecutive misses). Exiting backend...")
                os._exit(0)
        else:
            miss_count = 0

def background_health_worker():
    """Runs periodic maintenance in the background without lag."""
    # Periodic background maintenance (every 15 minutes)
    while True:
        try:
            time.sleep(900)  # 15 minutes
            if config.steam_path and os.path.isdir(config.steam_path):
                validator.cleanup_steam_crashes(config.steam_path)
                sync_depotcache_manifests(config.steam_path)
        except Exception as ex:
            logger.debug(f"[Background Health] Periodic check warning: {ex}")

def start_server():
    """Starts the Flask server in a local port with automatic zero-config onboarding."""
    # 1. Execute automatic self-healing and zero-config onboarding silently in background on startup
    def first_run_onboarding_worker():
        try:
            logger.info("[Onboarding] Running automatic zero-config self-healing check...")
            heal_res = run_self_healing_routine(force=False)
            logger.info(f"[Onboarding] Self-healing completed: {heal_res.get('actions', [])}")
        except Exception as e:
            logger.warning(f"[Onboarding] Self-healing startup note: {e}")

    onboarding_thread = threading.Thread(target=first_run_onboarding_worker, daemon=True)
    onboarding_thread.start()

    # 2. Periodic background maintenance
    health_thread = threading.Thread(target=background_health_worker, daemon=True)
    health_thread.start()

    # 3. Run startup component checks in background (repos + SteamTools)
    updater.run_startup_checks(config.manifest_repos, config.steam_path)

    
    try:
        from werkzeug.serving import run_simple
        run_simple("127.0.0.1", 65012, app, threaded=True)
    except Exception:
        app.run(host="127.0.0.1", port=65012, debug=False, use_reloader=False)


# %%
if __name__ == "__main__":
    setup_logger()
    logger.info("Starting SteamTools Auto Flask API Server...")
    start_server()
