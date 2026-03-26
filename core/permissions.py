
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, List
from core.config_manager import config_manager

def is_super_admin():
    """Check if user is a super admin from env or config"""
    async def predicate(interaction: discord.Interaction) -> bool:
        # Check environment variable super admins first
        super_admin_ids = config_manager.get("super_admins", [])
        
        # Also check config file super admins (for backward compatibility)
        config_super_admins = config_manager.get("super_admin_ids", [])
        all_super_admins = list(set(super_admin_ids + config_super_admins))
        
        return interaction.user.id in all_super_admins
    return app_commands.check(predicate)

def is_high_role():
    """Check if user has high role from env or is moderator"""
    async def predicate(interaction: discord.Interaction) -> bool:
        # Check super admin first
        super_admin_ids = config_manager.get("super_admins", [])
        config_super_admins = config_manager.get("super_admin_ids", [])
        all_super_admins = list(set(super_admin_ids + config_super_admins))
        
        if interaction.user.id in all_super_admins:
            return True
        
        # Check high roles from env
        if not interaction.guild:
            return False
        
        high_role_ids = config_manager.get("high_roles", [])
        user_roles = [role.id for role in interaction.user.roles]
        
        # Check if user has any high role
        for role_id in high_role_ids:
            if role_id in user_roles:
                return True
        
        # Check config file mod roles (for backward compatibility)
        mod_role_ids = config_manager.get("mod_role_ids", [])
        for role_id in mod_role_ids:
            if role_id in user_roles:
                return True
        
        # Check Discord permissions
        return interaction.user.guild_permissions.manage_guild
    
    return app_commands.check(predicate)

def nsfw_channel_only():
    """Check if command is used in NSFW channel or allowed channel from env"""
    async def predicate(interaction: discord.Interaction) -> bool:
        if not interaction.channel:
            return False
        
        # Allow in DMs (no channel check)
        if isinstance(interaction.channel, discord.DMChannel):
            return True
        
        # Check if channel is in allowed NSFW channels from env
        allowed_channel_ids = config_manager.get("nsfw_channels", [])
        if interaction.channel.id in allowed_channel_ids:
            return True
        
        # Check if channel is NSFW marked
        if hasattr(interaction.channel, 'is_nsfw'):
            return interaction.channel.is_nsfw()
        
        return False
    
    return app_commands.check(predicate)

def log_channel_only():
    """Check if command is used in log channel from env"""
    async def predicate(interaction: discord.Interaction) -> bool:
        if not interaction.channel:
            return False
        
        log_channel_id = config_manager.get("log_channel")
        if not log_channel_id:
            return True  # No log channel set, allow anywhere
        
        return interaction.channel.id == log_channel_id
    
    return app_commands.check(predicate)

class PermissionErrorView(discord.ui.View):
    """View for permission errors"""
    
    def __init__(self, error_message: str):
        super().__init__(timeout=60)
        self.error_message = error_message
    
    @discord.ui.button(label="Permission Denied", style=discord.ButtonStyle.danger, disabled=True)
    async def permission_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """Handle command errors"""
    if isinstance(error, app_commands.CheckFailure):
        # Check for specific channel restrictions
        if "nsfw_channel_only" in str(error):
            embed = discord.Embed(
                title="Channel Restriction",
                description="This command can only be used in NSFW-marked channels or specifically allowed channels.",
                color=config_manager.get("error_color", 0xFF0000)
            )
            
            # Show allowed channels if any
            allowed_channels = config_manager.get("nsfw_channels", [])
            if allowed_channels:
                channels_mention = " ".join([f"<#{cid}>" for cid in allowed_channels])
                embed.add_field(
                    name="Allowed Channels",
                    value=channels_mention,
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        embed = discord.Embed(
            title="Permission Denied",
            description="You don't have permission to use this command.",
            color=config_manager.get("error_color", 0xFF0000)
        )
        
        if isinstance(error, app_commands.MissingPermissions):
            embed.add_field(
                name="Missing Permissions",
                value=", ".join(error.missing_permissions),
                inline=False
            )
        
        view = PermissionErrorView("Permission Denied")
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    elif isinstance(error, app_commands.CommandNotFound):
        embed = discord.Embed(
            title="Command Not Found",
            description="The command you tried to use doesn't exist.",
            color=config_manager.get("error_color", 0xFF0000)
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    else:
        # Log other errors
        print(f"Command error: {error}")
        embed = discord.Embed(
            title="Command Error",
            description="An unexpected error occurred.",
            color=config_manager.get("error_color", 0xFF0000)
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
