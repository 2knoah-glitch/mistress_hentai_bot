
import discord
from discord import app_commands
from discord.ext import commands
import os

from core.permissions import is_super_admin
from utils.embeds import create_success_embed, create_error_embed
from core.config_manager import config_manager

class Admin(commands.Cog):
    """Super admin commands"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = config_manager
    
    @app_commands.command(name="sync", description="Sync slash commands (Super Admin only)")
    @is_super_admin()
    async def sync(self, interaction: discord.Interaction):
        """Sync slash commands globally"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            synced = await self.bot.tree.sync()
            embed = create_success_embed(f"Synced {len(synced)} command(s) globally.")
        except Exception as e:
            embed = create_error_embed(f"Failed to sync commands: {e}")
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(name="reload", description="Reload a cog (Super Admin only)")
    @app_commands.describe(cog="Cog to reload")
    @is_super_admin()
    async def reload(self, interaction: discord.Interaction, cog: str):
        """Reload a cog"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            await self.bot.reload_extension(f"cogs.{cog}")
            embed = create_success_embed(f"Reloaded cog: {cog}")
        except commands.ExtensionNotLoaded:
            try:
                await self.bot.load_extension(f"cogs.{cog}")
                embed = create_success_embed(f"Loaded cog: {cog}")
            except Exception as e:
                embed = create_error_embed(f"Failed to load cog {cog}: {e}")
        except Exception as e:
            embed = create_error_embed(f"Failed to reload cog {cog}: {e}")
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(name="shutdown", description="Shutdown the bot (Super Admin only)")
    @is_super_admin()
    async def shutdown(self, interaction: discord.Interaction):
        """Shutdown the bot"""
        embed = create_success_embed("Shutting down bot...")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # Close connections
        from core.api_client import api_client
        from utils.webhook_handler import webhook_handler
        
        await api_client.close()
        await webhook_handler.close()
        
        await self.bot.close()
    
    @app_commands.command(name="addadmin", description="Add a super admin (Super Admin only)")
    @app_commands.describe(user_id="User ID to add as super admin")
    @is_super_admin()
    async def addadmin(self, interaction: discord.Interaction, user_id: str):
        """Add a super admin"""
        try:
            user_id_int = int(user_id)
            
            # Get current super admins from env
            super_admin_ids = self.config.get("super_admins", [])
            
            if user_id_int in super_admin_ids:
                embed = create_error_embed("User is already a super admin.")
            else:
                super_admin_ids.append(user_id_int)
                # Update in memory only (env vars can't be modified at runtime)
                self.config.set("super_admins", super_admin_ids)
                embed = create_success_embed(f"Added <@{user_id_int}> as super admin (in memory).\n"
                                           f"Add to SUPER_ADMINS in .env for persistence.")
        
        except ValueError:
            embed = create_error_embed("Invalid user ID.")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="removeadmin", description="Remove a super admin (Super Admin only)")
    @app_commands.describe(user_id="User ID to remove from super admins")
    @is_super_admin()
    async def removeadmin(self, interaction: discord.Interaction, user_id: str):
        """Remove a super admin"""
        try:
            user_id_int = int(user_id)
            
            # Get current super admins from env
            super_admin_ids = self.config.get("super_admins", [])
            
            if user_id_int == interaction.user.id:
                embed = create_error_embed("You cannot remove yourself.")
            elif user_id_int not in super_admin_ids:
                embed = create_error_embed("User is not a super admin.")
            else:
                super_admin_ids.remove(user_id_int)
                # Update in memory only
                self.config.set("super_admins", super_admin_ids)
                embed = create_success_embed(f"Removed <@{user_id_int}> from super admins (in memory).\n"
                                           f"Remove from SUPER_ADMINS in .env for persistence.")
        
        except ValueError:
            embed = create_error_embed("Invalid user ID.")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="addhighrole", description="Add a high role (Super Admin only)")
    @app_commands.describe(role_id="Role ID to add as high role")
    @is_super_admin()
    async def addhighrole(self, interaction: discord.Interaction, role_id: str):
        """Add a high role"""
        try:
            role_id_int = int(role_id)
            
            # Get current high roles from env
            high_role_ids = self.config.get("high_roles", [])
            
            if role_id_int in high_role_ids:
                embed = create_error_embed("Role is already a high role.")
            else:
                high_role_ids.append(role_id_int)
                # Update in memory only
                self.config.set("high_roles", high_role_ids)
                embed = create_success_embed(f"Added <@&{role_id_int}> as high role (in memory).\n"
                                           f"Add to HIGH_ROLES in .env for persistence.")
        
        except ValueError:
            embed = create_error_embed("Invalid role ID.")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="addnsfwchannel", description="Add an NSFW channel (Super Admin only)")
    @app_commands.describe(channel_id="Channel ID to add as NSFW channel")
    @is_super_admin()
    async def addnsfwchannel(self, interaction: discord.Interaction, channel_id: str):
        """Add an NSFW channel"""
        try:
            channel_id_int = int(channel_id)
            
            # Get current NSFW channels from env
            nsfw_channel_ids = self.config.get("nsfw_channels", [])
            
            if channel_id_int in nsfw_channel_ids:
                embed = create_error_embed("Channel is already an NSFW channel.")
            else:
                nsfw_channel_ids.append(channel_id_int)
                # Update in memory only
                self.config.set("nsfw_channels", nsfw_channel_ids)
                embed = create_success_embed(f"Added <#{channel_id_int}> as NSFW channel (in memory).\n"
                                           f"Add to NSFW_CHANNELS in .env for persistence.")
        
        except ValueError:
            embed = create_error_embed("Invalid channel ID.")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    """Setup the cog"""
    await bot.add_cog(Admin(bot))
