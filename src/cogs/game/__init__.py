from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from discord import app_commands
from discord.app_commands import locale_str as __
from discord.ext.commands import GroupCog  # pyright: ignore[reportMissingTypeStubs]

from core import cog_property
from core.i18n import _

if TYPE_CHECKING:
    from discord import Interaction

    from mybot import MyBot

    from .connect4 import GameConnect4
    from .rpc import GameRPC
    from .tictactoe import GameTictactoe


logger = logging.getLogger(__name__)


# Subcommands cannot be seperated in multiple files.
# https://github.com/Rapptz/discord.py/discussions/8069
# So all commands are defined here, and their implementation are in other files.


class Game(GroupCog, group_name=__("game"), group_description=__("Play some games.")):
    def __init__(self, bot: MyBot) -> None:
        self.bot = bot

    @cog_property("game_connect4")
    def connect4_cog(self) -> GameConnect4:
        ...

    @cog_property("game_rpc")
    def rpc_cog(self) -> GameRPC:
        ...

    @cog_property("game_tictactoe")
    def tictactoe_cog(self) -> GameTictactoe:
        ...

    @app_commands.command(
        name=__("connect4"),
        description=__("Play connect 4"),
        extras={"soon": True},
    )
    async def connect4(self, inter: Interaction) -> None:
        await self.connect4_cog.connect4(inter)

    @app_commands.command(
        name=__("rpc"),
        description=__("Play rock paper cisors"),
        extras={"soon": True},
    )
    async def rpc(self, inter: Interaction) -> None:
        await self.rpc_cog.rpc(inter)

    @app_commands.command(
        name=__("tictactoe"),
        description=__("Play tictactoe"),
        extras={"soon": True},
    )
    async def tictactoe(self, inter: Interaction) -> None:
        await self.tictactoe_cog.tictactoe(inter)


async def setup(bot: MyBot) -> None:
    from .connect4 import GameConnect4
    from .rpc import GameRPC
    from .tictactoe import GameTictactoe

    await bot.add_cog(GameTictactoe(bot))
    await bot.add_cog(GameRPC(bot))
    await bot.add_cog(GameConnect4(bot))

    await bot.add_cog(Game(bot))
