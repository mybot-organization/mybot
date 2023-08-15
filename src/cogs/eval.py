from __future__ import annotations

import ast
import logging
import re
import traceback
from functools import partial
from io import StringIO
from typing import TYPE_CHECKING, Any, Self

import discord
from discord import ButtonStyle, Color, Embed, Message, TextStyle, app_commands, ui
from discord.ext import commands
from discord.ext.commands import Cog  # pyright: ignore[reportMissingTypeStubs]
from discord.interactions import Interaction

from core._config import config
from core.checkers.app import is_me
from core.checkers.base import is_me_bool
from core.utils import size_text

if TYPE_CHECKING:
    from discord import Interaction

    from mybot import MyBot


logger = logging.getLogger(__name__)


class Eval(Cog):
    def __init__(self, bot: MyBot):
        self.bot: MyBot = bot

    @commands.command(name="+eval")
    @commands.check(lambda ctx: is_me_bool(ctx.author.id))
    async def add_eval(self, ctx: commands.Context[MyBot]) -> None:
        try:
            self.bot.tree.add_command(self._eval, guild=ctx.guild)
        except app_commands.CommandAlreadyRegistered:
            await ctx.send("Command already registered.")
        else:
            async with ctx.typing():
                await self.bot.tree.sync(guild=ctx.guild)
                await ctx.send("Command added.")

    @commands.command(name="-eval")
    @commands.check(lambda ctx: is_me_bool(ctx.author.id))
    async def remove_eval(self, ctx: commands.Context[MyBot]) -> None:
        if self.bot.tree.remove_command("eval", guild=ctx.guild) is None:
            await ctx.send("Command not registered. Cleaning eventual leftovers...")
        async with ctx.typing():
            await self.bot.tree.sync(guild=ctx.guild)
            await ctx.send("Command removed.")

    @app_commands.command(
        name="eval",
        description="Evaluate python code.",
    )
    @app_commands.guilds()
    @is_me
    async def _eval(self, inter: Interaction, ephemeral: bool = True) -> None:
        await inter.response.send_modal(EvalForm(self.bot, ephemeral=ephemeral, message=inter.message))


class EvalForm(ui.Modal):
    def __init__(self, bot: MyBot, default: str | None = None, ephemeral: bool = False, message: Message | None = None):
        super().__init__(title="Code evaluation")

        self.code = ui.TextInput[Self](
            label="Code", style=TextStyle.long, placeholder='print("hello world")', default=default
        )
        self.add_item(self.code)

        self.bot = bot
        self.message = message
        self.ephemeral = ephemeral

    async def on_submit(self, inter: Interaction) -> None:
        embeds: list[Embed] = []

        def set_embeds_color(color: Color) -> None:
            for embed in embeds:
                embed.color = color

        code = clean_code(str(self.code))
        embed = Embed(
            title="Code evaluation:", description=f'```py\n{size_text(code, size=1900, mode="end")}\n```\t\t\t\t\u200b'
        )
        embed.set_author(name="Input:")
        embeds.append(embed)

        embed = Embed(description="```Evaluating...```")
        embed.set_author(name="Output:")
        embeds.append(embed)

        set_embeds_color(Color.greyple())

        if self.message is not None:
            strategy = inter.response.edit_message
        else:
            strategy = partial(inter.response.send_message, ephemeral=self.ephemeral)

        await strategy(embeds=embeds, view=EvalView(self.bot, code))
        result, errored = await code_evaluation(str(self.code), inter, self.bot)
        embeds[1].description = f"```py\n{size_text(result, 4000, 'middle')}\n```"
        if errored:
            set_embeds_color(Color.red())
        else:
            set_embeds_color(Color.green())

        await inter.edit_original_response(embeds=embeds)


class EvalView(ui.View):
    def __init__(self, bot: MyBot, cached_code: str) -> None:
        super().__init__(timeout=None)

        self.cached_code = cached_code
        self.bot = bot

    @ui.button(label="Edit", style=ButtonStyle.blurple)
    async def edit(self, inter: Interaction, button: ui.Button[Self]) -> None:
        del button  # unused
        await inter.response.send_modal(EvalForm(self.bot, default=self.cached_code, message=inter.message))

    @ui.button(label="Delete", style=ButtonStyle.red)
    async def delete(self, inter: Interaction, button: ui.Button[Self]) -> None:
        del button  # unused
        await inter.response.defer()
        await inter.delete_original_response()


def clean_code(code: str) -> str:
    code = re.sub(r"```(?:py\n)?|(?:```$)", r"", code)
    return code.strip()


def insert_returns(body: Any) -> Any:
    # insert return stmt if the last expression is a expression statement
    if isinstance(body[-1], ast.Expr):
        body[-1] = ast.Return(body[-1].value)
        ast.fix_missing_locations(body[-1])

    # for if statements, we insert returns into the body and the or else
    if isinstance(body[-1], ast.If):
        insert_returns(body[-1].body)
        insert_returns(body[-1].orelse)

    # for with blocks, again we insert returns into the body
    if isinstance(body[-1], ast.With):
        insert_returns(body[-1].body)


async def code_evaluation(code: str, inter: Interaction, bot: MyBot) -> tuple[str, bool]:
    args = "\n".join([f"    {li}" for li in code.splitlines()])
    # fmt: off
    str_body = (
        "async def _eval():\n"
        f"{args}\n"
    )
    # fmt: on

    stdout_buffer = StringIO()

    env: dict[str, Any] = {
        "bot": bot,
        "discord": discord,
        "commands": commands,
        "app_commands": app_commands,
        "ui": ui,
        "inter": inter,
        "__import__": __import__,
        "config": config,
        "print": partial(print, file=stdout_buffer),
    }

    try:
        parsed: Any = ast.parse(str_body)
        body: Any = parsed.body[0].body
        insert_returns(body)

        exec(compile(parsed, "<ast>", "exec"), env)
        output: Any = await eval("_eval()", env)
    except Exception as error:
        error = traceback.format_exc()
        return error, True

    stdout_buffer.seek(0)
    std_output = stdout_buffer.read()

    if std_output:
        output = std_output

    return str(output), False


async def setup(bot: MyBot) -> None:
    await bot.add_cog(Eval(bot))
