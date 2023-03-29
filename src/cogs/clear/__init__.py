from __future__ import annotations

import asyncio
import logging
import time
from enum import Enum, auto
from typing import TYPE_CHECKING, AsyncGenerator, Awaitable, Callable, cast

import discord
from discord import app_commands, ui
from discord.app_commands import Transform, locale_str as __
from discord.ext.commands import Cog  # pyright: ignore[reportMissingTypeStubs]
from typing_extensions import Self

from core import Menu, MessageDisplay, ResponseType, response_constructor
from core.checkers import MaxConcurrency
from core.errors import BadArgument, MaxConcurrencyReached, NonSpecificError, UnexpectedError
from core.i18n import _
from core.utils import async_all

from .clear_transformers import PinnedTransformer, RegexTransformer, RoleTransformer, UserTransformer
from .filters import Filter, PinnedFilter, RegexFilter, RoleFilter, UserFilter

if TYPE_CHECKING:
    from discord import TextChannel, Thread, VoiceChannel

    from mybot import MyBot

    AllowPurgeChannel = TextChannel | VoiceChannel | Thread


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


def channel_bucket(inter: discord.Interaction):
    return inter.channel_id


class Clear(Cog):
    def __init__(self, bot: MyBot):
        self.bot: MyBot = bot

        self.clear_max_concurrency = MaxConcurrency(1, key=channel_bucket, wait=False)

    @app_commands.command(
        description=__("Delete multiple messages with some filters."),
        extras={"beta": True},
    )
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
    )
    @app_commands.describe(
        amount=__("The amount of messages to delete."),
        user=__("Delete only messages from the specified user."),
        role=__("Delete only messages whose user has the specified role."),
        pattern=__(
            "Delete only messages that match the specified search (can be regex)."
        ),  # e.g. regex:hello will delete the message "hello world".
        has=__(
            "Delete only messages that contains the selected entry. #TODO"
        ),  # e.g. attachement:image will delete messages that has an image attached.
        length=__("Delete only messages where length match the specified entry. (e.g. '<=100', '5', '>10') #TODO"),
        before=__("Delete only messages sent before the specified message or date. (yyyy-mm-dd) #TODO"),
        after=__("Delete only messages sent after the specified message or date. (yyyy-mm-dd) #TODO"),
        pinned=__(
            'Include/exclude pinned messages in deletion, or deletes "only" pinned messages. (default to exclude)'
        ),
    )
    @app_commands.rename(
        amount=__("amount"),
        user=__("user"),
        role=__("role"),
        pattern=__("search"),
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
        user: Transform[UserFilter, UserTransformer] | None = None,
        role: Transform[RoleFilter, RoleTransformer] | None = None,
        pattern: Transform[RegexFilter, RegexTransformer] | None = None,
        has: Has | None = None,
        length: str | None = None,
        before: str | None = None,
        after: str | None = None,
        pinned: Transform[PinnedFilter, PinnedTransformer] = PinnedFilter.default(),
    ):
        await self.clear_max_concurrency.acquire(inter)

        if inter.channel is None:
            raise UnexpectedError(f"{inter} had its channel set to None")

        if not 0 < amount < 251:
            raise BadArgument(_("You must supply a number between 1 and 250. (0 < {amount} < 251)", amount=amount))

        # Because of @guild_only, we can assume that the channel is a guild channel
        # Also, the channel should not be able to be a ForumChannel or StageChannel or CategoryChannel

        available_filters: list[Filter | None] = [pinned, user, role, pattern]  # , has, length, before, after]
        active_filters: list[Filter] = [f for f in available_filters if f is not None]

        job = ClearWorker(self.bot, inter, amount, active_filters)
        await job.start()
        await self.clear_max_concurrency.release(inter)

    @clear.error
    async def release_concurrency(self, inter: discord.Interaction, error: app_commands.AppCommandError):
        if not isinstance(error, MaxConcurrencyReached):
            await self.clear_max_concurrency.release(inter)


