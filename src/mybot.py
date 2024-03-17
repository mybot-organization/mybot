from __future__ import annotations

import logging
import re
import sys
from typing import TYPE_CHECKING, Any, cast

import discord
import topgg as topggpy
from discord.ext import tasks
from discord.ext.commands import AutoShardedBot, errors, when_mentioned  # pyright: ignore[reportMissingTypeStubs]
from discord.utils import get
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from commands_exporter import Feature, extract_features
from core import ExtendedCog, ResponseType, TemporaryCache, config, response_constructor
from core.custom_command_tree import CustomCommandTree
from core.error_handler import ErrorHandler
from core.extended_commands import MiscCommandContext
from core.i18n import Translator

if TYPE_CHECKING:
    from discord import Guild, Thread, User
    from discord.abc import PrivateChannel
    from discord.app_commands import AppCommand
    from discord.guild import GuildChannel
    from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

    from core.db.tables import Base
    from core.errors import MiscCommandError
    from core.extended_commands import MiscCommand

logger = logging.getLogger(__name__)


class MyBot(AutoShardedBot):
    support: Guild
    tree: CustomCommandTree  # pyright: ignore[reportIncompatibleMethodOverride]
    app_commands: list[AppCommand]
    error_handler: ErrorHandler
    topgg: topggpy.DBLClient | None
    topgg_webhook_manager: topggpy.WebhookManager | None
    topgg_current_votes: TemporaryCache[int, bool] = TemporaryCache(60 * 60)  # 1 hour
    features_infos: list[Feature]
    db_engine: AsyncEngine
    async_session: async_sessionmaker[AsyncSession]

    def __init__(self, running: bool = True, startup_sync: bool = False) -> None:
        self.startup_sync: bool = startup_sync
        self.running = running
        self._invite: discord.Invite | None = None

        self.error_handler = ErrorHandler(self)
        if config.TOPGG_TOKEN is not None:
            self.topgg = topggpy.DBLClient(config.TOPGG_TOKEN, default_bot_id=config.BOT_ID)
            self.topgg_webhook_manager = topggpy.WebhookManager()
            (
                self.topgg_webhook_manager.endpoint()
                .route("/topgg_vote")
                .type(topggpy.WebhookType.BOT)
                .auth(config.TOPGG_AUTH or "")
                .callback(self.topgg_endpoint)
                .add_to_manager()
            )

        else:
            self.topgg = None

        intents = discord.Intents().none()
        intents.reactions = True
        intents.guilds = True
        intents.messages = True
        logger.debug("Intents : %s", ", ".join(flag[0] for flag in intents if flag[1]))

        super().__init__(
            command_prefix=when_mentioned,
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
            # "api",
            # "calculator",
            "clear",
            "config",
            # "game",
            "help",
            "poll",
            # "ping",
            # "restore",
            "stats",
            "eval",
            "translate",
        ]
        self.config = config
        self.app_commands = []

    async def setup_hook(self) -> None:
        await self.tree.set_translator(Translator())
        await self.load_extensions()

        if self.topgg is not None and self.topgg_webhook_manager is not None:
            self.update_guild_count_on_bot_lists.start()
            self.loop.create_task(self.topgg_webhook_manager.start(port=8081))

        if self.startup_sync:
            await self.sync_tree()
        else:
            self.app_commands = await self.tree.fetch_commands()

        self.features_infos = extract_features(self)

        await self.connect_db()

    @tasks.loop(minutes=30)
    async def update_guild_count_on_bot_lists(self):
        await self.wait_until_ready()

        if self.topgg is not None:
            try:
                await self.topgg.post_guild_count(guild_count=len(self.guilds), shard_count=self.shard_count)
            except Exception as e:
                logger.exception("Failed to post guild count to top.gg.", exc_info=e)

    async def topgg_endpoint(self, vote_data: topggpy.types.BotVoteData) -> None:
        logger.debug("Received vote from top.gg", extra=vote_data)
        self.dispatch("topgg_vote", vote_data)

    async def get_topgg_vote(self, user_id: int) -> bool:
        if self.topgg is None:
            return True
        if user_id not in self.topgg_current_votes and await self.topgg.get_user_vote(user_id):
            self.topgg_current_votes[user_id] = True
        return self.topgg_current_votes.get(user_id, False)

    async def connect_db(self):
        if config.POSTGRES_PASSWORD is None:
            logger.critical("Missing environment variable POSTGRES_PASSWORD.")
            sys.exit(1)

        self.db_engine = create_async_engine(
            f"postgresql+asyncpg://{config.POSTGRES_USER}:{config.POSTGRES_PASSWORD}@database:5432/{config.POSTGRES_DB}"
        )
        self.async_session = async_sessionmaker(self.db_engine, expire_on_commit=False)

    async def sync_tree(self) -> None:
        for guild_id in self.tree.active_guild_ids:
            try:
                await self.tree.sync(guild=discord.Object(guild_id))
            except discord.Forbidden as e:
                logger.exception("Failed to sync guild %s.", guild_id, exc_info=e)
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
        await self.support_invite  # load the invite

        logger.info("Logged in as : %s", bot_user.name)
        logger.info("ID : %d", bot_user.id)

        # await self.sync_database()

    async def on_message(self, message: discord.Message) -> None:
        await self.wait_until_ready()
        if self.user is None:
            return

        bot_mentioned_regex = re.compile(f"^<@!?{self.user.id}>$")
        if not bot_mentioned_regex.match(message.content.strip()):
            await self.invoke(await self.get_context(message))
            return

        if message.guild is None:
            special_slash_message = False
        else:
            try:
                await self.tree.fetch_commands(guild=message.guild)
            except discord.HTTPException:
                # I suppose that, in very rare case, if the bot is not added as an integration, this will raise an error
                special_slash_message = True
            else:
                special_slash_message = False

        if special_slash_message:
            embed = response_constructor(ResponseType.warning, "MyBot is now using slash commands!").embed
            embed.add_field(
                name="🇫🇷 Salut, moi c'est Toby !",
                value=(
                    "Saches que dorénavant, MyBot fonctionne uniquement avec des **slash commands**. "
                    "C'est le petit menu qui apparaît quand on faire `/` dans un salon.\n"
                    "Si tu ne vois pas les commandes de MyBot apparaître, essayes de réinviter le bot avec ce lien"
                    " ci-dessous !\n"
                    "Si tu rencontres un problème, n'hésite pas à rejoindre le serveur de support.\n\n"
                ),
                inline=False,
            )
            embed.add_field(
                name="🇬🇧 Hi, I'm Toby !",
                value=(
                    "Know that from now on, MyBot only works with **slash commands**. It's the small menu that appears "
                    "when  you type `/` in a channel.\n"
                    "If you don't see MyBot's commands appear, try to reinvite the bot with the link below !\n"
                    "If you encounter a problem, don't hesitate to join the support server.\n\n"
                ),
                inline=False,
            )
        else:
            embed = response_constructor(ResponseType.success, "MyBot, the cute bot at your service!").embed
            embed.add_field(
                name="🇫🇷 Salut, moi c'est Toby !",
                value=(
                    "Je suis un bot qui a pour but de rendre ton serveur plus agréable et plus interactif !\n"
                    "Pour voir la liste des commandes, fais `/` dans un salon.\n"
                    "Commences par faire `/help` pour voir les commandes disponibles.\n"
                    "Si tu rencontres un problème, n'hésite pas à rejoindre le serveur de support.\n\n"
                ),
                inline=False,
            )
            embed.add_field(
                name="🇬🇧 Hi, I'm Toby !",
                value=(
                    "I'm a bot that aims to make your server more pleasant and more interactive !\n"
                    "To see the list of commands, type `/` in a channel.\n"
                    "Start by doing `/help` to see the available commands.\n"
                    "If you encounter a problem, don't hesitate to join the support server.\n\n"
                ),
                inline=False,
            )

        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(
                label="Invite link",
                style=discord.ButtonStyle.url,
                emoji="🔗",
                url=f"https://discord.com/api/oauth2/authorize?client_id={config.BOT_ID}&scope=bot%20applications.commands",  # NOSONAR noqa: E501
            )
        )
        view.add_item(
            discord.ui.Button(
                label="Support invite",
                style=discord.ButtonStyle.url,
                emoji="📢",
                url=(await self.support_invite).url,
            )
        )

        await message.channel.send(embed=embed, view=view)

    @property
    async def support_invite(self) -> discord.Invite:
        if self._invite is None:
            self._invite = get(await self.support.invites(), max_age=0, max_uses=0, inviter=self.user)

        if self._invite is None:  # If invite is STILL None
            channel = tmp if (tmp := self.support.rules_channel) else self.support.channels[0]

            self._invite = await channel.create_invite(reason="Support guild invite.")

        return self._invite

    async def load_extensions(self) -> None:
        for ext in self.extensions_names:
            if not ext.startswith("cogs."):
                ext = "cogs." + ext

            try:
                await self.load_extension(ext)
            except errors.ExtensionError as e:
                logger.exception("Failed to load extension %s.", ext, exc_info=e)
            else:
                logger.info("Extension %s loaded successfully.", ext)

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
        except (discord.NotFound, discord.Forbidden):
            return None
        return channel

    async def get_or_create_db[T: type[Base]](self, session: AsyncSession, table: T, **key: Any) -> T:
        """Get an object from the database. If it doesn't exist, it is created.
        It is CREATEd if the guild doesn't exist in the database.
        """
        guild = await session.get(table, tuple(key.values()))  # pyright: ignore[reportArgumentType]

        if guild is None:
            guild = table(**key)
            session.add(guild)
            await session.flush()

        return guild

    def misc_commands(self):
        """Get all the misc commands.

        Returns:
            _type_: the list of misc commands
        """
        misc_commands: list[MiscCommand[Any, ..., Any]] = []
        for cog in self.cogs.values():
            if isinstance(cog, ExtendedCog):
                misc_commands.extend(cog.get_misc_commands())
        return misc_commands

    async def on_error(self, event_method: str, /, *args: Any, **kwargs: Any) -> None:
        del args, kwargs  # unused
        logger.error("An error occurred in %s.", event_method, exc_info=True)

    async def on_misc_command_error(
        self,
        context: MiscCommandContext[MyBot],
        error: MiscCommandError,
    ) -> None:
        await self.error_handler.handle_misc_command_error(context, error)
