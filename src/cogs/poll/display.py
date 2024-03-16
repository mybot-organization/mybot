from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from sqlalchemy import func

from core import Emojis, db
from core.i18n import _
from core.response import MessageDisplay

from .constants import (
    BOOLEAN_INDEXES,
    COLOR_TO_HEX,
    COLORS_ORDER,
    DB_VALUE_TO_BOOLEAN,
    GRAPH_EMOJIS,
    LEFT_CORNER_EMOJIS,
    LEGEND_EMOJIS,
    RIGHT_CORNER_EMOJIS,
)

if TYPE_CHECKING:
    from discord import Embed

    from core.db import Poll
    from mybot import MyBot


class PollDisplay:
    def __init__(self, poll: Poll, votes: dict[str, int] | None):
        self.poll: Poll = poll
        self.votes = votes

    @classmethod
    async def build(cls, poll: Poll, bot: MyBot, old_embed: Embed | None = None) -> MessageDisplay:
        content = poll.description
        embed = discord.Embed(title=poll.title)

        votes: dict[str, int] | None
        if poll.public_results is True:
            async with bot.async_session.begin() as session:
                stmt = (
                    db.select(db.PollAnswer.value, func.count())
                    .select_from(db.PollAnswer)
                    .where(db.PollAnswer.poll_id == poll.id)
                    .group_by(db.PollAnswer.value)
                )
                # a generator is used for typing purposes
                votes = dict(
                    (key, value)
                    for key, value in (await session.execute(stmt)).all()  # choice_id: vote_count
                )
                if poll.type == db.PollType.CHOICE:
                    # when we delete a choice from a poll, the votes are still in the db before commit
                    # so we need to filter them
                    votes = {
                        key: value for key, value in votes.items() if key in (str(choice.id) for choice in poll.choices)
                    }
        else:
            votes = None

        poll_display = cls(poll, votes)

        description_split: list[str] = []
        description_split.append(poll_display.build_end_date())
        description_split.append(poll_display.build_legend())

        embed.description = "\n".join(description_split)

        if poll.public_results:
            embed.add_field(name="\u200b", value=poll_display.build_graph())
            embed.color = poll_display.build_color()

        if old_embed:
            embed.set_footer(text=old_embed.footer.text)
        else:
            author = await bot.getch_user(poll.author_id)
            embed.set_footer(text=_("Poll created by {}", author.name if author else "unknown"))

        return MessageDisplay(content=content, embed=embed)

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
                    if self.poll.public_results is False:
                        return f"{LEGEND_EMOJIS[index]} {choice.label}"
                    percent = self.calculate_proportion(str(choice.id)) * 100
                    return f"{LEGEND_EMOJIS[index]} `{percent:6.2f}%` {choice.label}"

                return "\n".join(format_legend_choice(i, choice) for i, choice in enumerate(self.poll.choices))
            case db.PollType.BOOLEAN:

                def format_legend_boolean(boolean_value: bool) -> str:
                    bool_text = _("Yes!") if boolean_value else _("No!")
                    if self.poll.public_results is False:
                        return f"{LEGEND_EMOJIS[BOOLEAN_INDEXES[boolean_value]]} {bool_text}"
                    percent = self.calculate_proportion("1" if boolean_value else "0") * 100
                    return f"{LEGEND_EMOJIS[BOOLEAN_INDEXES[boolean_value]]} `{percent:6.2f}%` {bool_text}"

                return "\n".join((format_legend_boolean(True), format_legend_boolean(False)))
            case db.PollType.OPINION:
                return ""
            case db.PollType.ENTRY:
                return ""

    def build_graph(self) -> str:
        if self.votes is None:  # self.votes is None if the poll is not public
            return ""

        graph: list[str] = []
        match self.poll.type:
            case db.PollType.CHOICE:
                if self.total_votes == 0:
                    return f"{Emojis.white_left}{Emojis.white_mid * 10}{Emojis.white_right}"

                for i, choice in enumerate(self.poll.choices):
                    proportion = self.calculate_proportion(str(choice.id))
                    graph.extend([GRAPH_EMOJIS[i]] * round(proportion * 12))

                if len(graph) < 12:
                    # This could be improved (if there is draws, it will be wrong)
                    graph.extend(graph[-1] * (12 - len(graph)))

                graph = graph[:12]
                graph[0] = LEFT_CORNER_EMOJIS[GRAPH_EMOJIS.index(graph[0])]
                graph[-1] = RIGHT_CORNER_EMOJIS[GRAPH_EMOJIS.index(graph[-1])]
            case db.PollType.BOOLEAN:
                if self.total_votes == 0:
                    return (
                        f"{Emojis.thumb_down}{Emojis.white_left}{Emojis.white_mid * 8}"
                        f"{Emojis.white_right}{Emojis.thumb_up}"
                    )

                for i, choice in enumerate(("1", "0")):
                    proportion = self.calculate_proportion(choice)
                    graph.extend([GRAPH_EMOJIS[i]] * round(proportion * 10))

                if len(graph) < 10:
                    graph.extend(graph[-1] * (10 - len(graph)))

                graph = graph[:10]
                graph[0] = LEFT_CORNER_EMOJIS[GRAPH_EMOJIS.index(graph[0])]
                graph[-1] = RIGHT_CORNER_EMOJIS[GRAPH_EMOJIS.index(graph[-1])]

                graph.insert(0, f"{Emojis.thumb_up} ")
                graph.append(f" {Emojis.thumb_down}")
            case _:
                pass

        return "".join(graph)

    def build_color(self) -> None | discord.Color:
        if not self.votes:
            return None

        ordered_votes = sorted(self.votes.items(), key=lambda item: item[1], reverse=True)
        if not (len(ordered_votes) == 1 or ordered_votes[0][1] != ordered_votes[1][1]):
            return None  # it's a draw !

        match self.poll.type:
            case db.PollType.CHOICE:
                choices_ids = [c.id for c in self.poll.choices]
                return discord.Color(COLOR_TO_HEX[COLORS_ORDER[choices_ids.index(int(ordered_votes[0][0]))]])
            case db.PollType.BOOLEAN:
                winner_index = BOOLEAN_INDEXES[DB_VALUE_TO_BOOLEAN[ordered_votes[0][0]]]
                return discord.Color(COLOR_TO_HEX[COLORS_ORDER[winner_index]])
            case _:
                return None
