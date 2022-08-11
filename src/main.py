from __future__ import annotations

from os import environ
import sys
from typing import TYPE_CHECKING, cast

import discord
from discord.ext.commands import AutoShardedBot  # type: ignore # Stubs missing from discord.py

from utils.custom_command_tree import CustomCommandTree
from utils.db import db
from utils.logger import INFO, create_logger

if TYPE_CHECKING:
    from logging import Logger

    from sqlalchemy.ext.asyncio import AsyncEngine


LOG_LEVEL = int(tmp) if (tmp := environ.get("LOG_LEVEL")) and tmp.isdigit() else INFO
logger = create_logger(__name__, level=LOG_LEVEL)


class MyBot(AutoShardedBot):
    logger: Logger = logger
    db: AsyncEngine = db

    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.members = True
        intents.presences = True

        super().__init__(
            command_prefix="unimplemented",  # Maybe consider use of IntegrationBot instead of AutoShardedBot
            tree_cls=CustomCommandTree,
            member_cache_flags=discord.MemberCacheFlags.all(),
            chunk_guilds_at_startup=True,
            allowed_mentions=discord.AllowedMentions.none(),
            intents=intents,
            help_command=None,
        )

        self.extensions_names: list[str] = []

    async def setup_hook(self) -> None:
        for ext in self.extensions_names:
            try:
                await self.load_extension(ext)
            except Exception as e:
                logger.error(f"Failed to load extension {ext}.", exc_info=e)

    async def on_ready(self) -> None:
        bot_user = cast(discord.ClientUser, self.user)  # Bot is logged in, so it's a ClientUser

        await self.tree.sync()

        activity = discord.Game("WIP!")
        await self.change_presence(status=discord.Status.online, activity=activity)

        logger.info(f"Logged in as : {bot_user.name}")
        logger.info(f"ID : {bot_user.id}")


if __name__ == "__main__":
    mybot = MyBot()
    try:
        mybot.run(environ["BOT_TOKEN"], reconnect=True)
    except KeyError as e:
        logger.critical(f"Missing environment variable {e}.")
        sys.exit(1)
