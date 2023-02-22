# TODO : allow editing of poll
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Self

import discord
from discord import app_commands, ui
from discord.app_commands import locale_str as __
from sqlalchemy.orm import selectinload

from core import SpecialCog, db
from core.i18n import _

from .display import PollDisplay
from .edit import EditPoll
from .vote_menus import PollPublicMenu

if TYPE_CHECKING:
    from discord import Interaction

    from mybot import MyBot


logger = logging.getLogger(__name__)


class PollCog(SpecialCog["MyBot"]):
    def __init__(self, bot: MyBot):
        super().__init__(bot)

        self.bot.tree.add_command(app_commands.ContextMenu(name=__("Edit poll"), callback=self.edit_poll))

    async def cog_load(self) -> None:
        self.bot.add_view(PollPublicMenu(self.bot))

    @app_commands.command(
        name=__("poll"),
        description=__("Do a poll."),
        extras={"soon": True},
    )
    @app_commands.choices(
        poll_type=[
            app_commands.Choice(name=__("custom choices"), value=db.PollType.CHOICE.value),
            app_commands.Choice(name=__("yes or no"), value=db.PollType.BOOLEAN.value),
            app_commands.Choice(name=__("opinion"), value=db.PollType.OPINION.value),
            app_commands.Choice(name=__("text"), value=db.PollType.ENTRY.value),
        ]
    )
    async def poll(self, inter: Interaction, poll_type: app_commands.Choice[int]) -> None:
        poll = db.Poll(
            channel_id=inter.channel_id,
            guild_id=inter.guild_id,
            author_id=inter.user.id,
            type=db.PollType(poll_type.value),
            creation_date=inter.created_at,
            max_answers=1,
            users_can_change_answer=True,
            closed=False,
            public_results=True,
        )
        if poll_type.value == db.PollType.CHOICE.value:
            await inter.response.send_modal(ChoicesPollModal(self.bot, poll))
        else:
            await inter.response.send_message("Other poll types are not implemented yet.")
            # await inter.response.send_modal(PollModal(self.bot, poll))

    # This is a context command.
    async def edit_poll(self, inter: Interaction, message: discord.Message) -> None:
        async with self.bot.async_session() as session:
            result = await session.execute(
                db.select(db.Poll).where(db.Poll.message_id == message.id).options(selectinload(db.Poll.choices))
            )
            poll = result.scalar_one_or_none()

        if not poll:
            return await inter.response.send_message(_("This message is not a poll."), ephemeral=True)
        if poll.author_id != inter.user.id:
            return await inter.response.send_message(_("You can't edit this poll."), ephemeral=True)
        await inter.response.send_message(
            **(await PollDisplay(poll, self.bot).build()), view=EditPoll(self.bot, poll, message), ephemeral=True
        )


class PollModal(ui.Modal):
    def __init__(self, bot: MyBot, poll: db.Poll):
        super().__init__(title=_("Create a new poll"), timeout=None)

        self.bot = bot
        self.poll = poll

        self.question = ui.TextInput[PollModal](
            label=_("Poll question"), placeholder=_("Do you agree this bot is awesome?"), max_length=256
        )
        self.add_item(self.question)
        self.description = ui.TextInput[PollModal](
            label=_("Poll description"),
            placeholder=_("Tell more about your poll here."),
            required=False,
            max_length=2000,
        )
        self.add_item(self.description)

    async def on_submit(self, inter: discord.Interaction):
        self.poll.title = self.question.value
        self.poll.description = self.description.value
        await inter.response.send_message(
            **(await PollDisplay(self.poll, self.bot).build()),
            view=EditPoll(self.bot, self.poll, inter.message),
            ephemeral=True,
        )


class ChoicesPollModal(PollModal):
    def __init__(self, bot: MyBot, poll: db.Poll):
        super().__init__(bot, poll)

        self.choice1 = ui.TextInput[Self](
            label=_("Choice 1"),
            placeholder=_("Yes, totally!"),
            max_length=512,
        )
        self.choice2 = ui.TextInput[Self](
            label=_("Choice 2"),
            placeholder=_("Absolutely!"),
            max_length=512,
        )

        self.add_item(self.choice1)
        self.add_item(self.choice2)

    async def on_submit(self, inter: discord.Interaction):
        self.poll.title = self.question.value
        self.poll.choices.append(db.PollChoice(poll_id=self.poll.id, label=self.choice1.value))
        self.poll.choices.append(db.PollChoice(poll_id=self.poll.id, label=self.choice2.value))

        await inter.response.send_message(
            **(await PollDisplay(self.poll, self.bot).build()),
            view=EditPoll(self.bot, self.poll, inter.message),
            ephemeral=True,
        )


async def setup(bot: MyBot):
    await bot.add_cog(PollCog(bot))
