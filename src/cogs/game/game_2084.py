# TODO : show score
# TODO : create game save
# TODO : handle game over

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Self, TypedDict

import discord
from discord import ui
from two048 import Direction, Tile, Two048

from core import ExtendedCog, ResponseType, response_constructor
from core.constants import Emojis

if TYPE_CHECKING:
    from discord import Interaction


logger = logging.getLogger(__name__)


class ResponseT(TypedDict):
    view: Two048View
    content: str


tile_value_to_emoji = {
    0: Emojis.two048_empty,
    2: Emojis.two048_2,
    4: Emojis.two048_4,
    8: Emojis.two048_8,
    16: Emojis.two048_16,
    32: Emojis.two048_32,
    64: Emojis.two048_64,
    128: Emojis.two048_128,
    256: Emojis.two048_256,
    512: Emojis.two048_512,
    1024: Emojis.two048_1024,
    2048: Emojis.two048_2048,
    4096: Emojis.two048_4096,
    8192: Emojis.two048_8192,
}


class Two048Cog(ExtendedCog, name="game_2048"):
    async def two048(self, inter: Interaction) -> None:
        await inter.response.send_message(**Two048View.init_game(inter.user))


class Two048View(ui.View):
    def __init__(self, game: Two048, user: discord.User | discord.Member):
        super().__init__()
        self.game = game
        self.user = user

    @classmethod
    def init_game(cls, user: discord.User | discord.Member) -> ResponseT:
        view = cls(Two048(), user)

        content = cls.str_board(view.game.board)

        return {"view": view, "content": content}

    @staticmethod
    def str_board(board: list[list[Tile]]) -> str:
        return "\n".join("".join(tile_value_to_emoji[t.value] for t in row) for row in board)

    async def interaction_check(self, interaction: Interaction, /) -> bool:
        if interaction.user != self.user:
            await interaction.response.send_message(
                **response_constructor(ResponseType.error, "You are not the owner of this game.")
            )
            return False
        return True

    async def play(self, inter: Interaction, direction: Direction) -> None:
        self.game.play(direction)

        await inter.response.edit_message(view=self, content=self.str_board(self.game.board))

    @ui.button(emoji=Emojis.left_arrow, style=discord.ButtonStyle.blurple)
    async def left(self, inter: Interaction, button: ui.Button[Self]) -> None:
        del button  # unused
        await self.play(inter, Direction.LEFT)

    @ui.button(emoji=Emojis.down_arrow, style=discord.ButtonStyle.blurple)
    async def down(self, inter: Interaction, button: ui.Button[Self]) -> None:
        del button  # unused
        await self.play(inter, Direction.DOWN)

    @ui.button(emoji=Emojis.up_arrow, style=discord.ButtonStyle.blurple)
    async def up(self, inter: Interaction, button: ui.Button[Self]) -> None:
        del button  # unused
        await self.play(inter, Direction.UP)

    @ui.button(emoji=Emojis.right_arrow, style=discord.ButtonStyle.blurple)
    async def right(self, inter: Interaction, button: ui.Button[Self]) -> None:
        del button  # unused
        await self.play(inter, Direction.RIGHT)
