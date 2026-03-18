"""User management"""

import logging
import discord
from discord.ext import commands
from discord import app_commands

from bot import VoiceSquadBot
from utils.channel_names import get_channel_names
from utils.server_settings import get_guild, update_guild
from utils.voice_channels import add_voice_channel



class VoiceManagementView(discord.ui.View):
    def __init__(self, bot: VoiceSquadBot):
        self.bot = bot
        super().__init__(timeout=None)

    @discord.ui.button(
        label="rename",
        custom_id="voice_rename",
        style=discord.ButtonStyle.primary,
    )
    async def rename_callback(self, interaction: discord.Interaction, button):
        print(self.bot)


    @discord.ui.button(
        label="Set limit",
        custom_id="voice_set_limit",
        style=discord.ButtonStyle.primary,
    )
    async def set_limit_callback(self, interaction: discord.Interaction, button):
        print(self.bot)


    @discord.ui.button(
        label="Change owner",
        custom_id="voice_change_owner",
        style=discord.ButtonStyle.primary,
    )
    async def change_owner_callback(self, interaction: discord.Interaction, button):
        print(self.bot)

        

class Admin(commands.Cog):
    def __init__(self, bot: VoiceSquadBot):
        self.bot = bot
        self.logger = logging.getLogger("admin")

    group = app_commands.Group(
        name="admin", description="Commands meant only for admins"
    )

    generate_group = app_commands.Group(
        name="generate", description="Generate a message", parent=group
    )

    @generate_group.command(name="initial-channel", description="Generate the initial squad channel")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def generate_initial_channel(self, interaction: discord.Interaction) -> None:
        """Generate the initial squad channel"""
        async with self.bot.db.create_session() as session:
            guild_settings = await get_guild(session, interaction.guild_id)
            if guild_settings is None:
                await interaction.response.send_message("No server settings found")
            if guild_settings.category_id is None:
                await interaction.response.send_message("Category is not set")
            
            for category in interaction.guild.categories:
                existing_channel_names = [channel.name for channel in category.voice_channels]

                if guild_settings.category_id == category.id:
                    channel_names = await get_channel_names(self.bot, session, interaction.guild_id)
                    unused_channel_names = [channel_name for channel_name in channel_names if channel_name not in existing_channel_names]
                    if len(unused_channel_names) == 0:
                        await interaction.response.send_message("There are no more squad names available")
                        return

                    voice_channel = await category.create_voice_channel(unused_channel_names[0])
                    await add_voice_channel(session, interaction.guild_id, voice_channel.id)
                    await interaction.response.send_message("Create the initial voice channel")
                    return
            
            await interaction.response.send_message("The set category is not found within the server")
            # traceback.print_exc()

    @generate_group.command(name="voice-management", description="Generate the voice-management buttons")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def generate_voice_management(self, interaction: discord.Interaction) -> None:
        """Generate the register button"""
        embed = discord.Embed(
            title="Manage squad voice channel",
            description="""
            The first person that joins a squad channel, owns the channel until its empty again.
            The owner of the channel can manage it with the buttons below."""
        )
        await interaction.response.send_message(
            embed=embed, view=VoiceManagementView(self.bot)
        )

    
    # generate_group = app_commands.Group(
    #     name="names", description="Generate a message", parent=group
    # )

    set_group = app_commands.Group(
        name="set", description="Set a setting", parent=group
    )

    @set_group.command(name="category", description="Set the used category")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def set_category(self, interaction: discord.Interaction, category: discord.CategoryChannel) -> None:
        """Set the used category"""
        await interaction.response.defer()
        if interaction.guild is None:
            return  # is already set to guild_only
        async with self.bot.db.create_session() as session:
            await update_guild(
                session, interaction.guild, {"category_id": category.id}
            )
        await interaction.followup.send(
            f'Set the category channel to "{category.name}"', ephemeral=True
        )


async def setup(bot: VoiceSquadBot) -> None:
    """Setup the cog within discord.py lib"""
    bot.add_view(VoiceManagementView(bot))
    await bot.add_cog(Admin(bot))
