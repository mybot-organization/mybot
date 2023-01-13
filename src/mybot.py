from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING, cast

import discord
from discord.ext import commands
from discord.ext.commands import AutoShardedBot, errors  # pyright: ignore[reportMissingTypeStubs]
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from commands_exporter import extract_features
from core import config, db
from core.custom_command_tree import CustomCommandTree
from core.i18n import Translator
from core.special_cog import SpecialCog

if TYPE_CHECKING:
    from discord import Guild, Thread, User
    from discord.abc import PrivateChannel
    from discord.app_commands import AppCommand
    from discord.guild import GuildChannel
    from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

    from core.misc_command import MiscCommand

logger = logging.getLogger(__name__)


class MyBot(AutoShardedBot):
    support: Guild
    tree: CustomCommandTree  # type: ignore
    app_commands: list[AppCommand]

    def __init__(self, running: bool = True, startup_sync: bool = False) -> None:
        self.startup_sync: bool = startup_sync
        self.running = running

        intents = discord.Intents().none()
        intents.reactions = True
        intents.guilds = True
        logger.debug(f"Intents : {', '.join(flag[0] for flag in intents if flag[1])}")

        super().__init__(
            command_prefix="!",  # Maybe consider use of IntegrationBot instead of AutoShardedBot
            tree_cls=CustomCommandTree,
            member_cache_flags=discord.MemberCacheFlags.none(),
            chunk_guilds_at_startup=False,
            allowed_mentions=discord.AllowedMentions.none(),
            intents=intents,
            help_command=None,
        )

        # Keep an alphabetic order, it is more clear.
        self.extensions_names: list[str] = [
            "admin",
            "api",
            "calculator",
            "clear",
            "config",
            "game",
            "help",
            "poll",
            "ping",
            "restore",
            "stats",
            "translate",
        ]
        self.config = config
        self.app_commands = []

    async def setup_hook(self) -> None:
        await self.tree.set_translator(Translator())
        await self.load_extensions()

        if self.startup_sync:
            await self.sync_tree()
        else:
            self.app_commands = await self.tree.fetch_commands()

        self.features_infos = extract_features(self)

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
            try:
                await self.tree.sync(guild=discord.Object(guild_id))
            except discord.Forbidden as e:
                logger.error(f"Failed to sync guild {guild_id}.", exc_info=e)
        self.app_commands = await self.tree.sync()

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

        # await self.sync_database()

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

    async def getch_user(self, id: int, /) -> User | None:
        """Get a user, or fetch it if not in cache.

        Args:
            id (int): the user id

        Returns:
            User | None: the user, or None if not found.
        """
        try:
            usr = self.get_user(id) or await self.fetch_user(id)
        except discord.NotFound:
            return None
        else:
            return usr

    async def getch_channel(self, id: int, /) -> GuildChannel | PrivateChannel | Thread | None:
        """Get a channel, or fetch is if not in cache.

        Args:
            id (int): the channel id

        Returns:
            GuildChannel | PrivateChannel | Thread | None: the channel, or None if not found.
        """
        try:
            channel = self.get_channel(id) or await self.fetch_channel(id)
        except discord.NotFound | discord.Forbidden:
            return None
        else:
            return channel

    async def get_guild_db(self, guild_id: int, session: AsyncSession | None = None) -> db.GuildDB:
        """Get a GuildDB object from the database.
        It is CREATEd if the guild doesn't exist in the database.

        Args:
            guild_id (int): the guild id

        Returns:
            db.GuildDB: the GuildDB object
        """
        if new_session := session is None:
            session = self.async_session()

        stmt = db.select(db.GuildDB).where(db.GuildDB.guild_id == guild_id)
        result = await session.execute(stmt)
        guild = result.scalar_one_or_none()

        if guild is None:
            guild = db.GuildDB(guild_id=guild_id, premium_type=db.PremiumType.NONE, translations_are_public=False)
            session.add(guild)
            await session.commit()

        if new_session:
            await session.close()

        return guild

    def misc_commands(self):
        """Get all the misc commands.

        Returns:
            _type_: the list of misc commands
        """
        misc_commands: list[MiscCommand] = []
        for cog in self.cogs.values():
            if isinstance(cog, SpecialCog):
                for misc_command in cog.get_misc_commands():
                    misc_commands.append(misc_command)
        return misc_commands
