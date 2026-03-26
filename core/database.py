
import sqlite3
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

class Database:
    """SQLite database handler for stats and settings"""
    
    def __init__(self, db_path: str = "data/database.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self) -> None:
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Command usage statistics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS command_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id TEXT,
                user_id TEXT,
                command_name TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Guild logging settings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS guild_logging (
                guild_id TEXT PRIMARY KEY,
                enabled BOOLEAN DEFAULT 0,
                log_events TEXT DEFAULT '[]',
                webhook_url TEXT,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # User settings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id TEXT PRIMARY KEY,
                preferred_mode TEXT DEFAULT 'nsfw',
                last_used DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # API cache
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_cache (
                cache_key TEXT PRIMARY KEY,
                data TEXT,
                expires DATETIME
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def log_command(self, guild_id: str, user_id: str, command_name: str) -> None:
        """Log a command usage"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO command_stats (guild_id, user_id, command_name)
            VALUES (?, ?, ?)
        ''', (str(guild_id), str(user_id), command_name))
        
        conn.commit()
        conn.close()
    
    def get_command_stats(self, guild_id: Optional[str] = None, 
                         limit: int = 100) -> List[Dict[str, Any]]:
        """Get command statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if guild_id:
            cursor.execute('''
                SELECT command_name, COUNT(*) as count
                FROM command_stats
                WHERE guild_id = ?
                GROUP BY command_name
                ORDER BY count DESC
                LIMIT ?
            ''', (str(guild_id), limit))
        else:
            cursor.execute('''
                SELECT command_name, COUNT(*) as count
                FROM command_stats
                GROUP BY command_name
                ORDER BY count DESC
                LIMIT ?
            ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_guild_logging(self, guild_id: str) -> Optional[Dict[str, Any]]:
        """Get guild logging settings"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM guild_logging WHERE guild_id = ?
        ''', (str(guild_id),))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            data = dict(row)
            # Parse JSON array
            if data.get('log_events'):
                try:
                    data['log_events'] = json.loads(data['log_events'])
                except:
                    data['log_events'] = []
            else:
                data['log_events'] = []
            return data
        return None
    
    def set_guild_logging(self, guild_id: str, enabled: bool, 
                         log_events: List[str], webhook_url: Optional[str] = None) -> None:
        """Set guild logging settings"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO guild_logging 
            (guild_id, enabled, log_events, webhook_url, last_updated)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (str(guild_id), enabled, json.dumps(log_events), webhook_url))
        
        conn.commit()
        conn.close()
    
    def disable_guild_logging(self, guild_id: str) -> None:
        """Disable logging for a guild"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE guild_logging 
            SET enabled = 0, last_updated = CURRENT_TIMESTAMP
            WHERE guild_id = ?
        ''', (str(guild_id),))
        
        conn.commit()
        conn.close()
    
    def get_cache(self, cache_key: str) -> Optional[Any]:
        """Get cached data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT data, expires FROM api_cache 
            WHERE cache_key = ? AND expires > datetime('now')
        ''', (cache_key,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            try:
                return json.loads(row['data'])
            except:
                return None
        return None
    
    def set_cache(self, cache_key: str, data: Any, ttl_seconds: int = 3600) -> None:
        """Set cached data with TTL"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        expires = datetime.now().timestamp() + ttl_seconds
        expires_dt = datetime.fromtimestamp(expires).isoformat()
        
        cursor.execute('''
            INSERT OR REPLACE INTO api_cache (cache_key, data, expires)
            VALUES (?, ?, ?)
        ''', (cache_key, json.dumps(data), expires_dt))
        
        conn.commit()
        conn.close()

database = Database()
