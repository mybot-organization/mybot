from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Self, Type, cast

import discord
from discord import Interaction, ui
from sqlalchemy import delete

from cogs.poll.vote_menus import PollPublicMenu
from core import Menu, MessageDisplay, ResponseType, db, response_constructor
from core.i18n import _
from core.response import ResponseType

from .constants import LEGEND_EMOJIS, TOGGLE_EMOTES
from .display import PollDisplay

if TYPE_CHECKING:
    from mybot import MyBot

    from . import PollCog


class EditPollMenus(ui.Select["EditPoll"]):
    def __init__(self, poll: db.Poll):
        super().__init__(placeholder=_("Select what you want to edit."))
        self.menus: list[Type[EditSubmenu]] = [
            EditTitleAndDescription,
            EditEndingTime,
            EditAllowedRoles,
        ]
        if poll.type == db.PollType.CHOICE:
            self.menus.append(EditChoices)
        if poll.type in (db.PollType.CHOICE, db.PollType.OPINION):
            self.menus.append(EditMaxChoices)

        for i, menu in enumerate(self.menus):
            self.add_option(
                label=_(menu.select_name),
                value=str(i),
                description=_(menu.select_description),
            )

    # TODO : inspect the type issue present here.
    async def callback(self, inter: Interaction[MyBot]) -> None:  # pyright: ignore [reportIncompatibleMethodOverride]
        view = cast(EditPoll, self.view)
        await view.set_menu(inter, await self.menus[int(self.values[0])](view).build())


