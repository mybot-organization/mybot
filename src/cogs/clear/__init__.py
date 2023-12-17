from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime
from typing import TYPE_CHECKING, AsyncGenerator, Awaitable, Callable, Self, cast

import discord
from discord import app_commands, ui
from discord.app_commands import Range, Transform, locale_str as __

from core import ExtendedCog, Menu, MessageDisplay, ResponseType, checkers, response_constructor
from core.errors import BadArgument, MaxConcurrencyReached, NonSpecificError, UnexpectedError
from core.i18n import _
from core.transformers import DateTransformer
from core.utils import async_all

from .clear_transformers import (
    HasTransformer,
    LengthTransformer,
    PinnedTransformer,
    RegexTransformer,
    RoleTransformer,
    UserTransformer,
)
from .filters import Filter, HasFilter, LengthFilter, PinnedFilter, RegexFilter, RoleFilter, UserFilter

if TYPE_CHECKING:
    from discord import TextChannel, Thread, VoiceChannel

    from mybot import MyBot

    AllowPurgeChannel = TextChannel | VoiceChannel | Thread


logger = logging.getLogger(__name__)


def channel_bucket(inter: discord.Interaction):
    return inter.channel_id


class Clear(ExtendedCog):
    def __init__(self, bot: MyBot):
        super().__init__(bot)

        self.clear_max_concurrency = checkers.MaxConcurrency(1, key=channel_bucket, wait=False)

    @checkers.app.bot_required_permissions(
        manage_messages=True, read_message_history=True, read_messages=True, connect=True
    )
    @app_commands.command(
        description=__("Delete multiple messages with filters."),
    )
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.guild_only()
    @app_commands.describe(
        amount=__("{{}} messages (max 250)"),
        user=__("messages from the user {{}}"),
        role=__("messages whose user has the role {{}}"),
        pattern=__("messages that match {{}} (regex, multiline, case sensitive, not anchored)"),
        has=__("messages that has {{}}"),  # e.g. attachement:image will delete messages that has an image attached.
        max_length=__("messages longer or equal to {{}} (blank spaces included) (empty messages included)"),
        min_length=__("messages shorter or equal to {{}} (blank spaces included)"),
        before=__("messages sent before {{}} (yyyy-mm-dd or message ID)"),
        after=__("messages sent after {{}} (yyyy-mm-dd or message ID)"),
        pinned=__("only pinned message or exclude them from the deletion. (default to exclude)"),
    )
    @app_commands.rename(
        amount=__("amount"),
        user=__("user"),
        role=__("role"),
        pattern=__("search"),
        has=__("has"),
        max_length=__("max_length"),
        min_length=__("min_length"),
        before=__("before"),
        after=__("after"),
        pinned=__("pinned"),
    )
    async def clear(
        self,
        inter: discord.Interaction,
        amount: Range[int, 1, 250],
        user: Transform[UserFilter, UserTransformer] | None = None,
        role: Transform[RoleFilter, RoleTransformer] | None = None,
        pattern: Transform[RegexFilter, RegexTransformer] | None = None,
        has: Transform[HasFilter, HasTransformer] | None = None,
        max_length: Transform[LengthFilter, LengthTransformer("max")] | None = None,
        min_length: Transform[LengthFilter, LengthTransformer("min")] | None = None,
        before: Transform[datetime, DateTransformer] | None = None,
        after: Transform[datetime, DateTransformer] | None = None,
        pinned: Transform[PinnedFilter, PinnedTransformer] = PinnedFilter.default(),
    ):
        await self.clear_max_concurrency.acquire(inter)

        if inter.channel is None:
            raise UnexpectedError(f"{inter} had its channel set to None")

        if not 0 < amount < 251:
            raise BadArgument(_("You must supply a number between 1 and 250. (0 < {amount} < 251)", amount=amount))

        available_filters: list[Filter | None] = [
            pinned,
            user,
            role,
            pattern,
            has,
            max_length,
            min_length,
        ]
        active_filters: list[Filter] = [f for f in available_filters if f is not None]

        job = ClearWorker(self.bot, inter, amount, active_filters, before, after)
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
        before: datetime | None,
        after: datetime | None,
    ):
        self.deleted_messages: int = 0
        self.analyzed_messages: int = 0
        self.deletion_planned: int = 0
        self.deletion_goal: int = amount
        self.filters = filters
        self.before = before
        self.after = after
        self.inter = inter
        self.bot = bot
        self.channel = cast("AllowPurgeChannel", inter.channel)

    def working_display(self) -> MessageDisplay:
        display = response_constructor(
            ResponseType.info,
            _("Clearing {amount} message(s)...", amount=self.deletion_goal, _locale=self.inter.locale),
        )
        display.embed.description = _(
            "Analyzed: {analyzed}\nDeleted: {deleted}/{goal}\nPlanned for deletion: {planned}",
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
            e = task.exception()
            if e:
                raise e

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
                self.deleted_messages += 1

        async def _bulk_delete_strategy(messages: list[discord.Message]) -> None:
            await self.channel.delete_messages(messages)  # long process for some reason
            self.deleted_messages += len(messages)

        minimum_time: int = int((time.time() - 14 * 24 * 60 * 60) * 1000.0 - 1420070400000) << 22
        strategy: Callable[[list[discord.Message]], Awaitable[None]] = _bulk_delete_strategy

        to_delete: list[discord.Message] = []

        async for msg in iterator:
            if len(to_delete) == 100:
                await strategy(to_delete)
                to_delete = []

            # older than 14 days old
            if msg.id < minimum_time and strategy is not _single_delete_strategy:
                if len(to_delete) >= 1:  # if there are messages to delete, bulk delete them
                    await strategy(to_delete)
                    to_delete = []
                strategy = _single_delete_strategy  # set the new strategy

            to_delete.append(msg)

        if len(to_delete) >= 1:
            await strategy(to_delete)

    async def filtered_history(self) -> AsyncGenerator[discord.Message, None]:
        limit = self.deletion_goal if not any(self.filters) else None

        async for msg in self.channel.history(limit=limit, before=self.before, after=self.after):
            # if not all the filters tests are compliant, continue
            self.analyzed_messages += 1
            if not await async_all(await filter.test(msg) for filter in self.filters):
                continue

            self.deletion_planned += 1
            yield msg

            if self.deletion_planned >= self.deletion_goal:
                break


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
