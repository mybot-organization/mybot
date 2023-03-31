# TODO(airo.pi_): implement anonymous votes

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Self, Sequence, cast

import discord
from discord import ui
from discord.utils import get
from sqlalchemy.orm import selectinload

from core import Menu, ResponseType, db, response_constructor
from core.constants import Emojis
from core.i18n import _

from .constants import LEGEND_EMOJIS
from .display import PollDisplay

if TYPE_CHECKING:
    from discord import Interaction

    from mybot import MyBot

    from . import PollCog


class PollPublicMenu(Menu["MyBot"]):
    def __init__(self, cog: PollCog, poll: db.Poll | None = None):
        super().__init__(bot=cog.bot, timeout=None)

        self.cog = cog
        self.poll = poll

    def get_current_votes(self, poll: db.Poll) -> dict[int, tuple[Interaction, ui.View]]:
        return self.cog.current_votes.setdefault(poll.id, {})

    async def build(self) -> Self:
        self.vote.label = _("Vote")
        return self

    @ui.button(style=discord.ButtonStyle.blurple, custom_id="poll_vote_button")
    async def vote(self, inter: discord.Interaction, button: ui.Button[Self]):
        del button  # unused
        message_id: int = inter.message.id  # type: ignore (interaction is a button, so it has a message)
        async with self.bot.async_session.begin() as session:
            stmt = db.select(db.Poll).where(db.Poll.message_id == message_id).options(selectinload(db.Poll.choices))
            poll = (await session.execute(stmt)).scalar_one_or_none()

            if poll is None:
                await inter.response.send_message(
                    **response_constructor(
                        ResponseType.error, _("Sorry, this poll seems not to exist. Please contact an admin.")
                    ),
                    ephemeral=True,
                )
                return

            if poll.closed:
                await inter.response.send_message(
                    **response_constructor(
                        ResponseType.error, _("Sorry, this poll is closed, you can't vote anymore!")
                    ),
                    ephemeral=True,
                )
                return

            if poll.end_date is not None and poll.end_date < datetime.now(timezone.utc):
                await inter.response.send_message(
                    **response_constructor(ResponseType.error, _("Sorry, this poll is over, you can't vote anymore!")),
                    ephemeral=True,
                )
                return
            user = cast(discord.Member, inter.user)
            if poll.allowed_roles and not set(role.id for role in user.roles) & set(poll.allowed_roles):
                message_display = response_constructor(
                    ResponseType.error, _("Sorry, you need one of the following roles to vote :")
                )
                message_display.embed.description = ", ".join(f"<@&{role_id}>" for role_id in poll.allowed_roles)
                await inter.response.send_message(**message_display, ephemeral=True)
                return

            stmt = (
                db.select(db.PollAnswer)
                .where(db.PollAnswer.poll_id == poll.id)
                .where(db.PollAnswer.user_id == inter.user.id)
            )
            votes = (await session.execute(stmt)).scalars().all()

            if not poll.users_can_change_answer and len(votes) > 0:
                await inter.response.send_message(
                    **response_constructor(ResponseType.error, "You already voted, and you can't change your vote."),
                    ephemeral=True,
                )
                return

        current_votes = self.get_current_votes(poll)
        if inter.user.id in current_votes:
            await current_votes[inter.user.id][0].delete_original_response()
        current_votes[inter.user.id] = (inter, self)

        vote_menu_types = {
            db.PollType.CHOICE: ChoicePollVote,
            db.PollType.BOOLEAN: BooleanPollVote,
            db.PollType.OPINION: OpinionPollVote,
            db.PollType.ENTRY: EntryPollVote,
        }

        vote_menu = vote_menu_types[poll.type](self, poll, votes, inter)
        await inter.response.send_message(
            **(await vote_menu.message_display()),
            view=await vote_menu.build(),
            ephemeral=True,
        )


