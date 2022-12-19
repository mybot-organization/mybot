from __future__ import annotations

import asyncio
import logging
import sys
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import select as select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload as selectinload

from .. import config
from .tables import (
    Base,
    GuildDB as GuildDB,
    Poll as Poll,
    PollChoice,
    PollType as PollType,
    PremiumType as PremiumType,
    UserDB as UserDB,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger(__name__)

if config.POSTGRES_PASSWORD is None:
    logger.critical(f"Missing environment variable POSTGRES_PASSWORD.")
    sys.exit(1)

db: AsyncEngine = create_async_engine(
    f"postgresql+asyncpg://{config.POSTGRES_USER}:{config.POSTGRES_PASSWORD}@database:5432/{config.POSTGRES_DB}"
)


async def main():
    async with db.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    guild = GuildDB(guild_id=123, premium_type=PremiumType.NONE, translations_are_public=True)
    poll = Poll(
        message_id=123,
        channel_id=123,
        guild_id=123,
        author_id=123,
        type=PollType.CHOICE,
        multiple=True,
        label="Quel est le ?",
        creation_date=datetime.now(),
        end_date=None,
    )
    async_session = async_sessionmaker(db, expire_on_commit=False)

    async with async_session() as session:
        session.add(guild)
        session.add(poll)

        for i in range(5):
            session.add(PollChoice(poll_id=1, label=str(i)))

        await session.commit()

        stmt = select(Poll).where(Poll.id == 1).options(selectinload(Poll.choices))
        result = await session.execute(stmt)
        poll = result.scalar_one()
        print(poll.message_id)
        print(poll.choices)

        await session.commit()
        print(poll.message_id)


if __name__ == "__main__":
    asyncio.run(main())
