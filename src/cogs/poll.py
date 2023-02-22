# TODO : allow editing of poll

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Self, Sequence

import discord
from discord import Embed, app_commands, ui
from discord.app_commands import locale_str as __
from discord.utils import get
from sqlalchemy import func
from sqlalchemy.orm import selectinload

from core import Emojis, Response, SpecialCog, db
from core.i18n import _

if TYPE_CHECKING:
    from discord import Interaction

    from mybot import MyBot


logger = logging.getLogger(__name__)


COLORS_ORDER = ["blue", "red", "yellow", "purple", "brown", "green", "orange"]
CHOICE_LEGEND_EMOJIS = [getattr(Emojis, f"{color}_round") for color in COLORS_ORDER]
GRAPH_EMOJIS = [getattr(Emojis, f"{color}_mid") for color in COLORS_ORDER]
RIGHT_CORNER_EMOJIS = [getattr(Emojis, f"{color}_right") for color in COLORS_ORDER]
LEFT_CORNER_EMOJIS = [getattr(Emojis, f"{color}_left") for color in COLORS_ORDER]
BOOLEAN_LEGEND_EMOJIS = [Emojis.thumb_down, Emojis.thumb_up]


class PollVisual:
    votes: dict[str, int] | None
    total_votes: int | None

    def __init__(self, poll: db.Poll, bot: MyBot, old_embed: Embed | None = None):
        self.poll = poll
        self.bot = bot
        self.old_embed = old_embed

    async def build(self) -> Response:
        content = self.poll.description
        embed = Embed(title=self.poll.title)

        if self.poll.public_results == True:
            async with self.bot.async_session.begin() as session:
                stmt = (
                    db.select(db.PollAnswer.value, func.count())
                    .select_from(db.PollAnswer)
                    .where(db.PollAnswer.poll_id == self.poll.id)
                    .group_by(db.PollAnswer.value)
                )
                self.votes = dict((await session.execute(stmt)).all())  # type: ignore
                self.total_votes = sum(self.votes.values())  # type: ignore
        else:
            self.votes = None
            self.total_votes = None

        description_split: list[str] = []
        description_split.append(self.build_end_date())
        description_split.append(self.build_legend())

        embed.description = "\n".join(description_split)

        if self.poll.public_results:
            embed.add_field(name="\u200b", value=self.build_graph())

        if self.old_embed:
            embed.set_footer(text=self.old_embed.footer.text)
        else:
            author = await self.bot.getch_user(self.poll.author_id)
            embed.set_footer(text=_("Poll created by {}", author.name if author else "unknown"))

        return Response(content=content, embed=embed)

    def build_end_date(self) -> str:
        if self.poll.end_date is None:
            return _("No end date.\n")
        if self.poll.closed:
            return _("Poll closed.\n")
        if self.poll.end_date < datetime.utcnow():
            return _("Poll ended.\n")
        return _("Poll ends <t:{}:R>\n", int(self.poll.end_date.timestamp()))

    def calculate_proportion(self, vote_value: str) -> float:
        if self.total_votes is None or self.votes is None or self.total_votes == 0:
            return 0
        return self.votes.get(vote_value, 0) / self.total_votes

    def build_legend(self) -> str:
        match self.poll.type:
            case db.PollType.CHOICE:

                def format_legend_choice(index: int, choice: db.PollChoice) -> str:
                    if self.poll.public_results == False:
                        return f"{CHOICE_LEGEND_EMOJIS[index]} {choice.label}"
                    percent = self.calculate_proportion(str(choice.id)) * 100
                    return f"{CHOICE_LEGEND_EMOJIS[index]} `{percent:6.2f}%` {choice.label}"

                return "\n".join(format_legend_choice(i, choice) for i, choice in enumerate(self.poll.choices))
            case db.PollType.BOOLEAN:

                def format_legend_boolean(boolean_value: bool) -> str:
                    if self.poll.public_results == False:
                        return f"{BOOLEAN_LEGEND_EMOJIS[boolean_value]} {_('Yes!') if boolean_value else _('No!')}"
                    return f"{BOOLEAN_LEGEND_EMOJIS[boolean_value]} `{self.calculate_proportion('1' if boolean_value else '0') * 100:6.2f}%` {_('Yes!') if boolean_value else _('No!')}"

                return "\n".join((format_legend_boolean(True), format_legend_boolean(False)))
            case db.PollType.OPINION:
                return ""
            case db.PollType.ENTRY:
                return ""

    def build_graph(self) -> str:
        if self.total_votes is None or self.votes is None:
            return ""
        if self.total_votes == 0:
            return f"{Emojis.white_left}{Emojis.white_mid * 10}{Emojis.white_right}"

        graph: list[str] = []
        match self.poll.type:
            case db.PollType.CHOICE:
                for i, choice in enumerate(self.poll.choices):
                    proportion = self.calculate_proportion(str(choice.id))
                    graph.extend([GRAPH_EMOJIS[i]] * round(proportion * 12))
            case _:
                pass

        if len(graph) < 12:
            graph.extend(graph[-1] * (12 - len(graph)))  # TODO : this is a temporary solution.

        graph = graph[:12]
        graph[0] = LEFT_CORNER_EMOJIS[GRAPH_EMOJIS.index(graph[0])]
        graph[-1] = RIGHT_CORNER_EMOJIS[GRAPH_EMOJIS.index(graph[-1])]

        return "".join(graph)


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
            **(await PollVisual(self.poll, self.bot).build()), view=EditPoll(self.bot, self.poll, True), ephemeral=True
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
            **(await PollVisual(self.poll, self.bot).build()), view=EditPoll(self.bot, self.poll, True), ephemeral=True
        )


