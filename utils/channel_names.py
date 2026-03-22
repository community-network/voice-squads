import csv
import io
import traceback
import discord
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from database.dto.channel_names import ChannelName
from sqlalchemy import and_, func


async def get_channel_names(bot, session: AsyncSession, server_id: int, include_defaults: bool = True) -> list[str]:
    stmt = (
        select(ChannelName.name)
        .filter(ChannelName.server_id == server_id)
    )
    res = (await session.execute(stmt)).all()
    formatted_res = [channel[0] for channel in res]

    if include_defaults and len(formatted_res) == 0:
        return bot.config.bot.default_channel_names

    return formatted_res


async def get_channel_names_csv(session: AsyncSession, server_id: int) -> tuple[int, discord.File]:
    stmt = (
        select(ChannelName)
        .filter(ChannelName.server_id == server_id)
    )
    res = (await session.execute(stmt)).all()
    total = len(res)
    with io.StringIO() as data_stream:
        outcsv = csv.writer(data_stream)
        outcsv.writerow(ChannelName.__table__.columns.keys())     
        for row in res:
            print(row)
            outcsv.writerow([row[0].id, row[0].server_id, row[0].name])
        data_stream.seek(0)
        return (total, discord.File(data_stream, filename="channel_names.csv"))



async def add_voice_channel_name(session: AsyncSession, server_id: int, channel_name: str):
    channel = dict(server_id=server_id, name=channel_name)
    stmt = insert(ChannelName).values(channel)
    await session.execute(stmt)
    await session.commit()


async def remove_voice_channel_name(session: AsyncSession, server_id: int, channel_name: str):
    stmt = (
        select(ChannelName)
        .filter(
            and_(
                func.lower(ChannelName.name) == func.lower(channel_name),
                ChannelName.server_id == server_id,
            )
        )
        .limit(1)
    )
    result = await session.execute(stmt)
    voice_channel = result.scalar_one_or_none()
    await session.delete(voice_channel)
    await session.commit()