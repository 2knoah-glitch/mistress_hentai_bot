
import discord
from discord import app_commands
from typing import List, Optional

class UserListConverter(app_commands.Transformer):
    """Convert comma-separated user IDs to list"""
    
    async def transform(self, interaction: discord.Interaction, value: str) -> List[int]:
        try:
            # Split by commas and clean up
            ids = [int(id_str.strip()) for id_str in value.split(',') if id_str.strip().isdigit()]
            return ids
        except ValueError:
            raise app_commands.AppCommandError("Invalid user IDs. Use comma-separated numbers.")

class TagListConverter(app_commands.Transformer):
    """Convert tag string to list"""
    
    async def transform(self, interaction: discord.Interaction, value: str) -> List[str]:
        # Split by commas or spaces
        if ',' in value:
            tags = [tag.strip() for tag in value.split(',') if tag.strip()]
        else:
            tags = [tag.strip() for tag in value.split() if tag.strip()]
        
        # Limit number of tags
        if len(tags) > 20:
            tags = tags[:20]
        
        return tags

class RoleConverter(app_commands.Transformer):
    """Convert role mention or ID to Role object"""
    
    async def transform(self, interaction: discord.Interaction, value: str) -> Optional[discord.Role]:
        try:
            # Try to parse as mention
            if value.startswith('<@&') and value.endswith('>'):
                role_id = int(value[3:-1])
            else:
                # Try as ID
                role_id = int(value)
            
            return interaction.guild.get_role(role_id)
        except (ValueError, AttributeError):
            # Try to find by name
            if interaction.guild:
                for role in interaction.guild.roles:
                    if role.name.lower() == value.lower():
                        return role
        return None
    
    async def autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        """Autocomplete role names"""
        if not interaction.guild:
            return []
        
        roles = interaction.guild.roles
        choices = []
        
        for role in roles:
            if current.lower() in role.name.lower() and not role.is_default():
                choices.append(app_commands.Choice(name=role.name, value=str(role.id)))
        
        return choices[:25]
