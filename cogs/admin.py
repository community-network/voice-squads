"""User management"""

import logging
import discord
from discord.ext import commands
from discord import app_commands

from bot import VoiceSquadBot
from database.dto.channel_names import ChannelName
from utils.channel_names import add_voice_channel_name, get_channel_names, get_channel_names_csv, remove_voice_channel_name
from utils.server_settings import get_guild, update_guild
from utils.voice_channels import add_voice_channel, get_voice_channel, update_voice_channel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select, func

async def channel_permision_check(session: AsyncSession, interaction: discord.Interaction,):
    voice = interaction.user.voice
    if voice is None or voice.channel is None:
        await interaction.response.send_message('You are not part of a voice channel', ephemeral=True)
        return False
    
    db_voice_channel = await get_voice_channel(session, interaction.guild_id, voice.channel.id)
    if db_voice_channel is None:
        await interaction.response.send_message('You are not in a managed voice channel', ephemeral=True)
        return False

    if db_voice_channel.owner_id != interaction.user.id:
        await interaction.response.send_message('You are not the owner of this voice channel', ephemeral=True)
        return False
    
    return True


class RenameModal(discord.ui.Modal, title="Rename the squad voice channel"):
    def __init__(self, bot: VoiceSquadBot):
        self.bot = bot
        super().__init__()

    name = discord.ui.TextInput(
        label="What do you want to name your voice channel?",
        style=discord.TextStyle.short,
        max_length=500,
        placeholder="test",
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction[VoiceSquadBot]) -> None:
        async with self.bot.db.create_session() as session:
            if await channel_permision_check(session, interaction):
                if len(self.name.value) < 3:
                    await interaction.response.send_message('Please pick a longer channel name', ephemeral=True)
                    return

                await interaction.user.voice.channel.edit(name=self.name.value)
                await interaction.response.send_message("Channel name has been updated!", ephemeral=True)
                    