class EditPoll(Menu["MyBot"]):
    def __init__(self, cog: PollCog, poll: db.Poll, poll_message: discord.Message | None = None):
        super().__init__(bot=cog.bot, timeout=600)

        self.poll = poll
        self.cog = cog
        self.poll_message = poll_message  # poll_message is None if the poll is new

    async def build(self) -> Self:
        self.add_item(EditPollMenus(self.poll))
        self.reset_votes.label = _("Reset")
        self.save.label = _("Save")

        # if self.poll.type == db.PollType.CHOICE:
        #     self.edit_choices.disabled = False
        #     self.set_max_choices.disabled = False
        # else:
        #     self.edit_choices.disabled = True
        #     self.set_max_choices.disabled = True

        await self.update()

        return self

    async def update(self) -> None:
        self.public_results.label = _("The results are {}.", _("public") if self.poll.public_results else _("private"))
        self.public_results.emoji = TOGGLE_EMOTES[self.poll.public_results]

        self.users_can_change_answer.label = _(
            "Users {} change their answer once voted.", _("can") if self.poll.users_can_change_answer else _("can't")
        )
        self.users_can_change_answer.emoji = TOGGLE_EMOTES[self.poll.users_can_change_answer]

        # self.users_can_be_anonymous.label = _(
        #     "Users {} vote anonymously.", _("can") if self.poll.anonymous_allowed else _("can't")
        # )
        # self.users_can_be_anonymous.emoji = TOGGLE_EMOTES[self.poll.anonymous_allowed]

        self.toggle_poll.disabled = self.poll_message is None
        self.reset_votes.disabled = self.poll_message is None

        if self.poll.closed:
            self.toggle_poll.label = _("Reopen poll")
            self.toggle_poll.style = discord.ButtonStyle.green
        else:
            self.toggle_poll.label = _("Close poll")
            self.toggle_poll.style = discord.ButtonStyle.red

    async def message_display(self) -> MessageDisplay:
        return await PollDisplay.build(self.poll, self.bot)

    @ui.button(row=1, style=discord.ButtonStyle.gray)
    async def public_results(self, inter: discord.Interaction, button: ui.Button[Self]):
        self.poll.public_results = not self.poll.public_results
        await self.message_refresh(inter)

    @ui.button(row=2, style=discord.ButtonStyle.gray)
    async def users_can_change_answer(self, inter: discord.Interaction, button: ui.Button[Self]):
        self.poll.users_can_change_answer = not self.poll.users_can_change_answer
        await self.message_refresh(inter, False)

    # @ui.button(row=3, style=discord.ButtonStyle.gray)
    # async def users_can_be_anonymous(self, inter: discord.Interaction, button: ui.Button[Self]):
    #     self.poll.anonymous_allowed = not self.poll.anonymous_allowed
    #     await self.message_refresh(inter, False)

    @ui.button(row=4, style=discord.ButtonStyle.red)
    async def reset_votes(self, inter: discord.Interaction, button: ui.Button[Self]):
        await self.set_menu(inter, await Reset(parent=self).build())

    @ui.button(row=4, style=discord.ButtonStyle.red)
    async def toggle_poll(self, inter: discord.Interaction, button: ui.Button[Self]):
        self.poll.closed = not self.poll.closed
        await self.message_refresh(inter)

    @ui.button(row=4, style=discord.ButtonStyle.green)
    async def save(self, inter: discord.Interaction, button: ui.Button[Self]):
        if self.poll_message is None:
            await inter.response.defer()
            await inter.delete_original_response()
            # channel can be other type of channels like voice, but it's ok.
            channel = cast(discord.TextChannel, inter.channel)
            message = await channel.send(
                **(await PollDisplay.build(self.poll, self.bot)), view=await PollPublicMenu(self.cog, self.poll).build()
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
                **(await PollDisplay.build(self.poll, self.bot)), view=await PollPublicMenu(self.cog, self.poll).build()
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


class EditSubmenu(Menu["MyBot"]):
    parent: EditPoll
    select_name: str
    select_description: str

    def __init__(self, parent: EditPoll):
        super().__init__(parent.bot, parent)
        self.poll = parent.poll

    async def set_back(self, inter: discord.Interaction):
        await self.parent.update()
        await super().set_back(inter)

    async def update_poll_display(self, inter: discord.Interaction, view: ui.View | None = None):
        await inter.response.edit_message(**(await PollDisplay.build(self.poll, self.bot)), view=view or self)


class EditTitleAndDescription(EditSubmenu, ui.Modal):
    select_name = _("Edit title and description", _locale=None)
    select_description = ""

    def __init__(self, parent: EditPoll):
        self.title = _("Create a new poll")
        self.custom_id = self.generate_custom_id()
        EditSubmenu.__init__(self, parent)

    async def build(self) -> Self:
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

        return self

    async def on_submit(self, inter: discord.Interaction) -> None:
        self.poll.title = self.question.value
        self.poll.description = self.description.value
        await self.set_back(inter)


class EditEndingTime(EditSubmenu):
    select_name = _("Edit ending time", _locale=None)
    select_description = _("Set a poll duration, it will be closed automatically.", _locale=None)

    def __init__(self, parent: EditPoll):
        super().__init__(parent)
        self.old_value = self.poll.end_date

    async def build(self) -> Self:
        self.select_days.placeholder = _("Select the number of days.")
        self.select_hours.placeholder = _("Select the number of hours.")
        self.select_minutes.placeholder = _("Select the number of minutes.")
        self.cancel.label = _("Cancel")
        self.back.label = _("Back")

        self.select_days.options = [discord.SelectOption(label=_("{} day(s)", i), value=str(i)) for i in range(1, 26)]
        self.select_hours.options = [discord.SelectOption(label=_("{} hour(s)", i), value=str(i)) for i in range(1, 24)]
        self.select_minutes.options = [
            discord.SelectOption(label=_("{} minute(s)", i), value=str(i)) for i in range(1, 61, 3)
        ]

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
        return self

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

    async def callback(self, inter: Interaction):
        self.set_time()
        await self.update()
        await self.update_poll_display(inter)

    @ui.select(min_values=0, max_values=1)
    async def select_days(self, inter: discord.Interaction, select: ui.Select[Self]):
        await self.callback(inter)

    @ui.select(min_values=0, max_values=1)
    async def select_hours(self, inter: discord.Interaction, select: ui.Select[Self]):
        await self.callback(inter)

    @ui.select(min_values=0, max_values=1)
    async def select_minutes(self, inter: discord.Interaction, select: ui.Select[Self]):
        await self.callback(inter)

    @ui.button(style=discord.ButtonStyle.red)
    async def cancel(self, inter: discord.Interaction, button: ui.Button[Self]):
        self.poll.end_date = self.old_value
        await self.set_back(inter)

    @ui.button(style=discord.ButtonStyle.green)
    async def back(self, inter: discord.Interaction, button: ui.Button[Self]):
        await self.set_back(inter)


class EditChoices(EditSubmenu):
    select_name = _("Edit choices", _locale=None)
    select_description = _("Add and removes choices for multiple choices polls.", _locale=None)

    def __init__(self, parent: EditPoll):
        super().__init__(parent)
        self.old_value = self.poll.choices.copy()

    async def build(self) -> Self:
        self.add_choice.label = _("Add a choice")
        self.remove_choice.label = _("Remove a choice")
        self.back.label = _("Back")
        self.cancel.label = _("Cancel")

        return await super().build()

    async def update(self):
        self.remove_choice.disabled = len(self.poll.choices) <= 2

    @ui.button(row=0, style=discord.ButtonStyle.blurple)
    async def add_choice(self, inter: discord.Interaction, button: ui.Button[Self]):
        await inter.response.send_modal(await AddChoice(self).build())

    @ui.button(row=0, style=discord.ButtonStyle.blurple)
    async def remove_choice(self, inter: discord.Interaction, button: ui.Button[Self]):
        await inter.response.edit_message(view=await RemoveChoices(self).build())

    @ui.button(row=1, style=discord.ButtonStyle.red)
    async def cancel(self, inter: discord.Interaction, button: ui.Button[Self]):
        self.poll.choices = self.old_value
        await self.set_back(inter)

    @ui.button(row=1, style=discord.ButtonStyle.green)
    async def back(self, inter: discord.Interaction, button: ui.Button[Self]):
        await self.set_back(inter)


class AddChoice(Menu["MyBot"], ui.Modal):
    parent: EditChoices

    def __init__(self, parent: EditChoices) -> None:
        ui.Modal.__init__(self, title=_("Add a new choice"))
        Menu.__init__(self, parent=parent)  # pyright: ignore [reportUnknownMemberType]

    async def build(self) -> Self:
        self.choice = ui.TextInput[Self](
            label=_("Choice"),
            placeholder=_("Enter a new choice here."),
            required=True,
            max_length=512,
        )
        self.add_item(self.choice)
        return self

    async def on_submit(self, inter: discord.Interaction) -> None:
        self.parent.poll.choices.append(db.PollChoice(label=self.choice.value))
        await self.parent.update()
        await self.parent.update_poll_display(inter)


class RemoveChoices(Menu["MyBot"]):
    parent: EditChoices

    def __init__(self, parent: EditChoices) -> None:
        super().__init__(bot=parent.bot, parent=parent)
        self.old_value = self.parent.poll.choices.copy()
        self.linked_choice = {choice: i for i, choice in enumerate(self.old_value)}

    async def build(self) -> Self:
        self.back.label = _("Back")
        self.cancel.label = _("Cancel")
        self.choices_to_remove.placeholder = _("Select the choices you want to remove.")
        for choice, i in self.linked_choice.items():
            self.choices_to_remove.add_option(label=choice.label[:99] + "…", value=str(i), emoji=LEGEND_EMOJIS[i])
        self.choices_to_remove.max_values = len(self.old_value) - 2
        self.choices_to_remove.min_values = 0
        return self

    async def update(self):
        for option in self.choices_to_remove.options:
            option.default = option.value in self.choices_to_remove.values

    @ui.select()
    async def choices_to_remove(self, inter: Interaction, select: ui.Select[Self]):
        self.parent.poll.choices = [
            choice for choice in self.old_value if str(self.linked_choice[choice]) not in select.values
        ]
        await self.update()
        await self.parent.update_poll_display(inter, view=self)

    @ui.button(style=discord.ButtonStyle.red)
    async def cancel(self, inter: discord.Interaction, button: ui.Button[Self]):
        self.parent.poll.choices = self.old_value
        await self.parent.set_back(inter)

    @ui.button(style=discord.ButtonStyle.green)
    async def back(self, inter: discord.Interaction, button: ui.Button[Self]):
        await self.parent.set_back(inter)


class EditMaxChoices(EditSubmenu):
    select_name = _("Edit max choices", _locale=None)
    select_description = _("Set the maximum of simultaneous values users can choose.", _locale=None)

    def __init__(self, parent: EditPoll) -> None:
        super().__init__(parent=parent)
        self.old_value = self.parent.poll.max_answers

    async def build(self) -> Self:
        self.cancel.label = _("Cancel")
        self.back.label = _("Back")

        self.max_choices.placeholder = _("Select the maximum number of choices.")
        self.max_choices.min_values = 1
        self.max_choices.max_values = 1

        self.max_choices._values = [str(self.parent.poll.max_answers)]  # pyright: ignore [reportPrivateUsage]
        for i in range(1, len(self.parent.poll.choices) + 1):
            self.max_choices.add_option(label=str(i), value=str(i), default=i == self.parent.poll.max_answers)

        return self

    @ui.select()
    async def max_choices(self, inter: Interaction, select: ui.Select[Self]):
        self.parent.poll.max_answers = int(select.values[0])
        await self.message_refresh(inter)

    @ui.button(style=discord.ButtonStyle.red)
    async def cancel(self, inter: discord.Interaction, button: ui.Button[Self]):
        self.parent.poll.max_answers = self.old_value
        await self.set_back(inter)

    @ui.button(style=discord.ButtonStyle.green)
    async def back(self, inter: discord.Interaction, button: ui.Button[Self]):
        await self.set_back(inter)


class EditAllowedRoles(EditSubmenu):
    select_name = _("Edit allowed roles", _locale=None)
    select_description = _("Only users with one of these role can vote.", _locale=None)

    def __init__(self, parent: EditPoll) -> None:
        super().__init__(parent=parent)
        self.old_value = self.parent.poll.allowed_roles.copy()

    async def build(self) -> Self:
        self.cancel.label = _("Cancel")
        self.back.label = _("Back")
        self.allowed_roles.placeholder = _("Select the roles that can vote.")

        # discord limitation ?
        # def get_role(role_id: int) -> discord.Role | None:
        #     guild: discord.Guild = cast(discord.Guild, self.bot.get_guild(self.parent.poll.guild_id))
        #     return guild.get_role(role_id)

        # self.allowed_roles._values = [  # pyright: ignore [reportPrivateUsage]
        #     role for role_id in self.parent.poll.allowed_roles if (role := get_role(role_id))
        # ]

        await self.update()

        return self

    @ui.select(cls=ui.RoleSelect[Self], max_values=25)
    async def allowed_roles(self, inter: Interaction, select: ui.RoleSelect[Self]):
        self.parent.poll.allowed_roles = [role.id for role in select.values]
        await self.message_refresh(inter)

    @ui.button(style=discord.ButtonStyle.red)
    async def cancel(self, inter: discord.Interaction, button: ui.Button[Self]):
        self.parent.poll.allowed_roles = self.old_value
        await self.set_back(inter)

    @ui.button(style=discord.ButtonStyle.green)
    async def back(self, inter: discord.Interaction, button: ui.Button[Self]):
        await self.set_back(inter)


class Reset(EditSubmenu):
    parent: EditPoll

    async def build(self) -> Self:
        self.reset.label = _("Reset")
        self.cancel.label = _("Cancel")
        return self

    async def message_display(self) -> MessageDisplay:
        return response_constructor(
            ResponseType.warning,
            _('This operation cannot be undone. By clicking on the "RESET" button, all the votes will be deleted.'),
        )

    @ui.button(style=discord.ButtonStyle.red)
    async def cancel(self, inter: discord.Interaction, button: ui.Button[Self]):
        await self.set_back(inter)

    @ui.button(style=discord.ButtonStyle.green)
    async def reset(self, inter: discord.Interaction, button: ui.Button[Self]):
        async with self.bot.async_session.begin() as session:
            await session.execute(delete(db.PollAnswer).where(db.PollAnswer.poll_id == self.parent.poll.id))
        await self.set_back(inter)
