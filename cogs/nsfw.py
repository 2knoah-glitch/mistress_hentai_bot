
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, List
import random

from core.api_client import api_client
from core.database import database
from core.permissions import nsfw_channel_only
from utils.embeds import create_nsfw_embed, create_error_embed, create_info_embed
from utils.paginator import PaginatorView, create_mass_nsfw_embeds
from utils.converters import TagListConverter
from core.config_manager import config_manager

class NSFW(commands.Cog):
    """NSFW image commands"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = config_manager
    
    @app_commands.command(name="loli", description="Fetch loli content")
    @app_commands.describe(mode="SFW or NSFW mode")
    @app_commands.choices(mode=[
        app_commands.Choice(name="sfw", value="sfw"),
        app_commands.Choice(name="nsfw", value="nsfw")
    ])
    @nsfw_channel_only()
    async def loli(self, interaction: discord.Interaction, mode: str = "nsfw"):
        """Fetch loli image"""
        await self.handle_nsfw_command(interaction, "loli", mode)
    
    @app_commands.command(name="shotacon", description="Fetch shotacon content")
    @app_commands.describe(mode="SFW or NSFW mode")
    @app_commands.choices(mode=[
        app_commands.Choice(name="sfw", value="sfw"),
        app_commands.Choice(name="nsfw", value="nsfw")
    ])
    @nsfw_channel_only()
    async def shotacon(self, interaction: discord.Interaction, mode: str = "nsfw"):
        """Fetch shotacon image"""
        await self.handle_nsfw_command(interaction, "shotacon", mode)
    
    @app_commands.command(name="yaoi", description="Fetch yaoi content")
    @app_commands.describe(mode="SFW or NSFW mode")
    @app_commands.choices(mode=[
        app_commands.Choice(name="sfw", value="sfw"),
        app_commands.Choice(name="nsfw", value="nsfw")
    ])
    @nsfw_channel_only()
    async def yaoi(self, interaction: discord.Interaction, mode: str = "nsfw"):
        """Fetch yaoi image"""
        await self.handle_nsfw_command(interaction, "yaoi", mode)
    
    @app_commands.command(name="yuri", description="Fetch yuri content")
    @app_commands.describe(mode="SFW or NSFW mode")
    @app_commands.choices(mode=[
        app_commands.Choice(name="sfw", value="sfw"),
        app_commands.Choice(name="nsfw", value="nsfw")
    ])
    @nsfw_channel_only()
    async def yuri(self, interaction: discord.Interaction, mode: str = "nsfw"):
        """Fetch yuri image"""
        await self.handle_nsfw_command(interaction, "yuri", mode)
    
    @app_commands.command(name="hentai", description="Fetch hentai content")
    @app_commands.describe(mode="SFW or NSFW mode")
    @app_commands.choices(mode=[
        app_commands.Choice(name="sfw", value="sfw"),
        app_commands.Choice(name="nsfw", value="nsfw")
    ])
    @nsfw_channel_only()
    async def hentai(self, interaction: discord.Interaction, mode: str = "nsfw"):
        """Fetch hentai image"""
        await self.handle_nsfw_command(interaction, "hentai", mode)
    
    async def handle_nsfw_command(self, interaction: discord.Interaction, category: str, mode: str):
        """Handle NSFW command logic"""
        await interaction.response.defer()
        
        # Log command usage
        if interaction.guild:
            database.log_command(str(interaction.guild.id), str(interaction.user.id), category)
        
        # Get tags from mapping
        tag_mappings = self.config.get("tag_mappings", {})
        base_tags = tag_mappings.get(category, category)
        
        # Add rating for SFW mode
        if mode == "sfw":
            tags = f"{base_tags} rating:general"
        else:
            tags = base_tags
        
        # Fetch image
        images = await api_client.fetch_image(tags, mode, limit=1)
        
        if images and len(images) > 0:
            image_data = images[0]
            embed = create_nsfw_embed(image_data, category)
            await interaction.followup.send(embed=embed)
        else:
            # Try fallback
            fallback_url = api_client.get_fallback_image(category)
            if fallback_url:
                embed = create_nsfw_embed(
                    {"file_url": fallback_url, "source": "Fallback", "tags": category},
                    category
                )
                embed.set_footer(text="Your Mistress Bot • Fallback Image")
                await interaction.followup.send(embed=embed)
            else:
                embed = create_error_embed(f"No {category} images found. Try again later.")
                await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="massloli", description="Fetch 10 loli images")
    @app_commands.describe(mode="SFW or NSFW mode")
    @app_commands.choices(mode=[
        app_commands.Choice(name="sfw", value="sfw"),
        app_commands.Choice(name="nsfw", value="nsfw")
    ])
    @nsfw_channel_only()
    async def massloli(self, interaction: discord.Interaction, mode: str = "nsfw"):
        """Fetch multiple loli images"""
        await self.handle_mass_nsfw_command(interaction, "loli", mode, 10)
    
    @app_commands.command(name="massshotacon", description="Fetch 10 shotacon images")
    @app_commands.describe(mode="SFW or NSFW mode")
    @app_commands.choices(mode=[
        app_commands.Choice(name="sfw", value="sfw"),
        app_commands.Choice(name="nsfw", value="nsfw")
    ])
    @nsfw_channel_only()
    async def massshotacon(self, interaction: discord.Interaction, mode: str = "nsfw"):
        """Fetch multiple shotacon images"""
        await self.handle_mass_nsfw_command(interaction, "shotacon", mode, 10)
    
    @app_commands.command(name="massyaoi", description="Fetch 10 yaoi images")
    @app_commands.describe(mode="SFW or NSFW mode")
    @app_commands.choices(mode=[
        app_commands.Choice(name="sfw", value="sfw"),
        app_commands.Choice(name="nsfw", value="nsfw")
    ])
    @nsfw_channel_only()
    async def massyaoi(self, interaction: discord.Interaction, mode: str = "nsfw"):
        """Fetch multiple yaoi images"""
        await self.handle_mass_nsfw_command(interaction, "yaoi", mode, 10)
    
    @app_commands.command(name="massyuri", description="Fetch 10 yuri images")
    @app_commands.describe(mode="SFW or NSFW mode")
    @app_commands.choices(mode=[
        app_commands.Choice(name="sfw", value="sfw"),
        app_commands.Choice(name="nsfw", value="nsfw")
    ])
    @nsfw_channel_only()
    async def massyuri(self, interaction: discord.Interaction, mode: str = "nsfw"):
        """Fetch multiple yuri images"""
        await self.handle_mass_nsfw_command(interaction, "yuri", mode, 10)
    
    @app_commands.command(name="masshentai", description="Fetch 10 hentai images")
    @app_commands.describe(mode="SFW or NSFW mode")
    @app_commands.choices(mode=[
        app_commands.Choice(name="sfw", value="sfw"),
        app_commands.Choice(name="nsfw", value="nsfw")
    ])
    @nsfw_channel_only()
    async def masshentai(self, interaction: discord.Interaction, mode: str = "nsfw"):
        """Fetch multiple hentai images"""
        await self.handle_mass_nsfw_command(interaction, "hentai", mode, 10)
    
    async def handle_mass_nsfw_command(self, interaction: discord.Interaction, category: str, mode: str, count: int):
        """Handle mass NSFW command logic"""
        await interaction.response.defer()
        
        # Log command usage
        if interaction.guild:
            database.log_command(str(interaction.guild.id), str(interaction.user.id), f"mass{category}")
        
        # Get tags from mapping
        tag_mappings = self.config.get("tag_mappings", {})
        base_tags = tag_mappings.get(category, category)
        
        # Add rating for SFW mode
        if mode == "sfw":
            tags = f"{base_tags} rating:general"
        else:
            tags = base_tags
        
        # Fetch images
        images = await api_client.fetch_image(tags, mode, limit=count)
        
        if images and len(images) > 0:
            # Create embeds
            embeds = create_mass_nsfw_embeds(images, category)
            
            # Send first embed with paginator
            view = PaginatorView(embeds)
            await interaction.followup.send(embed=embeds[0], view=view)
        else:
            embed = create_error_embed(f"No {category} images found. Try again later.")
            await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="search", description="Search specific tags across multiple sites")
    @app_commands.describe(
        tags="Tags to search for (comma or space separated)",
        mode="SFW or NSFW mode",
        limit="Number of results (1-10)"
    )
    @app_commands.choices(mode=[
        app_commands.Choice(name="sfw", value="sfw"),
        app_commands.Choice(name="nsfw", value="nsfw")
    ])
    @nsfw_channel_only()
    async def search(
        self, 
        interaction: discord.Interaction, 
        tags: str,
        mode: str = "nsfw",
        limit: app_commands.Range[int, 1, 10] = 5
    ):
        """Search for images with specific tags"""
        await interaction.response.defer()
        
        # Log command usage
        if interaction.guild:
            database.log_command(str(interaction.guild.id), str(interaction.user.id), "search")
        
        # Fetch images
        images = await api_client.fetch_image(tags, mode, limit=limit)
        
        if images and len(images) > 0:
            if limit == 1:
                # Single result
                embed = create_nsfw_embed(images[0], "Search Result")
                embed.title = f"Search: {tags[:50]}"
                await interaction.followup.send(embed=embed)
            else:
                # Multiple results with paginator
                embeds = create_mass_nsfw_embeds(images, f"Search: {tags[:30]}")
                view = PaginatorView(embeds)
                await interaction.followup.send(embed=embeds[0], view=view)
        else:
            embed = create_error_embed(f"No results found for tags: {tags}")
            await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    """Setup the cog"""
    await bot.add_cog(NSFW(bot))
