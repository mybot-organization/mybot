from __future__ import annotations

import json
import logging
from collections.abc import Awaitable, Callable
from functools import partial
from typing import TYPE_CHECKING, Concatenate

from aiohttp import hdrs, web

from core import ExtendedCog, config, db
from core.db.queries.poll import get_poll_answers

if TYPE_CHECKING:
    from mybot import MyBot


logger = logging.getLogger(__name__)


def route(method: str, path: str):
    def wrap[C: ExtendedCog](func: Callable[Concatenate[C, web.Request, ...], Awaitable[web.Response]]):
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
        logger.info("Server started on address 0.0.0.0:8080")
        await site.start()

    async def cog_unload(self) -> None:
        await self.app.shutdown()
        await self.runner.cleanup()

    @route(hdrs.METH_GET, r"/poll/{poll_url}/")
    async def poll(self, request: web.Request):
        poll_url = request.match_info["poll_url"]
        result = await db.get_poll_informations(self.bot)(poll_url)
        if result is None:
            return web.Response(status=404)

        return web.Response(text=json.dumps(result))

    @route(hdrs.METH_GET, r"/poll/{poll_url}/{choice_id:\d+}/")
    async def poll_votes(self, request: web.Request):
        poll_url = request.match_info["poll_url"]
        choice_id = int(request.match_info["choice_id"])
        try:
            from_ = int(request.query.get("from", 0))
            number = max(int(request.query.get("number", 10)), 100)
        except ValueError:
            return web.Response(status=400)

        votes = await get_poll_answers(self.bot)(poll_url, choice_id, from_, number)

        return web.Response(text=json.dumps(votes))


async def setup(bot: MyBot):
    await bot.add_cog(API(bot))
