from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Self, Sequence, cast

import discord
from discord import ui
from discord.utils import get
from sqlalchemy.orm import selectinload

from core import Response, ResponseType, db, response_constructor
from core.i18n import _

from .constants import CHOICE_LEGEND_EMOJIS
from .display import PollDisplay

if TYPE_CHECKING:
    from discord import Interaction

    from core.db import Poll, PollAnswer
    from mybot import MyBot

    from . import PollCog


class PollPublicMenu(ui.View):
    def __init__(self, cog: PollCog):
        super().__init__(timeout=None)

        self.bot = cog.bot
        self.cog = cog

        self.result_url = ui.Button[Self](
            style=discord.ButtonStyle.link,
            label="View results",
            url="https://google.com/soon",
        )
        self.add_item(self.result_url)

    def get_current_votes(self, poll: db.Poll) -> dict[int, tuple[Interaction, ui.View]]:
        return self.cog.current_votes.setdefault(poll.id, {})

    def localize(self):
        self.vote.label = _("Vote")

    @classmethod
    def build(cls, cog: PollCog, poll: db.Poll) -> PollPublicMenu:
        view = cls(cog)
        view.result_url.disabled = not poll.public_results
        view.localize()
        return view

    @ui.button(style=discord.ButtonStyle.blurple, custom_id="poll_vote_button")
    async def vote(self, inter: discord.Interaction, button: ui.Button[Self]):
        message_id: int = inter.message.id  # type: ignore (interaction is a button, so it has a message)
        async with self.bot.async_session.begin() as session:
            stmt = db.select(db.Poll).where(db.Poll.message_id == message_id).options(selectinload(db.Poll.choices))
            poll = (await session.execute(stmt)).scalar_one()

            if poll.closed:
                await inter.response.send_message(
                    **response_constructor(ResponseType.error, _("Sorry, this poll is closed, you can't vote anymore!"))
                )
                return

            if poll.end_date is not None and poll.end_date < datetime.utcnow():
                await inter.response.send_message(
                    **response_constructor(ResponseType.error, _("Sorry, this poll is over, you can't vote anymore!"))
                )
                return

            stmt = (
                db.select(db.PollAnswer)
                .where(db.PollAnswer.poll_id == poll.id)
                .where(db.PollAnswer.user_id == inter.user.id)
            )
            votes = (await session.execute(stmt)).scalars().all()

            if not poll.users_can_change_answer and len(votes) > 0:
                await inter.response.send_message(
                    **response_constructor(ResponseType.error, "You already voted, and you can't change your vote.")
                )
                return

        if poll.type == db.PollType.CHOICE:
            current_votes = self.get_current_votes(poll)
            if inter.user.id in current_votes:
                await current_votes[inter.user.id][0].delete_original_response()
            current_votes[inter.user.id] = (inter, self)

            await inter.response.send_message(
                **(await ChoicePollVote.message(self.bot, poll, votes)),
                view=ChoicePollVote(self, poll, votes, inter),
                ephemeral=True,
            )

        # TODO OPINION, BOOLEAN, ENTRY


