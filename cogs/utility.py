
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
import psutil
import platform
from datetime import datetime

from core.database import database
from core.permissions import is_high_role, is_super_admin
from utils.embeds import create_info_embed, create_error_embed
from core.config_manager import config_manager
from core.api_client import api_client

class Utility(commands.Cog):
    """Utility commands"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = config_manager
        self.start_time = datetime.utcnow()
    
    @app_commands.command(name="ping", description="Check bot latency and API status")
    async def ping(self, interaction: discord.Interaction):
        """Check bot latency"""
        # Calculate latency
        latency = round(self.bot.latency * 1000)
        
        # Test API connectivity
        api_status = "❓ Unknown"
        try:
            test_data = await api_client.fetch_from_api(
                "https://safebooru.org/index.php?page=dapi&s=post&q=index&json=1&tags=rating:general&limit=1"
            )
            api_status = "✅ Online" if test_data else "❌ Offline"
        except:
            api_status = "❌ Offline"
        
        bot_name = self.config.get("bot_name", "Lust Mommy")
        
        embed = create_info_embed(f"🏓 {bot_name} - Ping", f"Bot latency: **{latency}ms**")
        embed.add_field(name="API Status", value=api_status, inline=True)
        embed.add_field(name="Shard", value=f"{interaction.guild.shard_id if interaction.guild else 0}", inline=True)
        
        await interaction.response.send_message(embed=embed)
        
        # Log command usage
        if interaction.guild:
            database.log_command(str(interaction.guild.id), str(interaction.user.id), "ping")
    
    @app_commands.command(name="help", description="Show help menu with all commands")
    async def help(self, interaction: discord.Interaction):
        """Show help menu"""
        bot_name = self.config.get("bot_name", "Lust Mommy")
        
        embed = create_info_embed(f"🤖 {bot_name} - Help", "Here are all available commands:")
        
        # Moderation commands
        mod_commands = """
        `/kick` - Kick a user from the server (High Roles+)
        `/ban` - Ban a user from the server (High Roles+)
        `/masskick` - Mass kick users by role (Super Admin only)
        `/massban` - Mass ban users by ID list (Super Admin only)
        `/log` - Configure logging for this server (High Roles+, Log Channel only)
        `/stopalllogs` - Disable all logging for this server (High Roles+, Log Channel only)
        `/stopselectedlogs` - Disable specific log events (High Roles+, Log Channel only)
        """
        embed.add_field(name="🔧 Moderation", value=mod_commands.strip(), inline=False)
        
        # Single NSFW commands
        single_nsfw = """
        `/loli` - Fetch loli content (NSFW channels only)
        `/shotacon` - Fetch shotacon content (NSFW channels only)
        `/yaoi` - Fetch yaoi content (NSFW channels only)
        `/yuri` - Fetch yuri content (NSFW channels only)
        `/hentai` - Fetch hentai content (NSFW channels only)
        """
        embed.add_field(name="🎨 Single NSFW", value=single_nsfw.strip(), inline=False)
        
        # Mass NSFW commands
        mass_nsfw = """
        `/massloli` - Fetch 10 loli images (NSFW channels only)
        `/massshotacon` - Fetch 10 shotacon images (NSFW channels only)
        `/massyaoi` - Fetch 10 yaoi images (NSFW channels only)
        `/massyuri` - Fetch 10 yuri images (NSFW channels only)
        `/masshentai` - Fetch 10 hentai images (NSFW channels only)
        """
        embed.add_field(name="📦 Mass NSFW", value=mass_nsfw.strip(), inline=False)
        
        # Search command
        search_cmd = """
        `/search [tags]` - Search specific tags across multiple sites (NSFW channels only)
        Example: `/search loli kiss`
        """
        embed.add_field(name="🔍 Search", value=search_cmd.strip(), inline=False)
        
        # Utility commands
        utility_cmds = """
        `/ping` - Check bot latency and API status
        `/serverinfo` - Get detailed server information
        `/userinfo` - Get user information
        `/help` - Show this help menu
        `/stats` - View command usage statistics (High Roles+)
        `/health` - View bot health metrics (Super Admins only)
        """
        embed.add_field(name="ℹ️ Utility", value=utility_cmds.strip(), inline=False)
        
        # Admin commands (only show to super admins)
        if await is_super_admin().predicate(interaction):
            admin_cmds = """
            `/sync` - Sync slash commands
            `/reload [cog]` - Reload a cog
            `/shutdown` - Shutdown the bot
            `/addadmin [user_id]` - Add a super admin
            `/removeadmin [user_id]` - Remove a super admin
            """
            embed.add_field(name="⚙️ Admin", value=admin_cmds.strip(), inline=False)
        
        # Show NSFW channel info
        nsfw_channels = self.config.get("nsfw_channels", [])
        if nsfw_channels:
            channels_mention = " ".join([f"<#{cid}>" for cid in nsfw_channels])
            embed.add_field(
                name="Allowed NSFW Channels",
                value=channels_mention,
                inline=False
            )
        
        # Show log channel info
        log_channel_id = self.config.get("log_channel")
        if log_channel_id:
            embed.add_field(
                name="Log Channel",
                value=f"<#{log_channel_id}>",
                inline=False
            )
        
        embed.set_footer(text=f"{bot_name} • Use /help for more commands")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # Log command usage
        if interaction.guild:
            database.log_command(str(interaction.guild.id), str(interaction.user.id), "help")
    
    @app_commands.command(name="stats", description="View command usage statistics (High Roles+)")
    @is_high_role()
    async def stats(self, interaction: discord.Interaction):
        """View command statistics"""
        await interaction.response.defer()
        
        # Get stats for this guild
        stats_data = database.get_command_stats(str(interaction.guild.id), limit=20)
        
        if not stats_data:
            embed = create_info_embed("📊 Command Statistics", "No command usage data yet.")
            await interaction.followup.send(embed=embed)
            return
        
        # Format stats
        stats_text = ""
        total_commands = 0
        
        for stat in stats_data:
            stats_text += f"**{stat['command_name']}**: {stat['count']} uses\n"
            total_commands += stat['count']
        
        bot_name = self.config.get("bot_name", "Lust Mommy")
        
        embed = create_info_embed(f"📊 {bot_name} - Statistics", f"Total commands: **{total_commands}**")
        embed.add_field(name="Top Commands", value=stats_text, inline=False)
        
        await interaction.followup.send(embed=embed)
        
        # Log command usage
        database.log_command(str(interaction.guild.id), str(interaction.user.id), "stats")
    
    @app_commands.command(name="health", description="View bot health metrics (Super Admins only)")
    @is_super_admin()
    async def health(self, interaction: discord.Interaction):
        """View bot health metrics"""
        await interaction.response.defer()
        
        # Calculate uptime
        uptime = datetime.utcnow() - self.start_time
        uptime_str = str(uptime).split('.')[0]  # Remove microseconds
        
        # Get system info
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get bot stats
        guild_count = len(self.bot.guilds)
        user_count = len(self.bot.users)
        channel_count = sum(len(guild.channels) for guild in self.bot.guilds)
        
        # Get configuration info
        bot_name = self.config.get("bot_name", "Lust Mommy")
        super_admin_count = len(self.config.get("super_admins", []))
        high_role_count = len(self.config.get("high_roles", []))
        nsfw_channel_count = len(self.config.get("nsfw_channels", []))
        
        # Create embed
        embed = create_info_embed(f"🏥 {bot_name} - Health Status", "")
        
        # System metrics
        embed.add_field(name="CPU Usage", value=f"{cpu_percent}%", inline=True)
        embed.add_field(name="Memory Usage", value=f"{memory.percent}%", inline=True)
        embed.add_field(name="Disk Usage", value=f"{disk.percent}%", inline=True)
        
        # Bot metrics
        embed.add_field(name="Uptime", value=uptime_str, inline=True)
        embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        embed.add_field(name="Python Version", value=platform.python_version(), inline=True)
        
        # Discord metrics
        embed.add_field(name="Guilds", value=str(guild_count), inline=True)
        embed.add_field(name="Users", value=str(user_count), inline=True)
        embed.add_field(name="Channels", value=str(channel_count), inline=True)
        embed.add_field(name="Shards", value=str(self.bot.shard_count or 1), inline=True)
        
        # Configuration metrics
        embed.add_field(name="Super Admins", value=str(super_admin_count), inline=True)
        embed.add_field(name="High Roles", value=str(high_role_count), inline=True)
        embed.add_field(name="NSFW Channels", value=str(nsfw_channel_count), inline=True)
        
        # API status
        try:
            test_data = await api_client.fetch_from_api(
                "https://safebooru.org/index.php?page=dapi&s=post&q=index&json=1&tags=rating:general&limit=1"
            )
            api_status = "✅ Online" if test_data else "⚠️ Partial"
        except:
            api_status = "❌ Offline"
        
        embed.add_field(name="API Status", value=api_status, inline=True)
        
        await interaction.followup.send(embed=embed)
        
        # Log command usage
        if interaction.guild:
            database.log_command(str(interaction.guild.id), str(interaction.user.id), "health")

async def setup(bot: commands.Bot):
    """Setup the cog"""
    await bot.add_cog(Utility(bot))
