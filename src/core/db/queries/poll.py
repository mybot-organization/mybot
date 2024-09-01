from typing import TYPE_CHECKING, Any

import sqlalchemy as sql
from sqlalchemy import orm

from ..tables import Poll, PollAnswer, PollChoice, PollType
from ..utils import with_session

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@with_session
async def get_poll_informations(session: AsyncSession, message_id: int):
    query = sql.select(Poll).where(Poll.message_id == message_id).options(orm.noload(Poll.choices))
    result = await session.execute(query)
    poll = result.scalar_one_or_none()
    if poll is None:
        return None
    if poll.type == PollType.CHOICE:
        answer_count_subquery = (
            sql.select(
                sql.cast(PollAnswer.value, sql.Integer).label("choice_id"),
                sql.func.count(sql.PollAnswer.id).label("choice_count"),
            )
            .where(PollAnswer.poll_id == poll.id)
            .group_by(PollAnswer.value)
            .subquery()
        )
        user_ids_subquery = (
            sql.select(sql.cast(PollAnswer.value, sql.Integer).label("choice_id"), PollAnswer.user_id)
            .where(PollAnswer.poll_id == poll.id)
            .limit(3)
            .subquery()
        )
        query = (
            sql.select(
                PollChoice,
                sql.func.coalesce(answer_count_subquery.c.choice_count, 0).label("choice_count"),
                sql.func.array_agg(user_ids_subquery.c.user_id).label("user_ids"),
            )
            .outerjoin(
                answer_count_subquery,
                sql.PollChoice.id == answer_count_subquery.c.choice_id,
            )
            .outerjoin(
                user_ids_subquery,
                sql.PollChoice.id == user_ids_subquery.c.choice_id,
            )
            .where(PollChoice.poll_id == poll.id)
            .group_by(PollChoice.id, answer_count_subquery.c.choice_count)
        )
        result = await session.execute(query)
        choices = result.all()
        values: list[dict[str, Any]] = [
            {"id": c.id, "label": c.label, "count": nb, "users_preview": (users if users != [None] else [])}
            for c, nb, users in choices
        ]
    else:
        values = []

    return poll, values
