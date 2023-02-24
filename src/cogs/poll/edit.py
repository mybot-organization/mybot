from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Self, cast

import discord
from discord import ui

from cogs.poll.vote_menus import PollPublicMenu
from core import ResponseType, db, response_constructor
from core.i18n import _

from .constants import TOGGLE_EMOTES
from .display import PollDisplay

if TYPE_CHECKING:
    from . import PollCog


class EditPoll(ui.View):
    def __init__(self, cog: PollCog, poll: db.Poll, poll_message: discord.Message | None = None):
        super().__init__(timeout=600)

        self.poll = poll
        self.bot = cog.bot
        self.cog = cog
        self.poll_message = poll_message  # poll_message is None if the poll is new

        self.build_view()

    def disable_view(self):
        for item in self.children:
            if isinstance(item, (ui.Button, ui.Select)):
                item.disabled = True

    def build_view(self):
        self.edit_title_and_description.label = _("Edit title & description")
        self.set_ending_time.label = _("Set ending time")
        self.edit_choices.label = _("Edit choices")

        if self.poll.type == db.PollType.CHOICE:
            self.edit_choices.disabled = False
        else:
            self.edit_choices.disabled = True

        self.public_results.label = _("The results are {}.", _("public") if self.poll.public_results else _("private"))
        self.public_results.emoji = TOGGLE_EMOTES[self.poll.public_results]
        self.users_can_change_answer.label = _(
            "Users {} change their answer once voted.", _("can") if self.poll.users_can_change_answer else _("can't")
        )
        self.users_can_change_answer.emoji = TOGGLE_EMOTES[self.poll.users_can_change_answer]

        self.toggle_poll.disabled = self.poll_message is None

        if self.poll.closed:
            self.toggle_poll.label = _("Reopen poll")
            self.toggle_poll.style = discord.ButtonStyle.green
        else:
            self.toggle_poll.label = _("Close poll")
            self.toggle_poll.style = discord.ButtonStyle.red

        self.save.label = _("Save")

    @ui.button(row=0, style=discord.ButtonStyle.blurple)
    async def edit_title_and_description(self, inter: discord.Interaction, button: ui.Button[Self]):
        await inter.response.send_modal(EditPollTitleAndDescription(self))

    @ui.button(row=0, style=discord.ButtonStyle.blurple)
    async def set_ending_time(self, inter: discord.Interaction, button: ui.Button[Self]):
        # EditPollEndingTime can edit the poll itself at definition, and the display will be updated
        view = EditPollEndingTime(self)
        await inter.response.edit_message(**(await PollDisplay.build(self.poll, self.bot)), view=view)

    @ui.button(row=0, style=discord.ButtonStyle.blurple)
    async def edit_choices(self, inter: discord.Interaction, button: ui.Button[Self]):
        pass  # TODO implement edit choices

    @ui.button(row=1, style=discord.ButtonStyle.gray)
    async def public_results(self, inter: discord.Interaction, button: ui.Button[Self]):
        self.poll.public_results = not self.poll.public_results
        self.build_view()
        await inter.response.edit_message(**(await PollDisplay.build(self.poll, self.bot)), view=self)

    @ui.button(row=2, style=discord.ButtonStyle.gray)
    async def users_can_change_answer(self, inter: discord.Interaction, button: ui.Button[Self]):
        self.poll.users_can_change_answer = not self.poll.users_can_change_answer
        self.build_view()
        await inter.response.edit_message(**(await PollDisplay.build(self.poll, self.bot)), view=self)

    @ui.button(row=4, style=discord.ButtonStyle.red)
    async def toggle_poll(self, inter: discord.Interaction, button: ui.Button[Self]):
        self.poll.closed = not self.poll.closed
        self.build_view()
        await inter.response.edit_message(**(await PollDisplay.build(self.poll, self.bot)), view=self)

    @ui.button(row=4, style=discord.ButtonStyle.green)
    async def save(self, inter: discord.Interaction, button: ui.Button[Self]):
        if self.poll_message is None:
            await inter.response.defer()
            await inter.delete_original_response()
            # channel can be other type of channels like voice, but it's ok.
            channel = cast(discord.TextChannel, inter.channel)
            message = await channel.send(
                **(await PollDisplay.build(self.poll, self.bot)), view=PollPublicMenu.build(self.cog, self.poll)
            )
            self.poll.message_id = message.id

            async with self.bot.async_session.begin() as session:
                guild_id: int = inter.guild_id  # type: ignore (poll is only usable in guild)
                await self.bot.get_guild_db(
                    guild_id, session=session
                )  # to be sure the guild is present in the database
                session.add(self.poll)
        else:
            async with self.bot.async_session.begin() as session:
                session.add(self.poll)
            await inter.response.defer()
            await inter.delete_original_response()

            await self.poll_message.edit(
                **(await PollDisplay.build(self.poll, self.bot)), view=PollPublicMenu.build(self.cog, self.poll)
            )

            currents = self.cog.current_votes.pop(self.poll.id, None)
            # stop view is not almost instant, so there is no risk of duplicate votes.
            if currents is not None:
                for __, vote_view in currents.values():
                    vote_view.stop()

                for vote_inter, __ in currents.values():
                    await vote_inter.edit_original_response(
                        **response_constructor(
                            ResponseType.error, _("The poll has been updated while you were voting.")
                        ),
                        view=None,
                    )


