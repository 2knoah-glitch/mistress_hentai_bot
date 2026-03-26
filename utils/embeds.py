
import discord
from datetime import datetime
from typing import Optional, List, Dict, Any
from core.config_manager import config_manager

def create_embed(
    title: str = "",
    description: str = "",
    color: Optional[int] = None,
    fields: List[Dict[str, str]] = None,
    image_url: Optional[str] = None,
    thumbnail_url: Optional[str] = None,
    footer_text: Optional[str] = None,
    author_name: Optional[str] = None,
    url: Optional[str] = None,
    timestamp: Optional[datetime] = None
) -> discord.Embed:
    """Create a standardized embed"""
    if color is None:
        color = config_manager.get("default_color", 0xFF69B4)
    
    embed = discord.Embed(
        title=title[:256],  # Discord limit
        description=description[:4096],  # Discord limit
        color=color,
        url=url,
        timestamp=timestamp or datetime.utcnow()
    )
    
    # Add fields
    if fields:
        for field in fields:
            name = field.get("name", "")[:256]
            value = field.get("value", "")[:1024]
            inline = field.get("inline", False)
            embed.add_field(name=name, value=value, inline=inline)
    
    # Add image
    if image_url:
        embed.set_image(url=image_url)
    
    # Add thumbnail
    if thumbnail_url:
        embed.set_thumbnail(url=thumbnail_url)
    
    # Add footer
    if footer_text:
        embed.set_footer(text=footer_text[:2048])
    
    # Add author (if not disabled per user request)
    if author_name:
        embed.set_author(name=author_name[:256])
    
    return embed

def create_error_embed(message: str) -> discord.Embed:
    """Create an error embed"""
    return create_embed(
        title="❌ Error",
        description=message,
        color=config_manager.get("error_color", 0xFF0000)
    )

def create_success_embed(message: str) -> discord.Embed:
    """Create a success embed"""
    return create_embed(
        title="✅ Success",
        description=message,
        color=config_manager.get("success_color", 0x00FF00)
    )

def create_info_embed(title: str, message: str) -> discord.Embed:
    """Create an info embed"""
    return create_embed(
        title=title,
        description=message,
        color=config_manager.get("log_color", 0x7289DA)
    )

def create_nsfw_embed(image_data: Dict[str, Any], category: str) -> discord.Embed:
    """Create an NSFW image embed"""
    tags = image_data.get("tags", "")
    if len(tags) > 500:
        tags = tags[:497] + "..."
    
    embed = create_embed(
        title=f"{category.capitalize()} Image",
        color=config_manager.get("default_color", 0xFF69B4),
        image_url=image_data.get("file_url", "")
    )
    
    if tags:
        embed.add_field(name="Tags", value=tags[:1024], inline=False)
    
    if image_data.get("source"):
        embed.add_field(name="Source", value=image_data["source"], inline=True)
    
    if image_data.get("rating"):
        embed.add_field(name="Rating", value=image_data["rating"].upper(), inline=True)
    
    if image_data.get("score"):
        embed.add_field(name="Score", value=str(image_data["score"]), inline=True)
    
    embed.set_footer(text="Your Mistress Bot • Use /help for more commands")
    
    return embed
