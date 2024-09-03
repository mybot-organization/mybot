from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypedDict

import sqlalchemy as sql
from sqlalchemy import orm

from ..tables import Poll, PollAnswer, PollChoice, PollType, UserDB
from ..utils import with_session

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class PollInformation(TypedDict):
    poll_id: int
    title: str
    description: str | None
    type: int
    values: list[ChoiceInformation]


class ChoiceInformation(TypedDict):
    id: int
    label: str
    count: int
    answers_preview: list[AnswerInformation]


class AnonAnswerInformation(TypedDict):
    username: None
    avatar: None
    anonymous: Literal[True]


class PublicAnswerInformation(TypedDict):
    username: str
    avatar: str
    anonymous: Literal[False]


AnswerInformation = AnonAnswerInformation | PublicAnswerInformation


@with_session
async def get_poll_informations(session: AsyncSession, poll_url: str) -> PollInformation | None:
    query = sql.select(Poll).where(Poll.url == poll_url).options(orm.noload(Poll.choices))
    result = await session.execute(query)
    poll = result.scalar_one_or_none()
    if poll is None:
        return None
    if poll.type == PollType.CHOICE:
        answer_count_subquery = (
            sql.select(
                sql.cast(PollAnswer.value, sql.Integer).label("choice_id"),
                sql.func.count(PollAnswer.id).label("choice_count"),
            )
            .where(PollAnswer.poll_id == poll.id)
            .group_by(PollAnswer.value)
            .subquery()
        )
        user_ids_subquery = (
            sql.select(
                sql.cast(PollAnswer.value, sql.Integer).label("choice_id"), PollAnswer.user_id, PollAnswer.anonymous
            )
            .where(PollAnswer.poll_id == poll.id)
            .limit(3)
            .subquery()
        )
        query = (
            sql.select(
                PollChoice,
                sql.func.coalesce(answer_count_subquery.c.choice_count, 0).label("choice_count"),
                sql.func.array_agg(UserDB.username).label("usernames"),
                sql.func.array_agg(UserDB.avatar).label("avatars"),
                sql.func.array_agg(user_ids_subquery.c.anonymous).label("anon"),
            )
            .outerjoin(
                answer_count_subquery,
                PollChoice.id == answer_count_subquery.c.choice_id,
            )
            .outerjoin(
                user_ids_subquery,
                PollChoice.id == user_ids_subquery.c.choice_id,
            )
            .outerjoin(UserDB, user_ids_subquery.c.user_id == UserDB.user_id)
            .where(PollChoice.poll_id == poll.id)
            .group_by(PollChoice.id, answer_count_subquery.c.choice_count)
        )
        result = await session.execute(query)
        choices = result.all()
        values: list[ChoiceInformation] = [
            {
                "id": c.id,
                "label": c.label,
                "count": nb,
                "answers_preview": [
                    {
                        "username": username if not an else None,
                        "avatar": avatar if not an else None,
                        "anonymous": an,
                    }
                    for username, avatar, an in zip(usernames, avatars, anon)
                ]
                # Postgres return [NULL] instead of an empty array, so we replace [None] with [].
                # There is a minor scenario where this is a problem: if there is exactly one vote from a user why is not in the database.
                # This minor case is ignored for now.
                if usernames != [None]
                else [],
            }
            for c, nb, usernames, avatars, anon in choices
        ]
    else:
        values = []

    return PollInformation(
        poll_id=poll.id, title=poll.title, description=poll.description, type=poll.type.value, values=values
    )


@with_session
async def get_poll_answers(
    session: AsyncSession, poll_url: str, choice_id: int, from_: int, number: int
) -> list[AnswerInformation]:
    result = await session.execute(
        sql.select(
            PollAnswer.anonymous,
            UserDB.username,
            UserDB.avatar,
        )
        .join(Poll, Poll.id == PollAnswer.poll_id)
        .outerjoin(UserDB, PollAnswer.user_id == UserDB.user_id)
        .where(
            Poll.url == poll_url,
            PollAnswer.poll_id == Poll.id,
            PollAnswer.value == str(choice_id),
        )
        .limit(number)
        .offset(from_)
    )
    return [
        {
            "username": username if not anon else None,
            "avatar": avatar if not anon else None,
            "anonymous": anon,
        }
        for anon, username, avatar in result.all()
    ]
