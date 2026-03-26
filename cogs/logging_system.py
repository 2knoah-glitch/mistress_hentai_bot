
import discord
from discord import app_commands
from discord.ext import commands
from typing import List, Optional

from core.database import database
from core.permissions import is_high_role, log_channel_only
from utils.embeds import create_success_embed, create_error_embed, create_info_embed
from utils.webhook_handler import webhook_handler
from core.config_manager import config_manager

class LoggingSystem(commands.Cog):
    """Logging system for server events"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = config_manager
        
        # Available log events
        self.available_events = [
            "message_delete",
            "message_edit",
            "member_join",
            "member_leave",
            "member_ban",
            "member_unban",
            "member_kick",
            "channel_create",
            "channel_delete",
            "role_create",
            "role_delete"
        ]
    
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        """Log message deletion"""
        if not message.guild or message.author.bot:
            return
        
        settings = database.get_guild_logging(str(message.guild.id))
        if not settings or not settings.get("enabled") or "message_delete" not in settings.get("log_events", []):
            return
        
        # Get webhook URL from database, env, or use default
        webhook_url = settings.get("webhook_url") or config_manager.get("webhook_log_url")
        if not webhook_url:
            return
        
        await webhook_handler.send_log(
            "message_delete",
            message.guild,
            {
                "user": f"{message.author} ({message.author.id})",
                "channel": message.channel.mention,
                "content": message.content or "*No text content*",
                "attachments": len(message.attachments),
                "timestamp": discord.utils.utcnow()
            },
            webhook_url
        )
    
    # ... [other event listeners remain the same, just update webhook_url fetching]
    
    @app_commands.command(name="log", description="Configure logging for this server")
    @app_commands.describe(webhook_url="Custom webhook URL (optional)")
    @is_high_role()
    @log_channel_only()
    async def log(self, interaction: discord.Interaction, webhook_url: Optional[str] = None):
        """Configure logging settings"""
        # Use provided webhook, env webhook, or database webhook
        final_webhook_url = webhook_url or config_manager.get("webhook_log_url")
        
        if not final_webhook_url:
            embed = create_error_embed(
                "No webhook URL provided. "
                "Set WEBHOOK_LOG_URL in .env or provide one with this command."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Create select menu for events
        class LogEventSelect(discord.ui.Select):
            def __init__(self, available_events: List[str], current_events: List[str], webhook_url: str):
                options = []
                for event in available_events:
                    option = discord.SelectOption(
                        label=event.replace("_", " ").title(),
                        value=event,
                        default=event in current_events,
                        description=f"Log {event.replace('_', ' ')} events"
                    )
                    options.append(option)
                
                super().__init__(
                    placeholder="Select events to log...",
                    min_values=0,
                    max_values=len(available_events),
                    options=options
                )
                self.webhook_url = webhook_url
            
            async def callback(self, select_interaction: discord.Interaction):
                if select_interaction.user != interaction.user:
                    await select_interaction.response.send_message("This is not your menu.", ephemeral=True)
                    return
                
                # Save selected events with webhook URL
                database.set_guild_logging(
                    str(interaction.guild.id),
                    True,
                    self.values,
                    self.webhook_url
                )
                
                embed = create_success_embed("Logging Configured")
                embed.add_field(
                    name="Webhook",
                    value=f"`{self.webhook_url[:50]}...`" if len(self.webhook_url) > 50 else f"`{self.webhook_url}`",
                    inline=False
                )
                embed.add_field(
                    name="Enabled Events",
                    value="\n".join([f"• {e.replace('_', ' ').title()}" for e in self.values]) or "None",
                    inline=False
                )
                
                await select_interaction.response.edit_message(embed=embed, view=None)
                
                # Log command usage
                database.log_command(str(interaction.guild.id), str(interaction.user.id), "log")
        
        class LogView(discord.ui.View):
            def __init__(self, available_events: List[str], current_events: List[str], webhook_url: str):
                super().__init__(timeout=180)
                self.add_item(LogEventSelect(available_events, current_events, webhook_url))
        
        # Get current settings
        current_settings = database.get_guild_logging(str(interaction.guild.id))
        current_events = current_settings.get("log_events", []) if current_settings else []
        
        embed = create_info_embed(
            "Logging Configuration",
            "Select which events you want to log. "
            f"Logs will be sent to the configured webhook."
        )
        
        if current_events:
            embed.add_field(
                name="Currently Logging",
                value="\n".join([f"• {e.replace('_', ' ').title()}" for e in current_events]),
                inline=False
            )
        
        view = LogView(self.available_events, current_events, final_webhook_url)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @app_commands.command(name="stopalllogs", description="Disable all logging for this server")
    @is_high_role()
    @log_channel_only()
    async def stopalllogs(self, interaction: discord.Interaction):
        """Disable all logging"""
        database.disable_guild_logging(str(interaction.guild.id))
        
        embed = create_success_embed("All logging has been disabled for this server.")
        await interaction.response.send_message(embed=embed)
        
        # Log command usage
        database.log_command(str(interaction.guild.id), str(interaction.user.id), "stopalllogs")
    
    @app_commands.command(name="stopselectedlogs", description="Disable specific log events")
    @is_high_role()
    @log_channel_only()
    async def stopselectedlogs(self, interaction: discord.Interaction):
        """Disable specific log events"""
        # Create select menu for events to disable
        class DisableEventSelect(discord.ui.Select):
            def __init__(self, current_events: List[str]):
                options = []
                for event in current_events:
                    option = discord.SelectOption(
                        label=event.replace("_", " ").title(),
                        value=event,
                        description=f"Stop logging {event.replace('_', ' ')} events"
                    )
                    options.append(option)
                
                super().__init__(
                    placeholder="Select events to disable...",
                    min_values=0,
                    max_values=len(current_events),
                    options=options
                )
            
            async def callback(self, select_interaction: discord.Interaction):
                if select_interaction.user != interaction.user:
                    await select_interaction.response.send_message("This is not your menu.", ephemeral=True)
                    return
                
                # Get current settings
                current_settings = database.get_guild_logging(str(interaction.guild.id))
                if not current_settings:
                    await select_interaction.response.edit_message(
                        content="No logging settings found.",
                        embed=None,
                        view=None
                    )
                    return
                
                # Remove selected events
                remaining_events = [e for e in current_settings["log_events"] if e not in self.values]
                
                # Update settings
                database.set_guild_logging(
                    str(interaction.guild.id),
                    len(remaining_events) > 0,  # Enable only if there are events
                    remaining_events,
                    current_settings.get("webhook_url")
                )
                
                embed = create_success_embed("Logging Updated")
                if remaining_events:
                    embed.add_field(
                        name="Still Logging",
                        value="\n".join([f"• {e.replace('_', ' ').title()}" for e in remaining_events]),
                        inline=False
                    )
                else:
                    embed.description = "All logging has been disabled."
                
                await select_interaction.response.edit_message(embed=embed, view=None)
                
                # Log command usage
                database.log_command(str(interaction.guild.id), str(interaction.user.id), "stopselectedlogs")
        
        class DisableView(discord.ui.View):
            def __init__(self, current_events: List[str]):
                super().__init__(timeout=180)
                if current_events:
                    self.add_item(DisableEventSelect(current_events))
        
        # Get current settings
        current_settings = database.get_guild_logging(str(interaction.guild.id))
        if not current_settings or not current_settings.get("log_events"):
            embed = create_error_embed("No logging is currently enabled.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        current_events = current_settings["log_events"]
        
        embed = create_info_embed(
            "Disable Log Events",
            "Select which events you want to stop logging."
        )
        embed.add_field(
            name="Currently Logging",
            value="\n".join([f"• {e.replace('_', ' ').title()}" for e in current_events]),
            inline=False
        )
        
        view = DisableView(current_events)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

async def setup(bot: commands.Bot):
    """Setup the cog"""
    await bot.add_cog(LoggingSystem(bot))
