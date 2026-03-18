from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession
from database.dto.channel_names import ChannelName


async def get_channel_names(bot, session: AsyncSession, server_id: int) -> list[str]:
    stmt = (
        select(ChannelName.name)
        .filter(ChannelName.server_id == server_id)
    )
    res = (await session.execute(stmt)).all()
    formatted_res = [channel[0] for channel in res]

    if len(formatted_res) == 0:
        return bot.config.bot.default_channel_names

    return formatted_res