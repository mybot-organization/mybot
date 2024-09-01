from __future__ import annotations

import json
import logging
from collections.abc import Awaitable, Callable
from functools import partial
from os import getpid
from typing import TYPE_CHECKING, Concatenate, ParamSpec, TypeVar, cast

from aiohttp import hdrs, web
from psutil import Process

from core import ExtendedCog, config, db

if TYPE_CHECKING:
    from mybot import MyBot


logger = logging.getLogger(__name__)

P = ParamSpec("P")
S = TypeVar("S", bound="ExtendedCog")


def route(method: str, path: str):
    def wrap(func: Callable[Concatenate[S, web.Request, P], Awaitable[web.Response]]):
        func.__route__ = (method, path)  # type: ignore
        return func

    return wrap


class API(ExtendedCog):
    def __init__(self, bot: MyBot):
        super().__init__(bot)
        self.app = web.Application()
        self.runner = web.AppRunner(self.app)
        self.routes = web.RouteTableDef()

        for func in API.__dict__.values():
            if hasattr(func, "__route__"):
                self.routes.route(*func.__route__)(partial(func, self))

        self.app.add_routes(self.routes)

    async def cog_load(self):
        if not config.export_mode:
            self.bot.loop.create_task(self.start())

    async def start(self) -> None:
        await self.bot.wait_until_ready()

        await self.runner.setup()
        site = web.TCPSite(self.runner, "0.0.0.0", 8080)  # noqa: S104  # in a docker container
        print("Server started")
        await site.start()

    async def cog_unload(self) -> None:
        await self.app.shutdown()
        await self.runner.cleanup()

    @route(hdrs.METH_GET, "/memory")
    async def test(self, request: web.Request):
        rss = cast(int, Process(getpid()).memory_info().rss)  # pyright: ignore[reportUnknownMemberType]
        return web.Response(text=f"{round(rss / 1024 / 1024, 2)} MB")

    @route(hdrs.METH_GET, r"/poll/{poll_message_id:\d+}/")
    async def poll(self, request: web.Request):
        poll_message_id = int(request.match_info["poll_message_id"])
        result = await db.get_poll_informations(self.bot)(poll_message_id)
        if result is None:
            return web.Response(status=404)
        poll, values = result

        return web.Response(
            text=json.dumps(
                {
                    "poll_id": poll.id,
                    "title": poll.title,
                    "description": poll.description,
                    "type": poll.type.name,
                    "values": values,
                }
            )
        )

    @route(hdrs.METH_GET, r"/poll/{poll_message_id:\d+}/{choice_id:\d+}/")
    async def poll_votes(self, request: web.Request):
        message_id = int(request.match_info["poll_message_id"])
        choice_id = int(request.match_info["choice_id"])
        try:
            from_ = int(request.query.get("from", 0))
            number = max(int(request.query.get("number", 10)), 100)
        except ValueError:
            return web.Response(status=400)

        async with self.bot.async_session() as session:
            result = await session.execute(
                db.select(db.PollAnswer)
                .join(db.Poll)
                .where(db.Poll.message_id == message_id)
                .where(db.PollAnswer.poll_id == db.Poll.id, db.PollAnswer.value == str(choice_id))
                .limit(number)
                .offset(from_)
            )
            votes = result.scalars().all()

        return web.Response(
            text=json.dumps(
                [
                    {
                        "id": vote.id,
                        "user_id": vote.user_id,
                        "anonymous": vote.anonymous,
                    }
                    for vote in votes
                ]
            )
        )


async def setup(bot: MyBot):
    await bot.add_cog(API(bot))
