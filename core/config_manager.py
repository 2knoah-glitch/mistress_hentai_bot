
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dotenv import load_dotenv

class ConfigManager:
    """Manages configuration loading from environment variables and files"""
    
    def __init__(self, config_path: str = "data/config.json"):
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.load_dotenv()
        self.load_config()
        self.validate_config()
    
    def load_dotenv(self) -> None:
        """Load environment variables from .env file"""
        load_dotenv()
    
    def load_config(self) -> None:
        """Load configuration from JSON file and merge with environment variables"""
        # Load from JSON file first
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
                self.config.update(file_config)
        except FileNotFoundError:
            print(f"Config file not found at {self.config_path}. Using environment variables only.")
        except json.JSONDecodeError as e:
            print(f"Error parsing config file: {e}. Using environment variables only.")
        
        # Override with environment variables
        self.load_from_env()
    
    def load_from_env(self) -> None:
        """Load configuration from environment variables"""
        # Bot authentication
        self.config["discord_token"] = os.getenv("DISCORD_TOKEN", "")
        self.config["client_id"] = os.getenv("CLIENT_ID", "")
        
        # Bot metadata
        self.config["bot_name"] = os.getenv("BOT_NAME", "Lust Mommy")
        
        # Role and user IDs (parse comma-separated strings)
        self.config["high_roles"] = self.parse_id_list(os.getenv("HIGH_ROLES", ""))
        self.config["super_admins"] = self.parse_id_list(os.getenv("SUPER_ADMINS", ""))
        
        # Channel IDs
        self.config["nsfw_channels"] = self.parse_id_list(os.getenv("NSFW_CHANNELS", ""))
        self.config["log_channel"] = self.parse_single_id(os.getenv("LOG_CHANNEL", ""))
        
        # Webhook URLs
        self.config["webhook_log_url"] = os.getenv("WEBHOOK_LOG_URL", "")
        
        # API endpoints (from file or defaults)
        if "api_endpoints" not in self.config:
            self.config["api_endpoints"] = {
                "safebooru": "https://safebooru.org/index.php?page=dapi&s=post&q=index&json=1&tags={tags}&limit={limit}",
                "danbooru": "https://danbooru.donmai.us/posts.json?tags={tags}&limit={limit}",
                "gelbooru": "https://gelbooru.com/index.php?page=dapi&s=post&q=index&json=1&tags={tags}&limit={limit}&pid={page}",
                "nekos_life": "https://nekos.life/api/v2/img/neko",
                "nekos_life_lewd": "https://nekos.life/api/v2/img/lewd"
            }
        
        # Tag mappings (from file or defaults)
        if "tag_mappings" not in self.config:
            self.config["tag_mappings"] = {
                "loli": "loli",
                "shotacon": "shotacon",
                "yaoi": "yaoi",
                "yuri": "yuri",
                "hentai": "rating:explicit"
            }
        
        # Other defaults
        defaults = {
            "request_delay": 2.0,
            "mass_action_batch_size": 5,
            "max_search_results": 10,
            "default_color": 0xFF69B4,
            "error_color": 0xFF0000,
            "success_color": 0x00FF00,
            "log_color": 0x7289DA,
            "bot_status": "Watching your commands | /help"
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def parse_id_list(self, env_string: str) -> List[int]:
        """Parse comma-separated string of IDs into list of integers"""
        if not env_string:
            return []
        
        ids = []
        for id_str in env_string.split(','):
            id_str = id_str.strip()
            if id_str.isdigit():
                ids.append(int(id_str))
        
        return ids
    
    def parse_single_id(self, env_string: str) -> Optional[int]:
        """Parse single ID string into integer"""
        if not env_string or not env_string.strip().isdigit():
            return None
        return int(env_string.strip())
    
    def validate_config(self) -> None:
        """Validate critical configuration values"""
        if not self.config.get("discord_token"):
            raise ValueError("DISCORD_TOKEN is required in environment variables")
        
        if not self.config.get("client_id"):
            print("Warning: CLIENT_ID not set. Some features may not work properly.")
    
    def save_config(self) -> None:
        """Save configuration to JSON file (for non-sensitive settings)"""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        # Don't save sensitive env vars to file
        safe_config = self.config.copy()
        sensitive_keys = ["discord_token", "webhook_log_url"]
        for key in sensitive_keys:
            if key in safe_config:
                del safe_config[key]
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(safe_config, f, indent=2)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value (saves to file for non-sensitive values)"""
        self.config[key] = value
        
        # Don't save sensitive values to file
        sensitive_keys = ["discord_token", "webhook_log_url"]
        if key not in sensitive_keys:
            self.save_config()
    
    def get_env(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get environment variable directly"""
        return os.getenv(key, default)

config_manager = ConfigManager()
