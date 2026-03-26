
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
import sys

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Import core modules
from core.config_manager import config_manager
from core.permissions import on_app_command_error
from core.logger import logger

# Import keep_alive for Replit
try:
    import keep_alive
    KEEP_ALIVE_AVAILABLE = True
except ImportError:
    KEEP_ALIVE_AVAILABLE = False
    logger.warning("keep_alive module not found. Replit uptime monitor disabled.")

class YourMistressBot(commands.Bot):
    """Custom bot class with enhanced functionality"""
    
    def __init__(self):
        # Define intents
        intents = discord.Intents.default()
        intents.message_content = True  # Required for message logging
        intents.members = True          # Required for member events
        intents.guilds = True
        intents.bans = True
        
        # Get bot name from config
        bot_name = config_manager.get("bot_name", "Lust Mommy")
        bot_status = config_manager.get("bot_status", "Watching your commands | /help")
        
        super().__init__(
            command_prefix="/",
            intents=intents,
            help_command=None,
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=bot_status
            )
        )
        
        # Store config
        self.config = config_manager
        
    async def setup_hook(self):
        """Setup hook for loading cogs"""
        logger.info("Starting bot setup...")
        
        # Load cogs
        cogs = [
            "cogs.nsfw",
            "cogs.moderation",
            "cogs.logging_system",
            "cogs.utility",
            "cogs.admin"
        ]
        
        for cog in cogs:
            try:
                await self.load_extension(cog)
                logger.info(f"Loaded cog: {cog}")
            except Exception as e:
                logger.error(f"Failed to load cog {cog}: {e}")
        
        # Sync commands
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} command(s)")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")
    
    async def on_ready(self):
        """Called when bot is ready"""
        bot_name = self.config.get("bot_name", "Lust Mommy")
        logger.info(f"Logged in as {self.user.name} (ID: {self.user.id})")
        logger.info(f"Bot Name: {bot_name}")
        logger.info(f"Connected to {len(self.guilds)} guild(s)")
        logger.info(f"Connected to {len(self.users)} user(s)")
        
        # Log configuration
        super_admins = self.config.get("super_admins", [])
        high_roles = self.config.get("high_roles", [])
        nsfw_channels = self.config.get("nsfw_channels", [])
        
        logger.info(f"Super Admins: {len(super_admins)} users")
        logger.info(f"High Roles: {len(high_roles)} roles")
        logger.info(f"NSFW Channels: {len(nsfw_channels)} channels")
        
        # Print guild list
        for guild in self.guilds:
            logger.info(f" - {guild.name} (ID: {guild.id})")
        
        print(f"\n{'='*50}")
        print(f"{bot_name} is online!")
        print(f"User: {self.user}")
        print(f"Guilds: {len(self.guilds)}")
        print(f"Super Admins: {len(super_admins)}")
        print(f"Use /help for commands")
        print(f"{'='*50}\n")
    
    async def on_guild_join(self, guild: discord.Guild):
        """Called when bot joins a guild"""
        bot_name = self.config.get("bot_name", "Lust Mommy")
        logger.info(f"Joined guild: {guild.name} (ID: {guild.id})")
        
        # Send welcome message to system channel or first text channel
        try:
            channel = guild.system_channel or next(
                (c for c in guild.text_channels if c.permissions_for(guild.me).send_messages),
                None
            )
            
            if channel:
                embed = discord.Embed(
                    title=f"Thanks for adding {bot_name}!",
                    description=(
                        f"I'm {bot_name}, a multi-purpose bot with NSFW, moderation, and logging features.\n\n"
                        "**Important:**\n"
                        "• NSFW commands require NSFW-marked channels or specifically allowed channels\n"
                        "• Configure logging with `/log`\n"
                        "• Use `/help` for all commands\n"
                        "• Super admins and high roles are configured via environment variables\n\n"
                        "Need help? Check the documentation."
                    ),
                    color=self.config.get("default_color", 0xFF69B4)
                )
                await channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Failed to send welcome message to {guild.name}: {e}")
    
    async def on_guild_remove(self, guild: discord.Guild):
        """Called when bot is removed from a guild"""
        logger.info(f"Removed from guild: {guild.name} (ID: {guild.id})")
    
    async def on_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        """Handle command errors"""
        await on_app_command_error(interaction, error)

async def main():
    """Main entry point"""
    # Check for token
    token = config_manager.get("discord_token")
    if not token:
        logger.error("DISCORD_TOKEN not found in environment variables.")
        print("Error: DISCORD_TOKEN not found. Please add it to your .env file.")
        return
    
    # Validate token format
    if not token.startswith(("MT", "Mz", "ND", "NT", "Nj", "Nz", "OD", "OT")):
        logger.warning("Discord token format may be invalid. Ensure it's a valid bot token.")
    
    # Create bot instance
    bot = YourMistressBot()
    
    # Start keep_alive for Replit
    if KEEP_ALIVE_AVAILABLE:
        keep_alive.keep_alive()
        logger.info("Started keep_alive server")
    
    # Start bot
    try:
        async with bot:
            await bot.start(token)
    except discord.LoginFailure:
        logger.error("Failed to login. Check your DISCORD_TOKEN.")
        print("Error: Invalid DISCORD_TOKEN. Please check your .env file.")
    except KeyboardInterrupt:
        logger.info("Bot stopped by keyboard interrupt")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        raise
    finally:
        # Cleanup
        from core.api_client import api_client
        from utils.webhook_handler import webhook_handler
        
        await api_client.close()
        await webhook_handler.close()
        logger.info("Cleanup complete")

if __name__ == "__main__":
    asyncio.run(main())