class EditPoll(ui.View):
    def __init__(self, bot: MyBot, poll: db.Poll, new: bool):
        super().__init__()

        self.new = new
        self.poll = poll
        self.bot = bot

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
        self.poll.public_results = not self.poll.public_results
        self.build_view()
        await inter.response.edit_message(view=self)

    @ui.button(row=2, style=discord.ButtonStyle.gray)
    async def users_can_change_answer(self, inter: discord.Interaction, button: ui.Button[Self]):
        self.poll.users_can_change_answer = not self.poll.users_can_change_answer
        self.build_view()
        await inter.response.edit_message(view=self)

    @ui.button(row=4, style=discord.ButtonStyle.red)
    async def cancel_or_end(self, inter: discord.Interaction, button: ui.Button[Self]):
        pass

    @ui.button(row=4, style=discord.ButtonStyle.green)
    async def save(self, inter: discord.Interaction, button: ui.Button[Self]):
        view = PollPublicMenu(self.bot)
        view.localize()
        await inter.response.send_message(**(await PollVisual(self.poll, self.bot).build()), view=view)
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

        if poll.type == db.PollType.CHOICE:
            await inter.response.send_message(
                **(await ChoicePollVote.message(self.bot, poll, votes)),
                view=ChoicePollVote(self.bot, poll, votes, inter),
                ephemeral=True,
            )


class ChoicePollVote(ui.View):
    def __init__(self, bot: MyBot, poll: db.Poll, user_votes: Sequence[db.PollAnswer], base_inter: Interaction):
        super().__init__(timeout=180)

        self.bot = bot
        self.user_votes = user_votes
        self.poll = poll
        self.base_inter = base_inter

        self.choice.max_values = poll.max_answers
        self.choice.min_values = 0
        for choice in poll.choices:
            self.choice.add_option(
                label=choice.label,
                value=str(choice.id),
                default=any(str(choice.id) == vote.value for vote in user_votes[: poll.max_answers]),
            )

        self.localize()

    def localize(self):
        self.cancel.label = _("Cancel")
        self.validate.label = _("Validate")

    def build_view(self):
        for option in self.choice.options:
            option.default = any(option.value == value for value in self.choice.values)

    def disable_view(self):
        self.cancel.disabled = True
        self.validate.disabled = True
        self.choice.disabled = True

    @classmethod
    async def message(cls, bot: MyBot, poll: db.Poll, user_votes: Sequence[db.PollAnswer]) -> Response:
        return Response()

    @ui.select()
    async def choice(self, inter: discord.Interaction, select: ui.Select[Self]):
        self.build_view()
        await inter.response.edit_message(view=self)

    @ui.button(style=discord.ButtonStyle.red)
    async def cancel(self, inter: discord.Interaction, button: ui.Button[Self]):
        pass

    @ui.button(style=discord.ButtonStyle.green)
    async def validate(self, inter: discord.Interaction, button: ui.Button[Self]):
        new_answers = {value for value in self.choice.values}
        old_answers = {answer.value for answer in self.user_votes}

        async with self.bot.async_session.begin() as session:
            for remove_anwser in old_answers - new_answers:
                poll_answer: db.PollAnswer = get(self.user_votes, value=remove_anwser)  # type: ignore
                await session.delete(poll_answer)

            for add_answer in new_answers - old_answers:
                poll_answer = db.PollAnswer(poll_id=self.poll.id, user_id=inter.user.id, value=add_answer)
                session.add(poll_answer)

            # await session.commit()

        self.disable_view()
        await inter.response.edit_message(view=self)
        try:
            message: discord.Message = self.base_inter.message  # type: ignore
            old_embed = message.embeds[0] if message.embeds else None
            await message.edit(**(await PollVisual(self.poll, self.bot, old_embed).build()))
        except discord.NotFound:
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
