# TODO : allow editing of poll

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Self

import discord
from discord import Embed, app_commands, ui
from discord.app_commands import locale_str as __
from sqlalchemy import func
from sqlalchemy.orm import selectinload

from core import Response, SpecialCog, db
from core.i18n import _

if TYPE_CHECKING:
    from discord import Interaction

    from mybot import MyBot


logger = logging.getLogger(__name__)


async def build_poll_visual(poll: db.Poll, bot: MyBot) -> Response:
    content = poll.description
    embed = Embed(title=poll.title)

    async with bot.async_session.begin() as session:
        stmt = (
            db.select(func.count())
            .select_from(db.PollAnswer)
            .where(db.PollAnswer.poll_id == poll.id)
            .group_by(db.PollAnswer.value)
        )
        votes = (await session.execute(stmt)).all()
        print(votes)

    def format_choice(choice: db.PollChoice) -> str:
        return f"🟦 `00.00%` {choice.label}"

    embed.description = "\n".join(
        (
            f"{_('Ends in : ')} <t:{1000000}:R>\n",
            "\n".join(format_choice(choice) for choice in poll.choices),
        )
    )

    if poll.type == db.PollType.BOOLEAN:
        embed.add_field(name=f"YES `00.00%` {__('yes')}", value="\u200b", inline=False)
        embed.add_field(name=f"NO `00.00%` {__('no')}", value="\u200b", inline=False)

    embed.set_footer(text=_("Poll created by <@{}>", poll.author_id))
    return Response(content=content, embed=embed)


class PollCog(SpecialCog["MyBot"]):
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
            await inter.response.send_modal(PollModal(self.bot, poll))


# class PollCreationStep1(ui.View):
#     def __init__(self, original_inter: Interaction, poll_type: int):
#         super().__init__()

#         self.poll_type = poll_type
#         self.original_inter = original_inter

#         self.public_results_value = 0
#         self.users_can_change_answer_value = 1

#         self.cancel.label = _("Cancel")
#         self.next.label = _("Next")

#         self.build_view()

#     async def disable_view(self):
#         self.public_results.disabled = True
#         self.users_can_change_answer.disabled = True
#         self.next.disabled = True
#         self.cancel.disabled = True

#         await self.original_inter.edit_original_response(view=self)

#     def build_view(self):
#         toggle_emojis = {0: Emojis.toggle_off, 1: Emojis.toggle_on}

#         self.public_results.emoji = toggle_emojis[self.public_results_value]
#         self.public_results.label = _("The results are {}.", _("public") if self.public_results_value else _("private"))
#         self.users_can_change_answer.emoji = toggle_emojis[self.users_can_change_answer_value]
#         self.users_can_change_answer.label = _(
#             "Users {} change their answer once voted.", _("can") if self.users_can_change_answer_value else _("can't")
#         )

#     @ui.button(row=0, style=discord.ButtonStyle.gray)
#     async def public_results(self, inter: discord.Interaction, button: ui.Button[Self]):
#         self.public_results_value = not self.public_results_value
#         self.build_view()
#         await inter.response.edit_message(view=self)

#     @ui.button(row=1, style=discord.ButtonStyle.gray)
#     async def users_can_change_answer(self, inter: discord.Interaction, button: ui.Button[Self]):
#         self.users_can_change_answer_value = not self.users_can_change_answer_value
#         self.build_view()
#         await inter.response.edit_message(view=self)

#     @ui.button(row=4, style=discord.ButtonStyle.green)
#     async def next(self, inter: discord.Interaction, button: ui.Button[Self]):
#         if self.poll_type == 1:
#             await inter.response.send_modal(ChoicesPollModal(self))
#         else:
#             await inter.response.send_modal(PollModal(self))

#     @ui.button(row=4, style=discord.ButtonStyle.red)
#     async def cancel(self, inter: discord.Interaction, button: ui.Button[Self]):
#         await inter.response.send_message(_("Poll creation cancelled."), ephemeral=True)
#         await self.disable_view()
#         self.stop()

#     async def on_timeout(self):
#         await self.disable_view()


class PollModal(ui.Modal):
    def __init__(self, bot: MyBot, poll: db.Poll):
        super().__init__(title=_("Create a new poll"), timeout=None)

        self.bot = bot
        self.poll = poll

        self.question = ui.TextInput[PollModal](
            label=_("Poll question"), placeholder=_("Do you agree this bot is awesome?")
        )
        self.add_item(self.question)

    async def on_submit(self, interaction: discord.Interaction):
        self.poll.title = self.question.value
        await interaction.response.send_message(
            **(await build_poll_visual(self.poll, self.bot)), view=EditPoll(self.bot, self.poll, True), ephemeral=True
        )