class ChoicePollVote(ui.View):
    def __init__(
        self, parent: PollPublicMenu, poll: db.Poll, user_votes: Sequence[db.PollAnswer], base_inter: Interaction
    ):
        super().__init__(timeout=180)

        self.parent = parent
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
        self.remove_vote.label = _("Remove vote")
        self.validate.label = _("Validate")

    def update_view(self):
        for option in self.choice.options:
            option.default = any(option.value == value for value in self.choice.values)
        self.remove_vote.disabled = len(self.choice.values) == 0

    async def on_timeout(self) -> None:
        self.clean_current_cache(self.base_inter.user.id)

    @classmethod
    async def message(cls, bot: MyBot, poll: db.Poll, user_votes: Sequence[db.PollAnswer]) -> Response:
        return Response()  # NOTE : don't know if a message is needed here.

    @ui.select()  # type: ignore (idk why there is an error here)
    async def choice(self, inter: Interaction, select: ui.Select[Self]):
        self.update_view()
        await inter.response.edit_message(view=self)

    @ui.button(style=discord.ButtonStyle.red)
    async def remove_vote(self, inter: Interaction, button: ui.Button[Self]):
        async with self.parent.bot.async_session.begin() as session:
            for answer in self.user_votes:
                await session.delete(answer)

        await self.update_poll_display()
        await inter.response.edit_message(
            **response_constructor(ResponseType.success, _("Your vote has been removed.")), view=None
        )
        self.clean_current_cache(inter.user.id)

    @ui.button(style=discord.ButtonStyle.green)
    async def validate(self, inter: Interaction, button: ui.Button[Self]):
        new_answers = {value for value in self.choice.values}
        old_answers = {answer.value for answer in self.user_votes}

        # TODO: if poll is edited while users votes, there can be some errors. Especially if a choice is removed.
        async with self.parent.bot.async_session.begin() as session:
            for remove_anwser in old_answers - new_answers:
                poll_answer = cast(db.PollAnswer, get(self.user_votes, value=remove_anwser))
                await session.delete(poll_answer)

            for add_answer in new_answers - old_answers:
                poll_answer = db.PollAnswer(poll_id=self.poll.id, user_id=inter.user.id, value=add_answer)
                session.add(poll_answer)

        await self.update_poll_display()
        await inter.response.edit_message(
            **response_constructor(ResponseType.success, _("Your vote has been taken into account!")), view=None
        )
        self.clean_current_cache(inter.user.id)

    async def update_poll_display(self):
        if self.poll.public_results:
            try:
                message = cast(discord.Message, self.base_inter.message)  # type: ignore
                old_embed = message.embeds[0] if message.embeds else None
                await message.edit(**(await PollDisplay.build(self.poll, self.parent.bot, old_embed)))
            except discord.NotFound:
                pass

    def clean_current_cache(self, user_id: int):
        current_votes = self.parent.get_current_votes(self.poll)
        current_votes.pop(user_id, None)
        if not current_votes:  # not current votes anymore.
            self.parent.cog.current_votes.pop(self.poll.id, None)


class BooleanPollVote(ui.View):
    def __init__(self, bot: MyBot, poll: Poll, user_votes: list[PollAnswer]):
        self.bot = bot
        self.user_votes = user_votes
        self.poll = poll
        super().__init__(timeout=180)

    @classmethod
    async def message(cls, bot: MyBot, poll: Poll, user_votes: list[PollAnswer]) -> Response:
        return Response()  # TODO BOOLEAN

    @ui.button()
    async def yes(self, inter: discord.Interaction, button: ui.Button[Self]):
        pass  # TODO BOOLEAN

    @ui.button()
    async def no(self, inter: discord.Interaction, button: ui.Button[Self]):
        pass  # TODO BOOLEAN


class OpinionPollVote(ui.View):
    def __init__(self, bot: MyBot, poll: Poll, user_votes: list[PollAnswer]):
        self.bot = bot
        self.user_votes = user_votes
        self.poll = poll
        super().__init__(timeout=180)

    @classmethod
    async def message(cls, bot: MyBot, poll: db.Poll, user_votes: list[db.PollAnswer]) -> Response:
        return Response()  # TODO OPINION

    # TODO OPINION


class EntryPollVote(ui.Modal):
    def __init__(self, bot: MyBot, poll: db.Poll, user_votes: list[db.PollAnswer]):
        self.bot = bot
        self.user_votes = user_votes
        self.poll = poll
        super().__init__(timeout=180)

    @classmethod
    async def message(cls, bot: MyBot, poll: db.Poll, user_votes: list[db.PollAnswer]) -> Response:
        return Response()  # TODO ENTRY

    # TODO ENTRY
