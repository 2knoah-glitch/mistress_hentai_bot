
import aiohttp
import asyncio
import random
from typing import Dict, List, Optional, Any
from core.config_manager import config_manager

class APIClient:
    """Handles API requests to image sources"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.request_delay = config_manager.get("request_delay", 2.0)
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        ]
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={"User-Agent": random.choice(self.user_agents)}
            )
        return self.session
    
    async def close(self) -> None:
        """Close the session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def fetch_from_api(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Fetch data from API endpoint"""
        await asyncio.sleep(self.request_delay)  # Rate limiting
        
        try:
            session = await self.get_session()
            async with session.get(endpoint, params=params, timeout=30) as response:
                if response.status == 200:
                    content_type = response.headers.get('Content-Type', '')
                    if 'application/json' in content_type:
                        return await response.json()
                    else:
                        text = await response.text()
                        # Try to parse as JSON anyway (some APIs don't set content-type)
                        try:
                            import json
                            return json.loads(text)
                        except:
                            return {"text": text}
                else:
                    print(f"API request failed: {response.status} {endpoint}")
                    return None
        except Exception as e:
            print(f"API request error: {e}")
            return None
    
    async def fetch_image(self, tags: str, mode: str = "nsfw", limit: int = 1) -> List[Dict[str, Any]]:
        """Fetch images based on tags and mode"""
        endpoints = config_manager.get("api_endpoints", {})
        results = []
        
        # Determine which APIs to use based on mode
        if mode == "sfw":
            api_priority = ["safebooru", "danbooru", "nekos_life"]
        else:
            api_priority = ["danbooru", "gelbooru", "nekos_life_lewd"]
        
        for api_name in api_priority:
            if api_name not in endpoints:
                continue
                
            endpoint = endpoints[api_name]
            
            # Format endpoint with parameters
            if api_name == "nekos_life" or api_name == "nekos_life_lewd":
                # Nekos.life doesn't use tags
                params = None
            else:
                # Booru-style APIs
                formatted_tags = tags.replace(" ", "+")
                endpoint = endpoint.format(tags=formatted_tags, limit=limit, page=0)
                params = None
                
                # Add API credentials if available
                if api_name == "danbooru":
                    api_key = config_manager.get_env("DANBOORU_API_KEY")
                    username = config_manager.get_env("DANBOORU_USERNAME")
                    if api_key and username:
                        params = {"login": username, "api_key": api_key}
                elif api_name == "gelbooru":
                    api_key = config_manager.get_env("GELBOORU_API_KEY")
                    user_id = config_manager.get_env("GELBOORU_USER_ID")
                    if api_key and user_id:
                        params = {"api_key": api_key, "user_id": user_id}
            
            data = await self.fetch_from_api(endpoint, params)
            
            if data:
                # Parse response based on API
                if api_name.startswith("nekos_life"):
                    if isinstance(data, dict) and "url" in data:
                        results.append({
                            "file_url": data["url"],
                            "source": "Nekos.life",
                            "tags": tags
                        })
                elif api_name in ["safebooru", "gelbooru"]:
                    if isinstance(data, dict) and "post" in data:
                        posts = data["post"]
                    else:
                        posts = data
                    
                    if posts and len(posts) > 0:
                        for post in posts[:limit]:
                            if isinstance(post, dict):
                                results.append({
                                    "file_url": post.get("file_url", post.get("sample_url", "")),
                                    "source": api_name.capitalize(),
                                    "tags": post.get("tags", ""),
                                    "rating": post.get("rating", ""),
                                    "score": post.get("score", 0)
                                })
                elif api_name == "danbooru":
                    if isinstance(data, list) and len(data) > 0:
                        for post in data[:limit]:
                            results.append({
                                "file_url": post.get("file_url", post.get("large_file_url", "")),
                                "source": "Danbooru",
                                "tags": post.get("tag_string", ""),
                                "rating": post.get("rating", ""),
                                "score": post.get("score", 0)
                            })
                
                if results:
                    break
        
        return results
    
    def get_fallback_image(self, category: str) -> Optional[str]:
        """Get a fallback image URL for a category"""
        fallbacks = config_manager.get("fallback_image_urls", {})
        category_fallbacks = fallbacks.get(category, [])
        
        if category_fallbacks:
            return random.choice(category_fallbacks)
        return None

api_client = APIClient()
