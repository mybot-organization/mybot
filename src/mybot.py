from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional, cast

import discord
from discord.ext.commands import AutoShardedBot, errors  # pyright: ignore[reportMissingTypeStubs]

from utils.custom_command_tree import CustomCommandTree
from utils.i18n import Translator

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine


logger = logging.getLogger(__name__)


class MyBot(AutoShardedBot):
    db: AsyncEngine

    def __init__(self, database_engine: Optional[AsyncEngine] = None) -> None:
        if database_engine:
            self.db = database_engine

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

        self.extensions_names: list[str] = ["cogs.clear"]

    async def setup_hook(self) -> None:
        await self.tree.set_translator(Translator())
        await self.load_extensions()

    async def on_ready(self) -> None:
        bot_user = cast(discord.ClientUser, self.user)  # Bot is logged in, so it's a ClientUser

        await self.tree.sync()

        activity = discord.Game("WIP!")
        await self.change_presence(status=discord.Status.online, activity=activity)

        logger.info(f"Logged in as : {bot_user.name}")
        logger.info(f"ID : {bot_user.id}")

    async def load_extensions(self) -> None:
        for ext in self.extensions_names:
            try:
                await self.load_extension(ext)
            except errors.ExtensionError as e:
                logger.error(f"Failed to load extension {ext}.", exc_info=e)
            else:
                logger.info(f"Extension {ext} loaded successfully.")
