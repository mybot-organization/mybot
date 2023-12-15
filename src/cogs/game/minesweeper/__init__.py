# TODO ? : add a way to play by reply to the message.

from __future__ import annotations

import logging
from string import ascii_uppercase
from typing import TYPE_CHECKING, Self

import discord
from discord import ui

from core import ExtendedCog, ResponseType, response_constructor

from .minesweeper_game import Minesweeper, MinesweeperConfig, PlayType

if TYPE_CHECKING:
    from discord import Interaction


logger = logging.getLogger(__name__)

corner = " "
row_denominators = ["⒈", "⒉", "⒊", "⒋", "⒌", "⒍", "⒎", "⒏", "⒐", "⒑", "⒒", "⒓", "⒔", "⒕", "⒖", "⒗", "⒘", "⒙", "⒚", "⒛"]
column_denominators = ascii_uppercase

board_size = (20, 13)


def build_board_display(game: Minesweeper) -> str:
    description = "```" + corner + " " * 3 + " ".join(column_denominators[i] for i in range(0, game.size[1])) + "\n"

    display_chars = {
        0: " ",
        -1: "X",
    }
    display_chars.update({i: str(i) for i in range(1, 10)})
    flag_char = "?"
    unrevealed_char = "■"

    def get_char(row: int, column: int) -> str:
        if (row, column) in game.flags:
            return flag_char
        if (row, column) in game.revealed:
            return display_chars[game.board[row][column]]

        return unrevealed_char

    for row in range(0, game.size[0]):
        description += row_denominators[row] + " |"
        for column in range(0, game.size[1]):
            description += " " + get_char(row, column)
        description += "\n"
    description += "```"

    return description


class MinesweeperCog(ExtendedCog, name="minesweeper"):
    async def minesweeper(self, inter: Interaction) -> None:
        embed = response_constructor(ResponseType.info, "Minesweeper").embed
        game = Minesweeper(board_size, 0)  # only used for the view, will be regenerated within the first play
        embed.description = build_board_display(game)

        embed.add_field(name="Time", value=f"<t:{int(inter.created_at.timestamp())}:R>")

        view = MinesweeperView(embed)
        await inter.response.send_message(embed=embed, view=view)


class MinesweeperView(ui.View):
    def __init__(self, game_embed: discord.Embed):
        super().__init__(timeout=180)
        self.game: Minesweeper | None = None
        self.game_embed = game_embed

        self.row.options = [
            discord.SelectOption(label=row_denominators[i], value=str(i)) for i in range(0, board_size[0])
        ]
        self.column.options = [
            discord.SelectOption(label=column_denominators[i], value=str(i)) for i in range(0, board_size[1])
        ]

    def check_playable(self) -> None:
        if self.row.values != [] and self.column.values != []:
            self.play.disabled = False

    @ui.select(
        cls=ui.Select,
        placeholder="Select the row",
        options=[],
    )
    async def row(self, inter: Interaction, value: ui.Select[Self]) -> None:
        for i, option in enumerate(self.row.options):
            option.default = i == int(value.values[0])
        self.check_playable()
        await inter.response.edit_message(view=self)

    @ui.select(
        cls=ui.Select,
        placeholder="Select the column",
        options=[],
    )
    async def column(self, inter: Interaction, value: ui.Select[Self]) -> None:
        for i, option in enumerate(self.column.options):
            option.default = i == int(value.values[0])
        self.check_playable()
        await inter.response.edit_message(view=self)

    @ui.button(label="Play", style=discord.ButtonStyle.green, disabled=True)
    async def play(self, inter: Interaction, button: ui.Button[Self]) -> None:
        x, y = int(self.row.values[0]), int(self.column.values[0])
        if self.game is None:
            conf = MinesweeperConfig(height=board_size[0], width=board_size[1], number_of_mines=50, initial_play=(x, y))
            self.game = Minesweeper.from_config(conf)
            self.flag.disabled = False
        else:
            play = self.game.play(x, y)
            print(play)
            if play.type == PlayType.BOMB_EXPLODED:
                print("bomb exploded")
                self.clear_items()

        self.game_embed.description = build_board_display(self.game)
        await inter.response.edit_message(embed=self.game_embed, view=self)

    @ui.button(label="Flag", style=discord.ButtonStyle.blurple, disabled=True)
    async def flag(self, inter: Interaction, button: ui.Button[Self]) -> None:
        if TYPE_CHECKING:
            assert self.game is not None

        x, y = int(self.row.values[0]), int(self.column.values[0])
        self.game.add_flag(x, y)

        self.game_embed.description = build_board_display(self.game)
        await inter.response.edit_message(embed=self.game_embed)
