
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, List
import asyncio

from core.database import database
from core.permissions import is_high_role, is_super_admin
from utils.embeds import create_success_embed, create_error_embed, create_info_embed
from utils.converters import UserListConverter, RoleConverter
from utils.webhook_handler import webhook_handler
from core.config_manager import config_manager

class Moderation(commands.Cog):
    """Moderation commands"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = config_manager
    
    @app_commands.command(name="kick", description="Kick a user from the server")
    @app_commands.describe(
        member="Member to kick",
        reason="Reason for kick"
    )
    @is_high_role()  # Changed from has_permissions to custom check
    async def kick(
        self, 
        interaction: discord.Interaction, 
        member: discord.Member,
        reason: Optional[str] = "No reason provided"
    ):
        """Kick a member"""
        # Check if target has high role
        high_role_ids = self.config.get("high_roles", [])
        target_high_role = any(role.id in high_role_ids for role in member.roles)
        
        if target_high_role and not await is_super_admin().predicate(interaction):
            embed = create_error_embed("You cannot kick members with high roles.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if member.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            embed = create_error_embed("You cannot kick members with equal or higher role.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if member == interaction.user:
            embed = create_error_embed("You cannot kick yourself.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        try:
            await member.kick(reason=f"{interaction.user}: {reason}")
            
            embed = create_success_embed(f"Kicked {member.mention}")
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
            
            await interaction.response.send_message(embed=embed)
            
            # Log to webhook
            if interaction.guild:
                await webhook_handler.send_log(
                    "member_kick",
                    interaction.guild,
                    {
                        "user": f"{member} ({member.id})",
                        "moderator": f"{interaction.user} ({interaction.user.id})",
                        "reason": reason,
                        "timestamp": discord.utils.utcnow()
                    }
                )
                
                # Log command usage
                database.log_command(str(interaction.guild.id), str(interaction.user.id), "kick")
        
        except discord.Forbidden:
            embed = create_error_embed("I don't have permission to kick this member.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.HTTPException as e:
            embed = create_error_embed(f"Failed to kick member: {e}")
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="ban", description="Ban a user from the server")
    @app_commands.describe(
        member="Member to ban",
        reason="Reason for ban",
        delete_message_days="Number of days of messages to delete (0-7)"
    )
    @is_high_role()  # Changed from has_permissions to custom check
    async def ban(
        self, 
        interaction: discord.Interaction, 
        member: discord.Member,
        reason: Optional[str] = "No reason provided",
        delete_message_days: app_commands.Range[int, 0, 7] = 0
    ):
        """Ban a member"""
        # Check if target has high role
        high_role_ids = self.config.get("high_roles", [])
        target_high_role = any(role.id in high_role_ids for role in member.roles)
        
        if target_high_role and not await is_super_admin().predicate(interaction):
            embed = create_error_embed("You cannot ban members with high roles.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if member.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            embed = create_error_embed("You cannot ban members with equal or higher role.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if member == interaction.user:
            embed = create_error_embed("You cannot ban yourself.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        try:
            await member.ban(
                reason=f"{interaction.user}: {reason}",
                delete_message_days=delete_message_days
            )
            
            embed = create_success_embed(f"Banned {member.mention}")
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
            if delete_message_days > 0:
                embed.add_field(name="Messages Deleted", value=f"{delete_message_days} days", inline=False)
            
            await interaction.response.send_message(embed=embed)
            
            # Log to webhook
            if interaction.guild:
                await webhook_handler.send_log(
                    "member_ban",
                    interaction.guild,
                    {
                        "user": f"{member} ({member.id})",
                        "moderator": f"{interaction.user} ({interaction.user.id})",
                        "reason": reason,
                        "delete_days": delete_message_days,
                        "timestamp": discord.utils.utcnow()
                    }
                )
                
                # Log command usage
                database.log_command(str(interaction.guild.id), str(interaction.user.id), "ban")
        
        except discord.Forbidden:
            embed = create_error_embed("I don't have permission to ban this member.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.HTTPException as e:
            embed = create_error_embed(f"Failed to ban member: {e}")
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="masskick", description="Mass kick users by role (Super Admin only)")
    @app_commands.describe(
        role="Role to mass kick",
        reason="Reason for mass kick"
    )
    @is_super_admin()  # Only super admins can use mass commands
    async def masskick(
        self,
        interaction: discord.Interaction,
        role: discord.Role,
        reason: Optional[str] = "Mass kick"
    ):
        """Mass kick members by role"""
        await interaction.response.defer()
        
        # Check if role is high role
        high_role_ids = self.config.get("high_roles", [])
        if role.id in high_role_ids:
            embed = create_error_embed("Cannot mass kick high roles.")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        if role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            embed = create_error_embed("You cannot mass kick members with equal or higher role.")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        members = [m for m in role.members if m != interaction.user and m != self.bot.user]
        
        if not members:
            embed = create_error_embed("No members found with that role (excluding yourself and bot).")
            await interaction.followup.send(embed=embed)
            return
        
        batch_size = self.config.get("mass_action_batch_size", 5)
        successful = 0
        failed = 0
        
        # Send initial status
        embed = create_info_embed(
            "Mass Kick Started",
            f"Kicking {len(members)} members from role {role.mention}..."
        )
        status_msg = await interaction.followup.send(embed=embed)
        
        # Process in batches
        for i in range(0, len(members), batch_size):
            batch = members[i:i + batch_size]
            
            for member in batch:
                try:
                    await member.kick(reason=f"{interaction.user}: {reason}")
                    successful += 1
                except:
                    failed += 1
                
                await asyncio.sleep(0.5)  # Rate limiting
            
            # Update status
            embed = create_info_embed(
                "Mass Kick in Progress",
                f"Progress: {i + len(batch)}/{len(members)}\n"
                f"Successful: {successful}\n"
                f"Failed: {failed}"
            )
            await status_msg.edit(embed=embed)
            
            if i + batch_size < len(members):
                await asyncio.sleep(1)  # Delay between batches
        
        # Final result
        embed = create_success_embed("Mass Kick Complete")
        embed.add_field(name="Total Members", value=str(len(members)), inline=True)
        embed.add_field(name="Successful", value=str(successful), inline=True)
        embed.add_field(name="Failed", value=str(failed), inline=True)
        embed.add_field(name="Role", value=role.mention, inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
        
        await status_msg.edit(embed=embed)
        
        # Log command usage
        if interaction.guild:
            database.log_command(str(interaction.guild.id), str(interaction.user.id), "masskick")
    
    @app_commands.command(name="massban", description="Mass ban users by ID list (Super Admin only)")
    @app_commands.describe(
        user_ids="Comma-separated user IDs to ban",
        reason="Reason for mass ban",
        delete_message_days="Number of days of messages to delete (0-7)"
    )
    @is_super_admin()  # Only super admins can use mass commands
    async def massban(
        self,
        interaction: discord.Interaction,
        user_ids: str,
        reason: Optional[str] = "Mass ban",
        delete_message_days: app_commands.Range[int, 0, 7] = 0
    ):
        """Mass ban users by ID list"""
        await interaction.response.defer()
        
        # Parse user IDs
        try:
            ids = [int(id_str.strip()) for id_str in user_ids.split(',') if id_str.strip().isdigit()]
        except ValueError:
            embed = create_error_embed("Invalid user IDs. Use comma-separated numbers.")
            await interaction.followup.send(embed=embed)
            return
        
        if len(ids) > 100:
            embed = create_error_embed("Maximum 100 users per mass ban.")
            await interaction.followup.send(embed=embed)
            return
        
        batch_size = self.config.get("mass_action_batch_size", 5)
        successful = 0
        failed = 0
        not_found = 0
        
        # Get high role IDs for protection check
        high_role_ids = self.config.get("high_roles", [])
        
        # Send initial status
        embed = create_info_embed(
            "Mass Ban Started",
            f"Banning {len(ids)} users..."
        )
        status_msg = await interaction.followup.send(embed=embed)
        
        # Process in batches
        for i in range(0, len(ids), batch_size):
            batch = ids[i:i + batch_size]
            
            for user_id in batch:
                try:
                    # Try to fetch member first
                    member = interaction.guild.get_member(user_id)
                    if member:
                        # Check if member has high role
                        member_high_role = any(role.id in high_role_ids for role in member.roles)
                        if member_high_role:
                            failed += 1
                            continue
                        
                        if member.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
                            failed += 1
                            continue
                    
                    # Ban by ID
                    await interaction.guild.ban(
                        discord.Object(id=user_id),
                        reason=f"{interaction.user}: {reason}",
                        delete_message_days=delete_message_days
                    )
                    successful += 1
                except discord.NotFound:
                    not_found += 1
                except:
                    failed += 1
                
                await asyncio.sleep(0.5)  # Rate limiting
            
            # Update status
            embed = create_info_embed(
                "Mass Ban in Progress",
                f"Progress: {i + len(batch)}/{len(ids)}\n"
                f"Successful: {successful}\n"
                f"Failed: {failed}\n"
                f"Not Found: {not_found}"
            )
            await status_msg.edit(embed=embed)
            
            if i + batch_size < len(ids):
                await asyncio.sleep(1)  # Delay between batches
        
        # Final result
        embed = create_success_embed("Mass Ban Complete")
        embed.add_field(name="Total IDs", value=str(len(ids)), inline=True)
        embed.add_field(name="Successful", value=str(successful), inline=True)
        embed.add_field(name="Failed", value=str(failed), inline=True)
        embed.add_field(name="Not Found", value=str(not_found), inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
        
        await status_msg.edit(embed=embed)
        
        # Log command usage
        if interaction.guild:
            database.log_command(str(interaction.guild.id), str(interaction.user.id), "massban")

async def setup(bot: commands.Bot):
    """Setup the cog"""
    await bot.add_cog(Moderation(bot))