class EditSubmenu(ui.View):
    def __init__(self, parent: EditPoll):
        super().__init__(timeout=600)
        self.parent = parent
        self.bot = parent.bot
        self.poll = parent.poll

        self.localize_view()
        self.set_select_options()

    def localize_view(self) -> None:
        pass

    def set_select_options(self) -> None:
        pass

    def build_view(self) -> None:
        raise NotImplementedError()

    async def set_parent_view(self, inter: discord.Interaction):
        self.parent.build_view()
        await inter.response.edit_message(**(await PollDisplay.build(self.poll, self.bot)), view=self.parent)

    async def update_overview(self, inter: discord.Interaction):
        try:
            self.build_view()
        except NotImplementedError:
            for item in self.children:
                if isinstance(item, ui.Select):
                    for option in item.options:
                        option.default = option.value in item.values
        await inter.response.edit_message(**(await PollDisplay.build(self.poll, self.bot)), view=self)


class EditPollTitleAndDescription(EditSubmenu, ui.Modal):
    def __init__(self, parent: EditPoll):
        ui.Modal.__init__(self, title=_("Create a new poll"))
        EditSubmenu.__init__(self, parent)

        self.question = ui.TextInput[Self](
            label=_("Poll question"),
            placeholder=_("Do you agree this bot is awesome?"),
            max_length=256,
            default=self.poll.title,
        )
        self.add_item(self.question)

        self.description = ui.TextInput[Self](
            label=_("Poll description"),
            style=discord.TextStyle.paragraph,
            placeholder=_("Tell more about your poll here."),
            required=False,
            max_length=2000,
            default=self.poll.description,
        )
        self.add_item(self.description)

    async def on_submit(self, inter: discord.Interaction) -> None:
        self.poll.title = self.question.value
        self.poll.description = self.description.value
        await self.set_parent_view(inter)


