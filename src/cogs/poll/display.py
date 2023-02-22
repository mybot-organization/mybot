from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import discord
from sqlalchemy import func

from core import Emojis, Response, db
from core.i18n import _

from .constants import (
    BOOLEAN_LEGEND_EMOJIS,
    CHOICE_LEGEND_EMOJIS,
    GRAPH_EMOJIS,
    LEFT_CORNER_EMOJIS,
    RIGHT_CORNER_EMOJIS,
)

if TYPE_CHECKING:
    from discord import Embed

    from core.db import Poll
    from main import MyBot


class PollDisplay:
    votes: dict[str, int] | None
    total_votes: int | None

    def __init__(self, poll: Poll, bot: MyBot, old_embed: Embed | None = None):
        self.poll = poll
        self.bot = bot
        self.old_embed = old_embed

    async def build(self) -> Response:
        content = self.poll.description
        embed = discord.Embed(title=self.poll.title)

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
        if self.poll.closed:
            return _("Poll closed.\n")
        if self.poll.end_date is None:
            return _("No end date.\n")
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
