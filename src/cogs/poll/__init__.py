# IDEA add rank polls (with average note etc...)

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Self, cast

import discord
from discord import app_commands, ui
from discord.app_commands import locale_str as __
from sqlalchemy.orm import selectinload

from core import SpecialGroupCog, db
from core.checkers import app_command_bot_required_permissions
from core.i18n import _

from .display import PollDisplay
from .edit import EditPoll
from .vote_menus import PollPublicMenu

if TYPE_CHECKING:
    from discord import Interaction

    from mybot import MyBot


logger = logging.getLogger(__name__)


@app_commands.default_permissions(administrator=True)
@app_commands.guild_only()
class PollCog(SpecialGroupCog["MyBot"], group_name=__("poll"), group_description=__("Create a new poll")):
    def __init__(self, bot: MyBot):
        super().__init__(bot)

        self.bot.tree.add_command(
            app_commands.ContextMenu(
                name=__("Edit poll"),
                callback=self.edit_poll,
                extras={"description": _("Use this to edit a poll even after creation.", _locale=None)},
            )
        )

        self.current_votes: dict[int, dict[int, tuple[Interaction, ui.View]]] = {}  # poll_id: {user_id: interaction}

    async def cog_load(self) -> None:
        self.bot.add_view(PollPublicMenu(self))

    async def callback(self, inter: Interaction, poll_type: db.PollType) -> None:
        channel_id = cast(int, inter.channel_id)  # not usable in private messages
        guild_id = cast(int, inter.guild_id)  # not usable in private messages

        poll = db.Poll(
            channel_id=channel_id,
            guild_id=guild_id,
            author_id=inter.user.id,
            type=db.PollType(poll_type.value),
            creation_date=inter.created_at,
        )

        poll_menu_from_type = {
            db.PollType.CHOICE: ChoicesPollModal,
            db.PollType.BOOLEAN: PollModal,
            db.PollType.OPINION: PollModal,
            db.PollType.ENTRY: PollModal,
        }

        poll_menu = poll_menu_from_type[db.PollType(poll_type.value)](self, poll)
        await inter.response.send_modal(poll_menu)

    @app_command_bot_required_permissions(send_messages=True, embed_links=True, external_emojis=True)
    @app_commands.command(
        name=__("custom_choice"),
        description=__("A poll with customizable options."),
        extras={"beta": True},
    )
    async def custom_choice(self, inter: Interaction) -> None:
        await self.callback(inter, db.PollType.CHOICE)

    @app_command_bot_required_permissions(send_messages=True, embed_links=True, external_emojis=True)
    @app_commands.command(
        name=__("yesno"),
        description=__('A simple poll with "Yes" and "No" as options.'),
        extras={"beta": True},
    )
    async def boolean(self, inter: Interaction) -> None:
        await self.callback(inter, db.PollType.BOOLEAN)

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
            **(await PollDisplay.build(poll, self.bot)),
            view=await EditPoll(self, poll, message).build(),
            ephemeral=True,
        )


class PollModal(ui.Modal):
    def __init__(self, cog: PollCog, poll: db.Poll):
        super().__init__(title=_("Create a new poll"), timeout=None)

        self.cog = cog
        self.bot = cog.bot
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
            style=discord.TextStyle.long,
        )
        self.add_item(self.description)

    async def on_submit(self, inter: discord.Interaction):
        self.poll.title = self.question.value
        self.poll.description = self.description.value
        await inter.response.send_message(
            **(await PollDisplay.build(self.poll, self.bot)),
            view=await EditPoll(self.cog, self.poll, inter.message).build(),
            ephemeral=True,
        )


class ChoicesPollModal(PollModal):
    def __init__(self, cog: PollCog, poll: db.Poll):
        super().__init__(cog, poll)

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
        self.poll.description = self.description.value
        self.poll.choices.append(db.PollChoice(poll_id=self.poll.id, label=self.choice1.value))
        self.poll.choices.append(db.PollChoice(poll_id=self.poll.id, label=self.choice2.value))

        await inter.response.send_message(
            **(await PollDisplay.build(self.poll, self.bot)),
            view=await EditPoll(self.cog, self.poll, inter.message).build(),
            ephemeral=True,
        )


async def setup(bot: MyBot):
    await bot.add_cog(PollCog(bot))
