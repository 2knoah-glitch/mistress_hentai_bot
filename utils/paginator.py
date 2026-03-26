
import discord
from typing import List, Dict, Any, Optional
from utils.embeds import create_nsfw_embed

class PaginatorView(discord.ui.View):
    """View for paginated embeds"""
    
    def __init__(self, embeds: List[discord.Embed], timeout: float = 180.0):
        super().__init__(timeout=timeout)
        self.embeds = embeds
        self.current_page = 0
        self.update_buttons()
    
    def update_buttons(self) -> None:
        """Update button states based on current page"""
        self.first_page.disabled = self.current_page == 0
        self.previous_page.disabled = self.current_page == 0
        self.next_page.disabled = self.current_page == len(self.embeds) - 1
        self.last_page.disabled = self.current_page == len(self.embeds) - 1
        
        # Update page counter
        self.page_counter.label = f"Page {self.current_page + 1}/{len(self.embeds)}"
    
    @discord.ui.button(label="« First", style=discord.ButtonStyle.secondary)
    async def first_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = 0
        self.update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
    
    @discord.ui.button(label="‹ Previous", style=discord.ButtonStyle.primary)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = max(0, self.current_page - 1)
        self.update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
    
    @discord.ui.button(label="Page 1/1", style=discord.ButtonStyle.secondary, disabled=True)
    async def page_counter(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass  # This button is just for display
    
    @discord.ui.button(label="Next ›", style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = min(len(self.embeds) - 1, self.current_page + 1)
        self.update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
    
    @discord.ui.button(label="Last »", style=discord.ButtonStyle.secondary)
    async def last_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = len(self.embeds) - 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
    
    @discord.ui.button(label="❌ Close", style=discord.ButtonStyle.danger)
    async def close_paginator(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()

def create_mass_nsfw_embeds(image_data_list: List[Dict[str, Any]], category: str) -> List[discord.Embed]:
    """Create multiple embeds for mass NSFW commands"""
    embeds = []
    
    for i, image_data in enumerate(image_data_list):
        embed = create_nsfw_embed(image_data, category)
        embed.set_footer(text=f"Your Mistress Bot • Image {i + 1}/{len(image_data_list)}")
        embeds.append(embed)
    
    return embeds