class ChoicesPollModal(PollModal):
    def __init__(self, bot: MyBot, poll: db.Poll):
        super().__init__(bot, poll)

        self.choice1 = ui.TextInput[Self](
            label=_("Choice 1"),
            placeholder=_("Yes, totally!"),
        )
        self.choice2 = ui.TextInput[Self](
            label=_("Choice 2"),
            placeholder=_("Absolutely!"),
        )

        self.add_item(self.choice1)
        self.add_item(self.choice2)

    async def on_submit(self, interaction: discord.Interaction):
        self.poll.title = self.question.value
        self.poll.choices.append(db.PollChoice(poll_id=self.poll.id, label=self.choice1.value))
        self.poll.choices.append(db.PollChoice(poll_id=self.poll.id, label=self.choice2.value))

        # TODO : TEMP
        self.poll.choices.append(db.PollChoice(poll_id=self.poll.id, label=self.choice2.value))
        self.poll.choices.append(db.PollChoice(poll_id=self.poll.id, label=self.choice2.value))

        # PollChoice(poll_id=self.poll.id, label=self.choice1.value)
        # PollChoice(poll_id=self.poll.id, label=self.choice2.value)
        await interaction.response.send_message(
            **(await build_poll_visual(self.poll, self.bot)), view=EditPoll(self.bot, self.poll, True), ephemeral=True
        )


class EditPoll(ui.View):
    def __init__(self, bot: MyBot, poll: db.Poll, new: bool):
        super().__init__()

        self.new = new
        self.poll = poll
        self.bot = bot

        print(poll.choices)

        self.build_view()

    def build_view(self):
        self.edit_title.label = _("Edit title")
        self.edit_description.label = _("Edit description")
        self.set_ending_time.label = _("Set ending time")
        self.edit_choices.label = _("Edit choices")

        if self.poll.type == db.PollType.CHOICE:
            self.edit_choices.disabled = False
        else:
            self.edit_choices.disabled = True

        self.public_results.label = _("The results are {}.", _("public") if self.poll.public_results else _("private"))
        self.users_can_change_answer.label = _(
            "Users {} change their answer once voted.", _("can") if self.poll.users_can_change_answer else _("can't")
        )

        if self.new:
            self.cancel_or_end.label = _("Cancel")
        else:
            self.cancel_or_end.label = _("End poll")

        self.save.label = _("Save")

    @ui.button(row=0, style=discord.ButtonStyle.blurple)
    async def edit_title(self, inter: discord.Interaction, button: ui.Button[Self]):
        pass

    @ui.button(row=0, style=discord.ButtonStyle.blurple)
    async def edit_description(self, inter: discord.Interaction, button: ui.Button[Self]):
        pass

    @ui.button(row=0, style=discord.ButtonStyle.blurple)
    async def set_ending_time(self, inter: discord.Interaction, button: ui.Button[Self]):
        pass

    @ui.button(row=0, style=discord.ButtonStyle.blurple)
    async def edit_choices(self, inter: discord.Interaction, button: ui.Button[Self]):
        pass

    @ui.button(row=1, style=discord.ButtonStyle.gray)
    async def public_results(self, inter: discord.Interaction, button: ui.Button[Self]):
        self.public_results_value = not self.public_results_value
        self.build_view()
        await inter.response.edit_message(view=self)

    @ui.button(row=2, style=discord.ButtonStyle.gray)
    async def users_can_change_answer(self, inter: discord.Interaction, button: ui.Button[Self]):
        self.users_can_change_answer_value = not self.users_can_change_answer_value
        self.build_view()
        await inter.response.edit_message(view=self)

    @ui.button(row=4, style=discord.ButtonStyle.red)
    async def cancel_or_end(self, inter: discord.Interaction, button: ui.Button[Self]):
        pass

    @ui.button(row=4, style=discord.ButtonStyle.green)
    async def save(self, inter: discord.Interaction, button: ui.Button[Self]):
        view = PollPublicMenu(self.bot)
        view.localize()
        await inter.response.send_message(**(await build_poll_visual(self.poll, self.bot)), view=view)
        self.poll.message_id = (await inter.original_response()).id

        async with self.bot.async_session.begin() as session:
            guild_id: int = inter.guild_id  # type: ignore (poll is only usable in guild)
            await self.bot.get_guild_db(guild_id, session=session)  # to be sure the guild is present in the database
            session.add(self.poll)


