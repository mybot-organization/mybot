from __future__ import annotations

from typing import TYPE_CHECKING, Concatenate

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from sqlalchemy.ext.asyncio import AsyncSession

    from mybot import MyBot


def with_session_begin[**P, R](
    fun: Callable[Concatenate[AsyncSession, P], Awaitable[R]],
) -> Callable[[MyBot], Callable[P, Awaitable[R]]]:
    def wrapper(bot: MyBot):
        async def inner(*args: P.args, **kwargs: P.kwargs) -> R:
            async with bot.async_session.begin() as session:
                return await fun(session, *args, **kwargs)

        return inner

    return wrapper


def with_session[**P, R](
    fun: Callable[Concatenate[AsyncSession, P], Awaitable[R]],
) -> Callable[[MyBot], Callable[P, Awaitable[R]]]:
    def wrapper(bot: MyBot):
        async def inner(*args: P.args, **kwargs: P.kwargs) -> R:
            async with bot.async_session() as session:
                return await fun(session, *args, **kwargs)

        return inner

    return wrapper
