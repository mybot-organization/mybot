from __future__ import annotations

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
    def __init__(self, poll: Poll, votes: dict[str, int] | None):
        self.poll = poll
        self.votes = votes

    @classmethod
    async def build(cls, poll: Poll, bot: MyBot, old_embed: Embed | None = None) -> Response:
        content = poll.description
        embed = discord.Embed(title=poll.title)

        votes: dict[str, int] | None
        if poll.public_results == True:
            async with bot.async_session.begin() as session:
                stmt = (
                    db.select(db.PollAnswer.value, func.count())
                    .select_from(db.PollAnswer)
                    .where(db.PollAnswer.poll_id == poll.id)
                    .group_by(db.PollAnswer.value)
                )
                # a generator is used for typing purposes
                votes = dict((key, value) for key, value in (await session.execute(stmt)).all())
        else:
            votes = None

        poll_display = cls(poll, votes)

        description_split: list[str] = []
        description_split.append(poll_display.build_end_date())
        description_split.append(poll_display.build_legend())

        embed.description = "\n".join(description_split)

        if poll.public_results:
            embed.add_field(name="\u200b", value=poll_display.build_graph())

        if old_embed:
            embed.set_footer(text=old_embed.footer.text)
        else:
            author = await bot.getch_user(poll.author_id)
            embed.set_footer(text=_("Poll created by {}", author.name if author else "unknown"))

        return Response(content=content, embed=embed)

    @property
    def total_votes(self) -> int:
        return sum(self.votes.values()) if self.votes else 0

    def build_end_date(self) -> str:
        if self.poll.closed:
            return _("Poll closed.\n")
        if self.poll.end_date is None:
            return _("No end date.\n")
        return _("Poll ends <t:{}:R>\n", int(self.poll.end_date.timestamp()))

    def calculate_proportion(self, vote_value: str) -> float:
        if self.votes is None or self.total_votes == 0:
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
                return ""  # TODO OPINION
            case db.PollType.ENTRY:
                return ""  # TODO ENTRY

    def build_graph(self) -> str:
        if self.votes is None:
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
                pass  # TODO OPINION, ENTRY, BOOLEAN

        if len(graph) < 12:
            # This could be improved (if there is draws, it will be wrong)
            graph.extend(graph[-1] * (12 - len(graph)))

        graph = graph[:12]
        graph[0] = LEFT_CORNER_EMOJIS[GRAPH_EMOJIS.index(graph[0])]
        graph[-1] = RIGHT_CORNER_EMOJIS[GRAPH_EMOJIS.index(graph[-1])]

        return "".join(graph)
