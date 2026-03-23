"""discord api connection"""

import asyncio
import logging
import os
import discord
from discord.ext import commands
from config import load_config
from database.connection import DatabaseSingleton
from logger import setup_logger
from utils.channel_names import get_channel_names
from utils.server_settings import add_guild, get_guild, has_guild, has_guild_category
from utils.voice_channels import add_voice_channel, get_voice_channel, get_voice_channels, remove_voice_channel, update_voice_channel
from sqlalchemy.ext.asyncio import AsyncSession


env_config = load_config()

logger = logging.getLogger("bot")
setup_logger(logger)

class VoiceSquadBot(commands.AutoShardedBot):
    """Bot setup class."""

    def __init__(self, *args, **kwargs):
        self.logger = logger
        self.config = env_config
        self.db = DatabaseSingleton(env_config.db)
        super().__init__(*args, **kwargs)

    async def setup_hook(self):
        await self.db.init_db()
        self.remove_command("help")
        await self.load_cogs()
        async with self.db.create_session() as session:
            async for guild in self.fetch_guilds():
                if not await has_guild(session, guild.id):
                    await add_guild(session, guild, {})
                    logger.info(f'Added guild "{guild.name}"')


        logger.info("Bot started")

    async def load_cogs(self):
        for file in os.listdir(os.path.dirname(__file__) + "/cogs"):
            if file.endswith(".py"):
                name = file[:-3]
                await bot.load_extension(f"cogs.{name}")
                self.logger.info(f"Loaded cog: {name}")


intents = discord.Intents.default()
intents.voice_states = True
bot = VoiceSquadBot(command_prefix="!", intents=intents)

async def get_channels_in_db(session: AsyncSession, member: discord.Member, category: discord.CategoryChannel):
    db_voice_channels = await get_voice_channels(session, member.guild.id)
    return [channel for channel in category.voice_channels if channel.id in db_voice_channels]

async def on_voice_channel_join(session: AsyncSession, member: discord.Member, after: discord.VoiceState):
    if not await has_guild_category(session, member.guild.id, after.channel.category_id):
        return
    
    db_channel = await get_voice_channel(session,  member.guild.id, after.channel.id)
    if db_channel is None: 
        return
    
    category = after.channel.category
    unused_voice_channel_names = await get_channel_names(bot, session, member.guild.id)
    channels_in_db = await get_channels_in_db(session, member, category)

    if len(after.channel.members) == 1:
        await update_voice_channel(session, after.channel.id, {"owner_id": member.id })

    total_empty_channels = 0
    for channel in channels_in_db:
        if len(channel.members) == 0:
            total_empty_channels += 1
        if channel.name in unused_voice_channel_names:
            unused_voice_channel_names.remove(channel.name)

    if (total_empty_channels == 0 and len(unused_voice_channel_names) > 0):
        guild_settings = await get_guild(session, member.guild.id)
        new_channel = await category.create_voice_channel(unused_voice_channel_names[0], position=after.channel.position)
        if guild_settings.default_user_limit is not None:
            await new_channel.edit(user_limit=guild_settings.default_user_limit)
        await add_voice_channel(session, member.guild.id, new_channel.id)

async def on_voice_channel_leave(session: AsyncSession, member: discord.Member, before: discord.VoiceState):
    if not await has_guild_category(session, member.guild.id, before.channel.category_id):
        return
    
    db_channel = await get_voice_channel(session,  member.guild.id, before.channel.id)
    if db_channel is None:
        return

    category = before.channel.category
    channels_in_db = await get_channels_in_db(session, member, category)
    empty_channels = 0
    for channel in reversed(channels_in_db):
        total_users = len(channel.members)
        if empty_channels > 0 and total_users <= 0:
            await remove_voice_channel(session, member.guild.id, channel.id)
            await channel.delete()
        elif len(channel.members) <= 0:
            empty_channels += 1

        
    

@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState | None, after: discord.VoiceState | None):
    async with bot.db.create_session() as session:
        if member.guild.id is None:
            return
        if (before.channel is None and after.channel is not None): # join
            await on_voice_channel_join(session, member, after)

        if before.channel is not None and after.channel is None: # leave
            await on_voice_channel_leave(session, member, before)

        if before.channel is not None and after.channel is not None and before.channel.id != after.channel.id:
            await on_voice_channel_leave(session, member, before)
            await on_voice_channel_join(session, member, after)

                

@bot.event
async def on_guild_join(guild: discord.Guild):
    async with bot.db.create_session() as session:
        if not await has_guild(session, guild.id):
            await add_guild(session, guild, {})
            logger.info(f'Added guild "{guild.name}"')

@bot.event
async def on_command_error(ctx, error):
    """dont give a error if a command doesn't exist"""
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingRequiredArgument):
        return
    elif isinstance(error, commands.MissingRole):
        return
    elif isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(
            color=0xE74C3C, description="Your not allowed to use this command"
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.NoPrivateMessage):
        embed = discord.Embed(
            color=0xE74C3C,
            description="This command can only be used within a community, not in DM",
        )
        await ctx.send(embed=embed)
    else:
        raise error



@bot.event
async def on_ready():
    """After bot is logged into discord"""
    await bot.tree.sync()

async def main() -> None:
    async with bot:
        await bot.start(env_config.bot.discord_bot_token)


if __name__ == "__main__":
    asyncio.run(main())