from __future__ import annotations

import asyncio
import datetime
import logging
import re
import time
from enum import Enum, auto
from typing import TYPE_CHECKING, AsyncGenerator, Awaitable, Callable, NamedTuple, cast

import discord
from discord import app_commands, ui
from discord.app_commands import locale_str as __
from discord.ext.commands import Cog  # pyright: ignore[reportMissingTypeStubs]
from discord.utils import get
from typing_extensions import Self

from utils import ResponseType, response_constructor
from utils.checks import MaxConcurrency
from utils.errors import BaseError, MaxConcurrencyReached
from utils.i18n import _

if TYPE_CHECKING:
    from discord import TextChannel, Thread, VoiceChannel

    from mybot import MyBot
    from utils._types import Snowflake

    PurgeableChannel = TextChannel | VoiceChannel | Thread


logger = logging.getLogger(__name__)


class Has(Enum):
    image = auto()
    video = auto()
    audio = auto()
    stickers = auto()
    files = auto()
    any_attachment = auto()
    embed = auto()
    link = auto()
    mention = auto()
    discord_invite = auto()


class Pinned(Enum):
    include = 1
    exclude = 2
    only = 3


class ClearFilters(NamedTuple):
    user_id: Snowflake | None
    role_id: Snowflake | None
    pattern: re.Pattern[str] | None
    # attachment_type: Has | None
    before: datetime.datetime | None
    after: datetime.datetime | None
    max_length: int | None
    min_length: int | None
    pinned: Pinned


