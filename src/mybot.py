from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING, cast

import discord
from discord.ext.commands import AutoShardedBot, errors  # pyright: ignore[reportMissingTypeStubs]
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from commands_exporter import features_to_dict
from utils import config, db
from utils.custom_command_tree import CustomCommandTree
from utils.i18n import Translator

if TYPE_CHECKING:
    from discord import Guild
    from discord.app_commands import AppCommand
    from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger(__name__)


class MyBot(AutoShardedBot):
    support: Guild
    tree: CustomCommandTree  # type: ignore

    def __init__(self, running: bool = True, startup_sync: bool = False) -> None:
        self.startup_sync: bool = startup_sync
        self.running = running

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

        self.extensions_names: list[str] = ["clear", "help", "admin", "stats"]
        self.config = config

    async def setup_hook(self) -> None:
        await self.tree.set_translator(Translator())
        await self.load_extensions()

        if self.startup_sync:
            await self.sync_tree()

        self.features_infos = features_to_dict(self)

        await self.connect_db()

    async def connect_db(self):
        if config.POSTGRES_PASSWORD is None:
            logger.critical(f"Missing environment variable POSTGRES_PASSWORD.")
            sys.exit(1)

        self.db_engine: AsyncEngine = create_async_engine(
            f"postgresql+asyncpg://{config.POSTGRES_USER}:{config.POSTGRES_PASSWORD}@database:5432/{config.POSTGRES_DB}"
        )
        self.async_session = async_sessionmaker(self.db_engine, expire_on_commit=False)

    async def sync_tree(self) -> None:
        for guild_id in self.tree.active_guild_ids:
            await self.tree.sync(guild=discord.Object(guild_id))
        self.app_commands: list[AppCommand] = await self.tree.sync()

    async def sync_database(self) -> None:
        stmt = db.select(db.GuildDB.guild_id)
        async with self.async_session() as session:
            for guild in self.guilds:
                pass

    async def on_ready(self) -> None:
        bot_user = cast(discord.ClientUser, self.user)  # Bot is logged in, so it's a ClientUser

        activity = discord.Game("WIP!")
        await self.change_presence(status=discord.Status.online, activity=activity)

        tmp = self.get_guild(self.config.SUPPORT_GUILD_ID)
        if not tmp:
            logger.critical("Support server cannot be retrieved")
            sys.exit(1)
        self.support = tmp

        logger.info(f"Logged in as : {bot_user.name}")
        logger.info(f"ID : {bot_user.id}")

        await self.sync_database()

    async def load_extensions(self) -> None:
        for ext in self.extensions_names:
            if not ext.startswith("cogs."):
                ext = "cogs." + ext

            try:
                await self.load_extension(ext)
            except errors.ExtensionError as e:
                logger.error(f"Failed to load extension {ext}.", exc_info=e)
            else:
                logger.info(f"Extension {ext} loaded successfully.")