class VoteMenu(Menu["MyBot"]):
    parent: PollPublicMenu

    def __init__(
        self, parent: PollPublicMenu, poll: db.Poll, user_votes: Sequence[db.PollAnswer], base_inter: Interaction
    ):
        super().__init__(parent=parent, timeout=180)

        self.user_votes = user_votes
        self.poll = poll
        self.base_inter = base_inter

    async def on_timeout(self) -> None:
        self.clean_current_cache(self.base_inter.user.id)
        await super().on_timeout()

    async def update_poll_display(self):
        """Update the poll display."""
        if self.poll.public_results:
            try:
                message = cast(discord.Message, self.base_inter.message)  # type: ignore
                old_embed = message.embeds[0] if message.embeds else None
                await message.edit(**(await PollDisplay.build(self.poll, self.parent.bot, old_embed)))
            except discord.NotFound:
                pass

    def clean_current_cache(self, user_id: int):
        """Remove the user from the current voters list."""
        current_votes = self.parent.get_current_votes(self.poll)
        current_votes.pop(user_id, None)
        if not current_votes:  # not current votes anymore.
            self.parent.cog.current_votes.pop(self.poll.id, None)


class ChoicePollVote(VoteMenu):
    async def build(self) -> Self:
        self.remove_vote.label = _("Remove vote")
        self.validate.label = _("Validate")

        self.choice.max_values = self.poll.max_answers
        self.choice.min_values = 0

        for i, choice in enumerate(self.poll.choices):
            label = choice.label if len(choice.label) <= 100 else choice.label[:99] + "…"
            default = str(choice.id) in (vote.value for vote in self.user_votes[: self.poll.max_answers])

            self.choice.add_option(
                label=label,
                value=str(choice.id),
                default=default,
                emoji=LEGEND_EMOJIS[i],
            )

            if default:
                self.choice._values.append(str(choice.id))  # pyright: ignore [reportPrivateUsage]

        return await super().build()

    async def update(self):
        await super().update()
        self.remove_vote.disabled = len(self.choice.values) == 0

    @ui.select()
    async def choice(self, inter: Interaction, select: ui.Select[Self]):
        del select  # unused
        await self.message_refresh(inter, False)

    @ui.button(style=discord.ButtonStyle.red)
    async def remove_vote(self, inter: Interaction, button: ui.Button[Self]):
        del button  # unused
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
        del button  # unused
        new_answers = set(self.choice.values)
        old_answers = {answer.value for answer in self.user_votes}

        async with self.parent.bot.async_session.begin() as session:
            for remove_answer in old_answers - new_answers:
                poll_answer = cast(db.PollAnswer, get(self.user_votes, value=remove_answer))
                await session.delete(poll_answer)

            for add_answer in new_answers - old_answers:
                poll_answer = db.PollAnswer(poll_id=self.poll.id, user_id=inter.user.id, value=add_answer)
                session.add(poll_answer)

        await self.update_poll_display()
        await inter.response.edit_message(
            **response_constructor(ResponseType.success, _("Your vote has been taken into account!")), view=None
        )
        self.clean_current_cache(inter.user.id)


class BooleanPollVote(VoteMenu):
    async def build(self) -> Self:
        self.yes.label = _("Yes")
        self.no.label = _("No")
        return await super().build()

    async def update(self):
        self.yes.style = self.no.style = discord.ButtonStyle.grey
        if self.user_votes:
            if self.user_votes[0].value == "1":
                self.yes.style = discord.ButtonStyle.green
            else:
                self.no.style = discord.ButtonStyle.green

    @ui.button(emoji=Emojis.thumb_up)
    async def yes(self, inter: discord.Interaction, button: ui.Button[Self]):
        del button  # unused
        await self.callback(inter, "1")

    @ui.button(emoji=Emojis.thumb_down)
    async def no(self, inter: discord.Interaction, button: ui.Button[Self]):
        del button  # unused
        await self.callback(inter, "0")

    async def callback(self, inter: Interaction, value: str):
        text_response = _("Your vote has been taken into account!")
        async with self.parent.bot.async_session.begin() as session:
            if self.user_votes:
                if self.user_votes[0].value != value:
                    self.user_votes[0].value = value
                    session.add(self.user_votes[0])
                else:
                    await session.delete(self.user_votes[0])
                    text_response = _("Your vote has been removed.")
            else:
                session.add(db.PollAnswer(poll_id=self.poll.id, user_id=inter.user.id, value=value))

        await self.update_poll_display()
        await inter.response.edit_message(**response_constructor(ResponseType.success, text_response), view=None)
        self.clean_current_cache(inter.user.id)


class OpinionPollVote(VoteMenu):
    pass
    # TODO(airo.pi_): OPINION


class EntryPollVote(VoteMenu):
    pass
    # TODO(airo.pi_): ENTRY
