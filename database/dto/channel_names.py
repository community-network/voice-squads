from sqlalchemy import BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from database.connection import Base


class ChannelName(Base):
    __tablename__ = "channel_names"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    server_id: Mapped[int] = mapped_column(BigInteger, index=True)
    name: Mapped[str]
