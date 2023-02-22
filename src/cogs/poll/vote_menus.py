from __future__ import annotations

from typing import TYPE_CHECKING, Self, Sequence, cast

import discord
from discord import ui
from discord.utils import get
from sqlalchemy.orm import selectinload

from core import Response, db
from core.i18n import _

from .constants import CHOICE_LEGEND_EMOJIS
from .display import PollDisplay

if TYPE_CHECKING:
    from discord import Interaction

    from core.db import Poll, PollAnswer
    from mybot import MyBot


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
                await inter.response.send_message("You already voted, and you can't change your vote.")  # TODO
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
        for i, choice in enumerate(poll.choices):
            label = choice.label if len(choice.label) <= 100 else choice.label[:99] + "…"
            self.choice.add_option(
                label=label,
                value=str(choice.id),
                default=any(str(choice.id) == vote.value for vote in user_votes[: poll.max_answers]),
                emoji=CHOICE_LEGEND_EMOJIS[i],
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

    @ui.select()  # type: ignore (idk why there is an error here)
    async def choice(self, inter: Interaction, select: ui.Select[Self]):
        self.build_view()
        await inter.response.edit_message(view=self)

    @ui.button(style=discord.ButtonStyle.red)
    async def cancel(self, inter: Interaction, button: ui.Button[Self]):
        pass

    @ui.button(style=discord.ButtonStyle.green)
    async def validate(self, inter: Interaction, button: ui.Button[Self]):
        new_answers = {value for value in self.choice.values}
        old_answers = {answer.value for answer in self.user_votes}

        async with self.bot.async_session.begin() as session:
            for remove_anwser in old_answers - new_answers:
                poll_answer = cast(db.PollAnswer, get(self.user_votes, value=remove_anwser))
                await session.delete(poll_answer)

            for add_answer in new_answers - old_answers:
                poll_answer = db.PollAnswer(poll_id=self.poll.id, user_id=inter.user.id, value=add_answer)
                session.add(poll_answer)

            # await session.commit()

        self.disable_view()
        await inter.response.defer()
        await inter.delete_original_response()

        if self.poll.public_results:
            try:
                message = cast(discord.Message, self.base_inter.message)  # type: ignore
                old_embed = message.embeds[0] if message.embeds else None
                await message.edit(**(await PollDisplay(self.poll, self.bot, old_embed).build()))
            except discord.NotFound:
                pass


class BooleanPollVote(ui.View):
    def __init__(self, bot: MyBot, poll: Poll, user_votes: list[PollAnswer]):
        self.bot = bot
        self.user_votes = user_votes
        self.poll = poll
        super().__init__(timeout=180)

    @classmethod
    async def message(cls, bot: MyBot, poll: Poll, user_votes: list[PollAnswer]) -> Response:
        return Response()

    @ui.button()
    async def yes(self, inter: discord.Interaction, button: ui.Button[Self]):
        pass

    @ui.button()
    async def no(self, inter: discord.Interaction, button: ui.Button[Self]):
        pass


class OpinionPollVote(ui.View):
    def __init__(self, bot: MyBot, poll: Poll, user_votes: list[PollAnswer]):
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
