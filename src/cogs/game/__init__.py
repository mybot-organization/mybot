from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from discord import app_commands
from discord.app_commands import locale_str as __

from core import SpecialGroupCog, cog_property
from core.i18n import _

from .connect4 import GameConnect4
from .minesweeper import MinesweeperCog
from .rpc import GameRPC
from .tictactoe import GameTictactoe

if TYPE_CHECKING:
    from discord import Interaction

    from mybot import MyBot


logger = logging.getLogger(__name__)


# Subcommands cannot be seperated in multiple files.
# https://github.com/Rapptz/discord.py/discussions/8069
# So all commands are defined here, and their implementation are in other files.


class Game(SpecialGroupCog["MyBot"], group_name=__("game"), group_description=__("Play some games.")):
    @cog_property("game_connect4")
    def connect4_cog(self) -> GameConnect4:
        ...

    @cog_property("game_rpc")
    def rpc_cog(self) -> GameRPC:
        ...

    @cog_property("game_tictactoe")
    def tictactoe_cog(self) -> GameTictactoe:
        ...

    @cog_property("minesweeper")
    def minesweeper_cog(self) -> MinesweeperCog:
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

    @app_commands.command(
        name=__("minesweeper"),
        description=__("Play minesweeper"),
        extras={"soon": True},
    )
    async def minesweeper(self, inter: Interaction) -> None:
        await self.minesweeper_cog.minesweeper(inter)


async def setup(bot: MyBot) -> None:
    await bot.add_cog(GameTictactoe(bot))
    await bot.add_cog(GameRPC(bot))
    await bot.add_cog(GameConnect4(bot))
    await bot.add_cog(MinesweeperCog(bot))

    await bot.add_cog(Game(bot))
