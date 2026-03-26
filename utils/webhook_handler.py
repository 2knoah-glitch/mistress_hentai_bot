
import discord
import aiohttp
from typing import Optional, Dict, Any
from core.config_manager import config_manager
from utils.embeds import create_embed

class WebhookHandler:
    """Handle Discord webhook operations"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self) -> None:
        """Close the session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def send_webhook(
        self, 
        webhook_url: str, 
        content: Optional[str] = None,
        embed: Optional[discord.Embed] = None,
        embeds: Optional[list] = None,
        username: Optional[str] = None,
        avatar_url: Optional[str] = None
    ) -> bool:
        """Send a message to a webhook"""
        try:
            session = await self.get_session()
            
            payload = {}
            if content:
                payload["content"] = content[:2000]  # Discord limit
            
            if embed:
                payload["embeds"] = [embed.to_dict()]
            elif embeds:
                payload["embeds"] = [e.to_dict() for e in embeds[:10]]  # Discord limit
            
            if username:
                payload["username"] = username[:80]
            
            if avatar_url:
                payload["avatar_url"] = avatar_url
            
            async with session.post(webhook_url, json=payload) as response:
                return response.status == 204 or response.status == 200
        
        except Exception as e:
            print(f"Webhook error: {e}")
            return False
    
    async def send_log(
        self,
        event_type: str,
        guild: discord.Guild,
        data: Dict[str, Any],
        webhook_url: Optional[str] = None
    ) -> bool:
        """Send a log message to webhook"""
        if not webhook_url:
            webhook_url = config_manager.get_env("LOG_WEBHOOK_URL")
        
        if not webhook_url:
            return False
        
        # Create log embed based on event type
        embed = self.create_log_embed(event_type, guild, data)
        
        return await self.send_webhook(
            webhook_url,
            embed=embed,
            username=f"{guild.name} Logs",
            avatar_url=guild.icon.url if guild.icon else None
        )
    
    def create_log_embed(self, event_type: str, guild: discord.Guild, data: Dict[str, Any]) -> discord.Embed:
        """Create a log embed for an event"""
        color = config_manager.get("log_color", 0x7289DA)
        
        # Map event types to titles and colors
        event_titles = {
            "message_delete": "🗑️ Message Deleted",
            "message_edit": "✏️ Message Edited",
            "member_join": "👤 Member Joined",
            "member_leave": "👤 Member Left",
            "member_ban": "🔨 Member Banned",
            "member_unban": "🔓 Member Unbanned",
            "member_kick": "👢 Member Kicked",
            "channel_create": "📁 Channel Created",
            "channel_delete": "📁 Channel Deleted",
            "role_create": "🎭 Role Created",
            "role_delete": "🎭 Role Deleted",
            "command_used": "⚙️ Command Used"
        }
        
        title = event_titles.get(event_type, f"📝 {event_type.replace('_', ' ').title()}")
        
        embed = create_embed(
            title=title,
            color=color,
            timestamp=data.get("timestamp")
        )
        
        # Add fields based on event type
        if "user" in data:
            embed.add_field(name="User", value=f"{data['user']} ({data.get('user_id', 'N/A')})", inline=False)
        
        if "moderator" in data:
            embed.add_field(name="Moderator", value=data["moderator"], inline=False)
        
        if "reason" in data:
            embed.add_field(name="Reason", value=data["reason"] or "No reason provided", inline=False)
        
        if "channel" in data:
            embed.add_field(name="Channel", value=data["channel"], inline=True)
        
        if "before" in data and "after" in data:
            embed.add_field(name="Before", value=data["before"][:500], inline=False)
            embed.add_field(name="After", value=data["after"][:500], inline=False)
        elif "content" in data:
            embed.add_field(name="Content", value=data["content"][:1000], inline=False)
        
        if "command" in data:
            embed.add_field(name="Command", value=data["command"], inline=True)
        
        embed.set_footer(text=f"Guild ID: {guild.id} • Event: {event_type}")
        
        return embed

webhook_handler = WebhookHandler()