class ClearWorker:
    def __init__(
        self,
        bot: MyBot,
        inter: discord.Interaction,
        amount: int,
        filters: list[Filter],
    ):
        self._deleted_messages: list[discord.Message] = []
        self.analyzed_messages: int = 0
        self.deletion_planned: int = 0
        self.deletion_goal: int = amount
        self.filters = filters
        self.inter = inter
        self.bot = bot
        self.channel = cast("AllowPurgeChannel", inter.channel)

    @property
    def deleted_messages(self) -> int:
        return len(self._deleted_messages)

    def working_display(self) -> MessageDisplay:
        display = response_constructor(
            ResponseType.info,
            _("Clearing {amount} message(s)...", amount=self.deletion_goal, _locale=self.inter.locale),
        )
        display.embed.description = _(
            ("Analyzed: {analyzed}\n" "Deleted: {deleted}/{goal}\n" "Planned for deletion: {planned}"),
            analyzed=self.analyzed_messages,
            deleted=self.deleted_messages,
            goal=self.deletion_goal,
            planned=self.deletion_planned,
            _locale=self.inter.locale,
        )
        return display

    async def start(self):
        view = await CancelClearView(self.bot, self.inter.user.id).build()

        await self.inter.response.send_message(
            **self.working_display(),
            ephemeral=True,
            view=view,
        )

        try:
            tasks = (
                asyncio.create_task(view.wait()),
                asyncio.create_task(self._clear()),
                asyncio.create_task(self.periodic_display_update()),
            )
            done, pending = await asyncio.wait(
                tasks,
                return_when=asyncio.FIRST_COMPLETED,
            )
        except discord.HTTPException as e:
            raise NonSpecificError(f"Could not delete messages in {self.channel.mention}.") from e

        for task in pending:
            task.cancel()
        for task in done:
            task.exception()

        if tasks[0] in done:
            text_response = (
                _("Cannot clear more than 3 minutes. {} message(s) deleted.", self.deleted_messages),
                _("Clear cancelled. {} message(s) deleted.", self.deleted_messages),
            )
            await self.inter.edit_original_response(
                **response_constructor(ResponseType.warning, text_response[view.pressed]),
                view=None,
            )
        else:
            await self.inter.edit_original_response(
                **response_constructor(ResponseType.success, _("{} message(s) deleted.", self.deleted_messages)),
                view=None,
            )

    async def periodic_display_update(self):
        while True:
            await asyncio.sleep(3)
            await self.inter.edit_original_response(**self.working_display())

    async def _clear(
        self,
    ) -> None:
        iterator: AsyncGenerator[discord.Message, None] = self.filtered_history()

        async def _single_delete_strategy(messages: list[discord.Message]) -> None:
            """Delete message older than 14 days. Delete them one by one."""
            for m in messages:
                await asyncio.sleep(2)
                await m.delete()
                self._deleted_messages.append(m)

        async def _bulk_delete_strategy(messages: list[discord.Message]) -> None:
            await self.channel.delete_messages(messages)  # long process for some reason
            self._deleted_messages.extend(messages)

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

                if strategy is self.channel.delete_messages:
                    self._deleted_messages.extend(to_delete)

    async def filtered_history(self) -> AsyncGenerator[discord.Message, None]:
        limit = self.deletion_goal if not any(self.filters) else None

        async for msg in self.channel.history(limit=limit):
            # if not all the filters tests are compliant, continue
            if not await async_all(await filter.test(msg) for filter in self.filters):
                self.analyzed_messages += 1
                continue

            if self.deletion_planned + 1 > self.deletion_goal:
                break
            self.deletion_planned += 1
            self.analyzed_messages += 1

            yield msg


class CancelClearView(Menu):
    def __init__(self, bot: MyBot, user_id: int):
        super().__init__(bot, timeout=3 * 60)
        self.pressed: bool = False
        self.user_id: int = user_id

    async def build(self):
        self.cancel.label = _("Cancel")
        return self

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        await interaction.response.defer()
        return interaction.user.id == self.user_id

    @ui.button(style=discord.ButtonStyle.red)
    async def cancel(self, inter: discord.Interaction, button: ui.Button[Self]):
        del inter, button  # unused
        self.pressed = True
        self.stop()


async def setup(bot: MyBot):
    await bot.add_cog(Clear(bot))