class Clear(Cog):
    def __init__(self, bot: MyBot):
        self.bot: MyBot = bot

        self.clear_max_concurrency = MaxConcurrency(1, key=Clear.ChannelBucket, wait=False)

    @staticmethod
    def ChannelBucket(inter: discord.Interaction):
        return inter.channel_id

    @app_commands.command(description=__("Delete multiple messages with some filters."), extras={"beta": True})
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.guild_only()
    @app_commands.choices(
        has=[
            app_commands.Choice(name=__("image"), value=Has.image.value),
            app_commands.Choice(name=__("video"), value=Has.video.value),
            app_commands.Choice(name=__("audio"), value=Has.audio.value),
            app_commands.Choice(name=__("stickers"), value=Has.stickers.value),
            app_commands.Choice(name=__("files"), value=Has.files.value),
            app_commands.Choice(name=__("any attachment"), value=Has.any_attachment.value),
            app_commands.Choice(name=__("embed"), value=Has.embed.value),
            app_commands.Choice(name=__("link (any URL)"), value=Has.link.value),
            app_commands.Choice(name=__("mention"), value=Has.mention.value),
            app_commands.Choice(name=__("discord invitation"), value=Has.discord_invite.value),
        ],
        pinned=[
            app_commands.Choice(name=__("include"), value=Pinned.include.value),
            app_commands.Choice(name=__("exclude"), value=Pinned.exclude.value),
            app_commands.Choice(name=__("only"), value=Pinned.only.value),
        ],
    )
    @app_commands.describe(
        amount=__("The amount of messages to delete."),
        user=__("Delete only messages from the specified user."),
        role=__("Delete only messages whose user has the specified role."),
        search=__(
            "Delete only messages that match the specified search (can be regex)."
        ),  # e.g. regex:hello will delete the message "hello world".
        has=__(
            "Delete only messages that contains the selected entry. #TODO"
        ),  # e.g. attachement:image will delete messages that has an image attached.
        length=__("Delete only messages where length match the specified entry. (e.g. '<=100', '5', '>10') #TODO"),
        before=__("Delete only messages sent before the specified message or date. (yyyy-mm-dd) #TODO"),
        after=__("Delete only messages sent after the specified message or date.  (yyyy-mm-dd) #TODO"),
        pinned=__(
            'Include/exclude pinned messages in deletion, or deletes "only" pinned messages. (default to exclude)'
        ),
    )
    @app_commands.rename(
        amount=__("amount"),
        user=__("user"),
        role=__("role"),
        search=__("search"),
        has=__("has"),
        length=__("length"),
        before=__("before"),
        after=__("after"),
        pinned=__("pinned"),
    )
    async def clear(
        self,
        inter: discord.Interaction,
        amount: int,
        user: discord.User | None = None,
        role: discord.Role | None = None,
        search: str | None = None,
        has: Has | None = None,
        length: str | None = None,
        before: str | None = None,
        after: str | None = None,
        pinned: Pinned = Pinned.exclude,
    ):
        await self.clear_max_concurrency.acquire(inter)

        if inter.channel is None:
            raise Exception(f"{inter} had its channel set to None")

        # Because of @guild_only, we can assume that the channel is a guild channel
        # Also, the channel should not be able to be a ForumChannel or StageChannel or CategoryChannel
        channel = cast("PurgeableChannel", inter.channel)

        if not 0 < amount < 251:
            raise ValueError(_("You must supply a number between 1 and 250. (0 < {amount} < 251)", amount=amount))

        if search:
            pattern: re.Pattern[str] | None = re.compile(
                search, re.MULTILINE
            )  # TODO: handle raise re.error if not a good pattern
        else:
            pattern = None

        # prebuild_pattern = None  # TODO
        # attachment_type = None  # TODO
        max_length = None  # TODO
        min_length = None  # TODO
        before = None  # TODO
        after = None  # TODO

        filters = ClearFilters(
            user_id=user.id if user else None,
            role_id=role.id if role else None,
            pattern=pattern,
            before=before,
            after=after,
            max_length=max_length,
            min_length=min_length,
            pinned=pinned,
        )

        class CancelClearView(ui.View):
            pressed: bool = False

            async def interaction_check(self, interaction: discord.Interaction) -> bool:
                await interaction.response.defer()
                return interaction.user.id == inter.user.id

            @ui.button(label=_("Cancel", _locale=inter.locale), style=discord.ButtonStyle.red)
            async def cancel(self, inter: discord.Interaction, button: ui.Button[Self]):
                self.pressed = True
                self.stop()

        view = CancelClearView(timeout=3 * 60)

        await inter.response.send_message(
            **response_constructor(ResponseType.info, _("Clearing {amount} message(s)...", amount=amount)),
            ephemeral=True,
            view=view,
        )

        deleted_messages: list[discord.Message] = []
        try:
            tasks = (
                asyncio.create_task(view.wait()),
                asyncio.create_task(self._clear(channel, amount, deleted_messages, filters)),
            )
            done, pending = await asyncio.wait(
                tasks,
                return_when=asyncio.FIRST_COMPLETED,
            )
        except discord.HTTPException:
            raise BaseError(f"Could not delete messages in {channel.mention}.")  # TODO: handle this better
        else:
            for task in pending:
                task.cancel()
            for task in done:
                task.exception()

        if tasks[0] in done:
            text_response = (
                _("Cannot clear more than 3 minutes. {} message(s) deleted.", len(deleted_messages)),
                _("Clear cancelled. {} message(s) deleted.", len(deleted_messages)),
            )
            await inter.edit_original_response(
                **response_constructor(ResponseType.warning, text_response[view.pressed]),
                view=None,
            )
        else:
            await inter.edit_original_response(
                **response_constructor(ResponseType.success, _("{} message(s) deleted.", len(deleted_messages))),
                view=None,
            )

        await self.clear_max_concurrency.release(inter)

    @clear.error
    async def release_concurrency(self, inter: discord.Interaction, error: app_commands.AppCommandError):
        if not isinstance(error, MaxConcurrencyReached):
            await self.clear_max_concurrency.release(inter)

    async def _clear(
        self,
        channel: PurgeableChannel,
        amount: int,
        deleted_messages: list[discord.Message],
        filters: ClearFilters,
    ) -> None:
        iterator: AsyncGenerator[discord.Message, None] = self.filtered_history(channel, amount, filters)

        async def _single_delete_strategy(messages: list[discord.Message]) -> None:
            for m in messages:
                await asyncio.sleep(2)
                await m.delete()
                deleted_messages.append(m)

        async def _bulk_delete_strategy(messages: list[discord.Message]) -> None:
            await channel.delete_messages(messages)  # long process for some reason
            deleted_messages.extend(messages)

        minimum_time: int = int((time.time() - 14 * 24 * 60 * 60) * 1000.0 - 1420070400000) << 22
        strategy: Callable[[list[discord.Message]], Awaitable[None]] = _bulk_delete_strategy

        to_delete: list[discord.Message] = []

        async for msg in iterator:
            if len(to_delete) == 100:
                await strategy(to_delete)
                to_delete = []

            # older than 14 days old
            if msg.id < minimum_time and strategy is not _single_delete_strategy:
                if len(to_delete) >= 1:
                    await strategy(to_delete)
                    to_delete = []
                strategy = _single_delete_strategy

            to_delete.append(msg)
        else:
            if len(to_delete) >= 1:
                await strategy(to_delete)

                if strategy is channel.delete_messages:
                    deleted_messages.extend(to_delete)

    @staticmethod
    async def filtered_history(
        channel: PurgeableChannel, amount: int, filters: ClearFilters
    ) -> AsyncGenerator[discord.Message, None]:
        guild = channel.guild

        limit = amount if not any(filters) else None
        count = 0

        async for msg in channel.history(limit=limit):
            if filters.user_id and msg.author.id != filters.user_id:
                continue
            if filters.role_id:
                try:
                    user = guild.get_member(msg.author.id) or await guild.fetch_member(msg.author.id)
                except discord.HTTPException:
                    continue

                if get(user.roles, id=filters.role_id) is None:
                    continue
            if filters.pattern and not bool(filters.pattern.search(msg.content)):
                continue
            if filters.pinned == Pinned.exclude and msg.pinned:
                continue
            if filters.pinned == Pinned.only and not msg.pinned:
                continue

            count += 1

            if count > amount:
                break

            yield msg


async def setup(bot: MyBot):
    await bot.add_cog(Clear(bot))