class ChangeOwnerView(discord.ui.View):
    def __init__(self, bot: VoiceSquadBot):
        self.bot = bot
        super().__init__(timeout=None)

    @discord.ui.select(custom_id="voice_change_owner_2", cls=discord.ui.UserSelect)
    async def select_channels(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        async with self.bot.db.create_session() as session:
            if await channel_permision_check(session, interaction):
                await update_voice_channel(session, interaction.user.voice.channel.id, {"owner_id": select.values[0].id })
                return await interaction.response.send_message(f'{select.values[0].mention} is now the owner of this voice channel', ephemeral=True)


class VoiceRoleLockView(discord.ui.View):
    def __init__(self, bot: VoiceSquadBot):
        self.bot = bot
        super().__init__(timeout=None)

    @discord.ui.select(custom_id="voice_role_lock_2", cls=discord.ui.RoleSelect, min_values=1, max_values=10)
    async def select_channels(self, interaction: discord.Interaction, select: discord.ui.RoleSelect):
        async with self.bot.db.create_session() as session:
            if await channel_permision_check(session, interaction):
                channel = interaction.user.voice.channel
                guild = interaction.guild
                
                overwrites = {key: value for key, value in channel.overwrites.items() if not isinstance(key, discord.role)}
                overwrites[guild.default_role] = discord.PermissionOverwrite(connect=False)
                
                for role in select.values:
                    overwrites[role] = discord.PermissionOverwrite(connect=True)

                await channel.edit(overwrites=overwrites)
                return await interaction.response.send_message("Allowed only the selected roles to join the channel", ephemeral=True)


class VoiceUserLockView(discord.ui.View):
    def __init__(self, bot: VoiceSquadBot):
        self.bot = bot
        super().__init__(timeout=None)

    @discord.ui.select(custom_id="voice_role_lock_2", cls=discord.ui.UserSelect, min_values=1, max_values=10)
    async def select_channels(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        async with self.bot.db.create_session() as session:
            if await channel_permision_check(session, interaction):
                channel = interaction.user.voice.channel
                guild = interaction.guild
                
                overwrites = {key: value for key, value in channel.overwrites.items() if not isinstance(key, discord.Member)}
                overwrites[guild.default_role] = discord.PermissionOverwrite(connect=False)
                
                for member in select.values:
                    overwrites[member] = discord.PermissionOverwrite(connect=True)

                await channel.edit(overwrites=overwrites)
                return await interaction.response.send_message("Allowed only the selected users to join the channel", ephemeral=True)



class SetLimitView(discord.ui.View):
    def __init__(self, bot: VoiceSquadBot):
        self.bot = bot
        super().__init__(timeout=None)

    
    async def change_voice_limit(self, interaction: discord.Interaction, amount: int):
        async with self.bot.db.create_session() as session:
            if await channel_permision_check(session, interaction):
                await interaction.user.voice.channel.edit(user_limit=amount)
                return await interaction.response.send_message("Voice channel limit set!", ephemeral=True)

    @discord.ui.button(
        label="2",
        custom_id="voice_limit_2",
        style=discord.ButtonStyle.secondary,
    )
    async def set_limit_callback_2(self, interaction: discord.Interaction, button):
        await self.change_voice_limit(interaction, 2)

    @discord.ui.button(
        label="3",
        custom_id="voice_limit_3",
        style=discord.ButtonStyle.secondary,
    )
    async def set_limit_callback_3(self, interaction: discord.Interaction, button):
        await self.change_voice_limit(interaction, 3)

    @discord.ui.button(
        label="4",
        custom_id="voice_limit_4",
        style=discord.ButtonStyle.secondary,
    )
    async def set_limit_callback_4(self, interaction: discord.Interaction, button):
        await self.change_voice_limit(interaction, 4)

    @discord.ui.button(
        label="5",
        custom_id="voice_limit_5",
        style=discord.ButtonStyle.secondary,
    )
    async def set_limit_callback_5(self, interaction: discord.Interaction, button):
        await self.change_voice_limit(interaction, 5)

    @discord.ui.button(
        label="6",
        custom_id="voice_limit_6",
        style=discord.ButtonStyle.secondary,
    )
    async def set_limit_callback_6(self, interaction: discord.Interaction, button):
        await self.change_voice_limit(interaction, 6)

    @discord.ui.button(
        label="Unlimited",
        custom_id="voice_limit_unlimited",
        style=discord.ButtonStyle.success,
    )
    async def set_limit_callback_unlimited(self, interaction: discord.Interaction, button):
        await self.change_voice_limit(interaction, 0)


class VoiceManagementView(discord.ui.View):
    def __init__(self, bot: VoiceSquadBot):
        self.bot = bot
        super().__init__(timeout=None)


    @discord.ui.button(
        label="📝 rename",
        custom_id="voice_rename",
        style=discord.ButtonStyle.success,
        row=0,
    )
    async def rename_callback(self, interaction: discord.Interaction, button):
        async with self.bot.db.create_session() as session:
            if await channel_permision_check(session, interaction):
                await interaction.response.send_modal(RenameModal(self.bot))


    @discord.ui.button(
        label="📍 Set limit",
        custom_id="voice_set_limit",
        style=discord.ButtonStyle.secondary,
        row=0,
    )
    async def set_limit_callback(self, interaction: discord.Interaction, button):
        async with self.bot.db.create_session() as session:
            if await channel_permision_check(session, interaction):
                return await interaction.response.send_message("How many people are allowed in this voice channel?", ephemeral=True, view=SetLimitView(self.bot))


    @discord.ui.button(
        label="🔓 Remove restrictions",
        custom_id="voice_unlock",
        style=discord.ButtonStyle.secondary,
        row=0,
    )
    async def voice_unlock_callback(self, interaction: discord.Interaction, button):
        async with self.bot.db.create_session() as session:
            if await channel_permision_check(session, interaction):
                await interaction.user.voice.channel.edit(user_limit=0)
                channel = interaction.user.voice.channel
                await channel.edit(overwrites={})
                return await interaction.response.send_message("Voice channel unlocked!", ephemeral=True)


    @discord.ui.button(
        label="👑 Change owner",
        custom_id="voice_change_owner",
        style=discord.ButtonStyle.danger,
        row=0,
    )
    async def change_owner_callback(self, interaction: discord.Interaction, button):
        async with self.bot.db.create_session() as session:
            if await channel_permision_check(session, interaction):
                return await interaction.response.send_message("Who do you want as the new owner of the channel?", ephemeral=True, view=ChangeOwnerView(self.bot))


    @discord.ui.button(
        label="🔐 Lock by role",
        custom_id="voice_role_lock",
        style=discord.ButtonStyle.secondary,
        row=1,
    )
    async def role_lock_callback(self, interaction: discord.Interaction, button):
        async with self.bot.db.create_session() as session:
            if await channel_permision_check(session, interaction):
                return await interaction.response.send_message("Which roles do you want to allow?", ephemeral=True, view=VoiceRoleLockView(self.bot))
        

    @discord.ui.button(
        label="🔒 Lock by current users",
        custom_id="voice_current_users_lock",
        style=discord.ButtonStyle.secondary,
        row=1,
    )
    async def current_users_lock_callback(self, interaction: discord.Interaction, button):
        async with self.bot.db.create_session() as session:
            if await channel_permision_check(session, interaction):
                channel = interaction.user.voice.channel
                guild = interaction.guild
                
                overwrites = {key: value for key, value in channel.overwrites.items() if not isinstance(key, discord.Member)}
                overwrites[guild.default_role] = discord.PermissionOverwrite(connect=False)
                
                for member in channel.members:
                    overwrites[member] = discord.PermissionOverwrite(connect=True)

                await channel.edit(overwrites=overwrites)
                return await interaction.response.send_message("Allowed only the current users to join the channel", ephemeral=True)
        

    @discord.ui.button(
        label="🔒 Lock by selected users",
        custom_id="voice_select_users_lock",
        style=discord.ButtonStyle.secondary,
        row=1,
    )
    async def select_users_lock_callback(self, interaction: discord.Interaction, button):
        async with self.bot.db.create_session() as session:
            if await channel_permision_check(session, interaction):
                return await interaction.response.send_message("Which users do you want to allow?", ephemeral=True, view=VoiceUserLockView(self.bot))
        

class Admin(commands.Cog):
    def __init__(self, bot: VoiceSquadBot):
        self.bot = bot
        self.logger = logging.getLogger("admin")


    async def channel_name_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete channel names"""
        async with self.bot.db.create_session() as session:
            stmt = (
                select(ChannelName.name)
                .filter(
                    and_(
                        func.lower(ChannelName.name).startswith(func.lower(current)),
                        ChannelName.server_id == interaction.guild_id,
                    )
                )
                .limit(25)
            )
            users = await session.execute(stmt)
            return [
                app_commands.Choice(name=channel_name, value=channel_name)
                for channel_name in users.scalars()
            ]


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

                    try:
                        voice_channel = await category.create_voice_channel(unused_channel_names[0])
                    except discord.DiscordException as e:
                        await interaction.response.send_message(f"Failed to create the initial voice channel: {e}")
                        return
                    await add_voice_channel(session, interaction.guild_id, voice_channel.id)
                    await interaction.response.send_message("Create the initial voice channel")
                    return
            
            await interaction.response.send_message("The set category is not found within the server")


    @generate_group.command(name="voice-management", description="Generate the voice-management buttons")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def generate_voice_management(self, interaction: discord.Interaction) -> None:
        """Generate the register button"""
        embed = discord.Embed(
            title="Manage squad voice channel",
            description="""
            The first person that joins a squad cusernamehannel, owns the channel until its empty again.
            The owner of the channel can manage it with the buttons below."""
        )
        await interaction.response.send_message(
            embed=embed, view=VoiceManagementView(self.bot)
        )

    
    names_group = app_commands.Group(
        name="names", description="Change the used channel names", parent=group
    )

    @names_group.command(name="add", description="Add a voice channel name")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def add_voice_channel_name(self, interaction: discord.Interaction, channel_name: str) -> None:
        """Add a voice channel name"""
        await interaction.response.defer()
        if interaction.guild is None:
            return  # is already set to guild_only
        async with self.bot.db.create_session() as session:
            await add_voice_channel_name(session, interaction.guild_id, channel_name)
            await interaction.followup.send("Channel name has been added to the list", ephemeral=True)

    @names_group.command(name="remove", description="Remove a voice channel name")
    @app_commands.guild_only()
    @app_commands.autocomplete(
        channel_name=channel_name_autocomplete
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_voice_channel_name(self, interaction: discord.Interaction, channel_name: str) -> None:
        """Add a voice channel name"""
        await interaction.response.defer()
        if interaction.guild is None:
            return  # is already set to guild_only
        async with self.bot.db.create_session() as session:
            await remove_voice_channel_name(session, interaction.guild_id, channel_name)
            await interaction.followup.send("Channel name has been removed from the list", ephemeral=True)

    @names_group.command(name="list", description="List all voice channel names")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def list_voice_channel_names(self, interaction: discord.Interaction) -> None:
        """list all voice channel names"""
        await interaction.response.defer()
        if interaction.guild is None:
            return  # is already set to guild_only
        async with self.bot.db.create_session() as session:
            description = ""
            channel_names = await get_channel_names(self.bot, session, interaction.guild_id, False)
            for channel_name in channel_names:
                description += f"{channel_name}\n"

            if len(channel_names) <= 0:
                await interaction.followup.send("No channel names have been set, bot it using the default set.", ephemeral=True)
                return

            embed = discord.Embed(title="Current custom channel names:", description=description)
            await interaction.followup.send(embed=embed, ephemeral=True)

    @names_group.command(name="export", description="Export all voice channel names")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def export_voice_channel_names(self, interaction: discord.Interaction) -> None:
        """Export all voice channel names"""
        await interaction.response.defer()
        if interaction.guild is None:
            return  # is already set to guild_only
        async with self.bot.db.create_session() as session:
            total, channel_names = await get_channel_names_csv(session, interaction.guild_id)
            if total <= 0:
                await interaction.followup.send("No channel names have been set, bot it using the default set.", ephemeral=True)
                return
            await interaction.followup.send("Current voice channel names:", ephemeral=True, file=channel_names)

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
    bot.add_view(ChangeOwnerView(bot))
    bot.add_view(SetLimitView(bot))
    bot.add_view(VoiceRoleLockView(bot))
    bot.add_view(VoiceUserLockView(bot))
    await bot.add_cog(Admin(bot))
