from __future__ import annotations

import logging
from functools import partial
from typing import TYPE_CHECKING, Awaitable, Callable, Concatenate, ParamSpec, TypeVar

from aiohttp import hdrs, web
from discord.ext.commands import Cog  # pyright: ignore[reportMissingTypeStubs]

if TYPE_CHECKING:
    from mybot import MyBot


logger = logging.getLogger(__name__)

P = ParamSpec("P")
S = TypeVar("S", bound="Cog")


def route(method: str, path: str):
    def wrap(func: Callable[Concatenate[S, web.Request, P], Awaitable[web.Response]]):
        func.__route__ = (method, path)  # type: ignore
        return func

    return wrap


class API(Cog):
    def __init__(self, bot: MyBot):
        self.bot: MyBot = bot
        self.app = web.Application()
        self.runner = web.AppRunner(self.app)
        self.routes = web.RouteTableDef()

        for func in API.__dict__.values():
            if hasattr(func, "__route__"):
                self.routes.route(*func.__route__)(partial(func, self))

        self.app.add_routes(self.routes)

    async def cog_load(self):
        self.bot.loop.create_task(self.start())

    async def start(self) -> None:
        await self.bot.wait_until_ready()

        await self.runner.setup()
        site = web.TCPSite(self.runner, "0.0.0.0", 8080)
        await site.start()

    async def cog_unload(self) -> None:
        await self.app.shutdown()
        await self.runner.cleanup()

    @route(hdrs.METH_GET, "/")
    async def test(self, request: web.Request):
        return web.Response(text="Hello World!")


async def setup(bot: MyBot):
    await bot.add_cog(API(bot))