from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING, Optional, cast

import discord
from discord.ext.commands import AutoShardedBot, errors  # pyright: ignore[reportMissingTypeStubs]

from utils.constants import SUPPORT_GUILD_ID
from utils.custom_command_tree import CustomCommandTree
from utils.i18n import Translator

if TYPE_CHECKING:
    from discord import Guild
    from sqlalchemy.ext.asyncio import AsyncEngine


logger = logging.getLogger(__name__)


class MyBot(AutoShardedBot):
    db: AsyncEngine
    support: Guild
    tree: CustomCommandTree  # type: ignore

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

        self.extensions_names: list[str] = ["cogs.clear", "cogs.admin"]

    async def setup_hook(self) -> None:
        await self.tree.set_translator(Translator())
        await self.load_extensions()

        await self.sync_tree()

    async def sync_tree(self) -> None:
        for guild_id in self.tree.active_guild_ids:
            await self.tree.sync(guild=discord.Object(guild_id))
        await self.tree.sync()

    async def on_ready(self) -> None:
        bot_user = cast(discord.ClientUser, self.user)  # Bot is logged in, so it's a ClientUser

        activity = discord.Game("WIP!")
        await self.change_presence(status=discord.Status.online, activity=activity)

        tmp = self.get_guild(SUPPORT_GUILD_ID)
        if not tmp:
            logger.critical("Support server cannot be retrieved")
            sys.exit(1)
        self.support = tmp

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