class EditPollEndingTime(EditSubmenu):
    def __init__(self, parent: EditPoll):
        super().__init__(parent)
        self.old_value = self.poll.end_date

        if self.poll.end_date is not None:
            delta = self.poll.end_date - datetime.now(timezone.utc)

            if delta < timedelta():
                self.poll.end_date = None
            else:
                if delta.days > 0:
                    default_days = str(delta.days)
                    self.select_days._values = [default_days]  # pyright: ignore [reportPrivateUsage]

                    option = next(opt for opt in self.select_days.options if opt.value == default_days)
                    option.default = True

                if delta.seconds // 3600 > 0:
                    default_hours = str(delta.seconds // 3600)
                    self.select_hours._values = [default_hours]  # pyright: ignore [reportPrivateUsage]

                    option = next(opt for opt in self.select_hours.options if opt.value == default_hours)
                    option.default = True

                minutes = delta.seconds % 3600 // 60
                if minutes > 0:
                    tmp = minutes - 1
                    default_minutes = str(tmp - tmp % 3 + 1)
                    self.select_minutes._values = [default_minutes]  # pyright: ignore [reportPrivateUsage]

                    option = next(opt for opt in self.select_minutes.options if opt.value == default_minutes)
                    option.default = True

    def localize_view(self):
        self.select_days.placeholder = _("Select the number of days.")
        self.select_hours.placeholder = _("Select the number of hours.")
        self.select_minutes.placeholder = _("Select the number of minutes.")
        self.cancel.label = _("Cancel")
        self.back.label = _("Back")

    def set_time(self):
        ending_time = timedelta()

        if self.select_days.values:
            ending_time += timedelta(days=int(self.select_days.values[0]))
        if self.select_hours.values:
            ending_time += timedelta(hours=int(self.select_hours.values[0]))
        if self.select_minutes.values:
            ending_time += timedelta(minutes=int(self.select_minutes.values[0]))

        if ending_time == timedelta():
            self.poll.end_date = None
        else:
            self.poll.end_date = datetime.now(timezone.utc) + ending_time

    def set_select_options(self):
        self.select_days.options = [discord.SelectOption(label=_("{} day(s)", i), value=str(i)) for i in range(1, 26)]
        self.select_hours.options = [discord.SelectOption(label=_("{} hour(s)", i), value=str(i)) for i in range(1, 24)]
        self.select_minutes.options = [
            discord.SelectOption(label=_("{} minute(s)", i), value=str(i)) for i in range(1, 61, 3)
        ]

    @ui.select(min_values=0, max_values=1)  # pyright: ignore reportUnknownMemberType
    async def select_days(self, inter: discord.Interaction, select: ui.Select[Self]):
        self.set_time()
        await self.update_overview(inter)

    @ui.select(min_values=0, max_values=1)  # pyright: ignore reportUnknownMemberType
    async def select_hours(self, inter: discord.Interaction, select: ui.Select[Self]):
        self.set_time()
        await self.update_overview(inter)

    @ui.select(min_values=0, max_values=1)  # pyright: ignore reportUnknownMemberType
    async def select_minutes(self, inter: discord.Interaction, select: ui.Select[Self]):
        self.set_time()
        await self.update_overview(inter)

    @ui.button(style=discord.ButtonStyle.red)
    async def cancel(self, inter: discord.Interaction, button: ui.Button[Self]):
        self.poll.end_date = self.old_value
        await self.set_parent_view(inter)

    @ui.button(style=discord.ButtonStyle.green)
    async def back(self, inter: discord.Interaction, button: ui.Button[Self]):
        await self.set_parent_view(inter)


class EditPollChoices(EditSubmenu):
    def localize_view(self):
        self.add_choice.label = _("Add a choice")
        self.remove_choice.label = _("Remove a choice")
        self.back.label = _("Back")

    @ui.button(row=0, style=discord.ButtonStyle.blurple)
    async def add_choice(self, inter: discord.Interaction, button: ui.Button[Self]):
        pass  # TODO implement add choice

    @ui.button(row=0, style=discord.ButtonStyle.blurple)
    async def remove_choice(self, inter: discord.Interaction, button: ui.Button[Self]):
        pass  # TODO implement remove choice

    @ui.button(row=1, style=discord.ButtonStyle.green)
    async def back(self, inter: discord.Interaction, button: ui.Button[Self]):
        await self.set_parent_view(inter)
