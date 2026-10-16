# %% [markdown]
# # Steam API Module
# Interacts with the official Steam Web API to fetch app metadata.

# %%
import requests
from typing import Optional, Dict, Any
from logger import logger

# %%
class SteamAPI:
    """Client for fetching game information from the official Steam Store API."""
    
    BASE_URL = "https://store.steampowered.com/api/appdetails"
    
    @classmethod
    def get_app_details(cls, appid: str) -> Optional[Dict[str, Any]]:
        """Fetches application information from the Steam Store API.
        
        Returns:
            Dict containing name, type, image, description, metacritic score, and required_age, 
            or None if the app is invalid/not found.
        """
        params = {"appids": appid, "l": "english"}
        try:
            logger.debug(f"Querying Steam Store API for AppID: {appid}")
            # Use a realistic User-Agent to avoid issues
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            
            cookies = {"birthtime": "0", "mature_content": "1"}
            
            try:
                response = requests.get(cls.BASE_URL, params=params, headers=headers, cookies=cookies, timeout=10)
            except requests.exceptions.SSLError:
                logger.debug("SSL verification failed; retrying without verification.")
                response = requests.get(cls.BASE_URL, params=params, headers=headers, cookies=cookies, timeout=10, verify=False)
            
            if response.status_code != 200:
                logger.error(f"Steam API returned HTTP status {response.status_code}")
                return None
                
            data = response.json()
            if not data or not isinstance(data, dict):
                return None
                
            entry = data.get(appid)
            if not entry or not entry.get("success"):
                for k, v in data.items():
                    if isinstance(v, dict) and v.get("success"):
                        entry = v
                        break
                        
            if not entry or not entry.get("success") or "data" not in entry:
                logger.warning(f"Steam API returned success=false or no data for AppID: {appid}")
                return None
                
            app_data = entry["data"]
            
            # Extract relevant fields
            metadata = {
                "name": app_data.get("name", "Unknown Game"),
                "type": app_data.get("type", "game"),
                "header_image": app_data.get("header_image", ""),
                "short_description": app_data.get("short_description", ""),
                "metacritic_score": app_data.get("metacritic", {}).get("score"),
                "required_age": app_data.get("required_age", 0),
                "is_free": app_data.get("is_free", False)
            }
            
            logger.info(f"Successfully retrieved Steam metadata for: {metadata['name']}")
            return metadata
            
        except requests.RequestException as e:
            logger.error(f"Connection error requesting Steam details for AppID {appid}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error parsing Steam API response: {e}")
            return None

    @classmethod
    def search_store(cls, query: str) -> list:
        """Searches Steam store for games matching query string.
        
        Returns:
            List of dicts containing name, id, and tiny_image.
        """
        search_url = "https://store.steampowered.com/api/storesearch/"
        params = {"term": query, "l": "english", "cc": "US"}
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            try:
                response = requests.get(search_url, params=params, headers=headers, timeout=8)
            except requests.exceptions.SSLError:
                response = requests.get(search_url, params=params, headers=headers, timeout=8, verify=False)
                
            if response.status_code != 200:
                return []
                
            data = response.json()
            items = data.get("items", [])
            results = []
            for item in items:
                results.append({
                    "id": str(item.get("id")),
                    "name": item.get("name", ""),
                    "tiny_image": item.get("tiny_image", "")
                })
            return results
        except Exception as e:
            logger.error(f"Search API error for query '{query}': {e}")
            return []

# %%
if __name__ == "__main__":
    # Small test cell
    test_id = "730"  # CS2
    details = SteamAPI.get_app_details(test_id)
    print("Test details:", details)