class EditPollChoices(ui.View):
    def __init__(self, parent: EditPoll):
        self.parent = parent
        super().__init__()
        self.localize_view()

    def localize_view(self):
        self.add_choice.label = _("Add a choice")
        self.remove_choice.label = _("Remove a choice")

    @ui.button(row=0, style=discord.ButtonStyle.blurple)
    async def add_choice(self, inter: discord.Interaction, button: ui.Button[Self]):
        pass

    @ui.button(row=0, style=discord.ButtonStyle.blurple)
    async def remove_choice(self, inter: discord.Interaction, button: ui.Button[Self]):
        pass


class PollPublicMenu(ui.View):
    """
    Here, localize NEEDS to be called outside the view itself. Don't forget to do it!
    """

    def __init__(self, bot: MyBot):
        self.bot = bot
        super().__init__(timeout=None)

    def localize(self):
        self.vote.label = _("Vote")

    @ui.button(style=discord.ButtonStyle.blurple, custom_id="poll_vote_button")
    async def vote(self, inter: discord.Interaction, button: ui.Button[Self]):
        message_id: int = inter.message.id  # type: ignore (interaction is a button, so it has a message)
        async with self.bot.async_session.begin() as session:
            stmt = db.select(db.Poll).where(db.Poll.message_id == message_id).options(selectinload(db.Poll.choices))
            poll = (await session.execute(stmt)).scalar_one()

            if poll.closed:
                await inter.response.send_message("closed.")  # TODO
                return

            stmt = (
                db.select(db.PollAnswer)
                .where(db.PollAnswer.poll_id == poll.id)
                .where(db.PollAnswer.user_id == inter.user.id)
            )
            votes = (await session.execute(stmt)).scalars().all()

            if not poll.users_can_change_answer and len(votes) > 0:
                await inter.response.send_message("You already voted.")  # TODO
                return

        await inter.response.send_message("U noob.")


class ChoicePollVote(ui.View):
    def __init__(self, bot: MyBot, poll: db.Poll, user_votes: list[db.PollAnswer]):
        self.bot = bot
        self.user_votes = user_votes
        self.poll = poll
        super().__init__(timeout=180)

    @classmethod
    async def message(cls, bot: MyBot, poll: db.Poll, user_votes: list[db.PollAnswer]) -> Response:
        return Response()

    @ui.select()
    async def choice(self, inter: discord.Interaction, select: ui.Select[Self]):
        pass

    @ui.button(style=discord.ButtonStyle.red)
    async def cancel(self, inter: discord.Interaction, button: ui.Button[Self]):
        pass

    @ui.button(style=discord.ButtonStyle.green)
    async def validate(self, inter: discord.Interaction, button: ui.Button[Self]):
        pass


class BooleanPollVote(ui.View):
    def __init__(self, bot: MyBot, poll: db.Poll, user_votes: list[db.PollAnswer]):
        self.bot = bot
        self.user_votes = user_votes
        self.poll = poll
        super().__init__(timeout=180)

    @classmethod
    async def message(cls, bot: MyBot, poll: db.Poll, user_votes: list[db.PollAnswer]) -> Response:
        return Response()

    @ui.button()
    async def yes(self, inter: discord.Interaction, button: ui.Button[Self]):
        pass

    @ui.button()
    async def no(self, inter: discord.Interaction, button: ui.Button[Self]):
        pass


class OpinionPollVote(ui.View):
    def __init__(self, bot: MyBot, poll: db.Poll, user_votes: list[db.PollAnswer]):
        self.bot = bot
        self.user_votes = user_votes
        self.poll = poll
        super().__init__(timeout=180)

    @classmethod
    async def message(cls, bot: MyBot, poll: db.Poll, user_votes: list[db.PollAnswer]) -> Response:
        return Response()

    # TODO


class EntryPollVote(ui.Modal):
    def __init__(self, bot: MyBot, poll: db.Poll, user_votes: list[db.PollAnswer]):
        self.bot = bot
        self.user_votes = user_votes
        self.poll = poll
        super().__init__(timeout=180)

    @classmethod
    async def message(cls, bot: MyBot, poll: db.Poll, user_votes: list[db.PollAnswer]) -> Response:
        return Response()

    # TODO


async def setup(bot: MyBot):
    await bot.add_cog(PollCog(bot))
