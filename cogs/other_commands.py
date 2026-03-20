"""Non-grouped commands"""

import discord
from discord import app_commands
from discord.ext import commands

from bot import VoiceSquadBot


class OtherCommands(commands.Cog):
    """Other commands"""

    def __init__(self, bot: VoiceSquadBot):
        self.bot = bot

    @app_commands.command(name="help", description="See more info about the bot")
    async def help_command(self, interaction: discord.Interaction):
        """Main help command"""
        await interaction.response.defer()
        embed = discord.Embed(
            color=0xFFA500,
            title="Help for the Voice Squad bot",
            description='This bot auto generates a voice channel when there are no more empty voice channels, and also removes them to keep it clean.\n' \
            'It will always leave 1 empty channel, for players to join.\n' \
            'To setup the bot "/admin set category" to set the category where it needs to create the voice squad channels.\n' \
            'Then use "/admin generate initial-channel" to create the initial squad voice channel to work with.\n' \
            'And "/admin generate voice-management" to generate the buttons for users to alter the voice channel.\n' \
            'The person that first joins the channel, will be the owner until it\'s empty again.\n' \
            'You can use "/admin names add/list/remove" to overwrite the names of all the voice channel names it creates with your own set.',
        )
        await interaction.followup.send(embed=embed)


async def setup(bot: VoiceSquadBot) -> None:
    """Setup the cog within discord.py lib"""
    await bot.add_cog(OtherCommands(bot))
