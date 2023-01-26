# TODO : use an autocompleter for the initial expression


from __future__ import annotations

import decimal
import logging
from functools import partial
from typing import TYPE_CHECKING, Self

import discord
from discord import ButtonStyle, app_commands, ui
from discord.app_commands import locale_str as __

from core import SpecialCog
from core.i18n import _

from .calcul import Calcul, UnclosedParentheses

if TYPE_CHECKING:
    from discord import Interaction

    from mybot import MyBot


logger = logging.getLogger(__name__)


def display_calcul(calcul: Calcul) -> str:
    if calcul.just_calculated:
        display = f"> ```py\n" f"> {calcul.expr} =\n" f"> {calcul.answer: <41}\n" f"> ```"
        calcul.expr = calcul.answer
        calcul.new = True
    else:
        display = f"> ```py\n" f"> Ans = {calcul.answer}\n" f"> {calcul.expr: <41}\n" f"> ```"
    return display


class Calculator(SpecialCog["MyBot"]):
    class CalculatorView(ui.View):
        def __init__(self, parent: Calculator, inter: Interaction, calcul: Calcul):
            super().__init__(timeout=600)
            self.parent: Calculator = parent
            self.inter: Interaction = inter
            self.calcul: Calcul = calcul

            buttons = [
                (ButtonStyle.primary, "xᶤ", " ^ "),
                (ButtonStyle.primary, "x²", "pow2"),
                (ButtonStyle.primary, "AC", "clear"),
                (ButtonStyle.primary, "⌫", "delete"),
                (ButtonStyle.danger, "/", " / "),
                (ButtonStyle.primary, "(", "("),
                (ButtonStyle.secondary, "7", "7"),
                (ButtonStyle.secondary, "8", "8"),
                (ButtonStyle.secondary, "9", "9"),
                (ButtonStyle.danger, "x", " * "),
                (ButtonStyle.primary, ")", ")"),
                (ButtonStyle.secondary, "4", "4"),
                (ButtonStyle.secondary, "5", "5"),
                (ButtonStyle.secondary, "6", "6"),
                (ButtonStyle.danger, "-", " - "),
                (ButtonStyle.primary, "π", "π"),
                (ButtonStyle.secondary, "1", "1"),
                (ButtonStyle.secondary, "2", "2"),
                (ButtonStyle.secondary, "3", "3"),
                (ButtonStyle.danger, "+", " + "),
                (ButtonStyle.primary, "Ans", "Ans"),
                (ButtonStyle.secondary, "⁺∕₋", "opposite"),
                (ButtonStyle.secondary, "0", "0"),
                (ButtonStyle.secondary, ",", "."),
                (ButtonStyle.success, "=", "result"),
            ]
            for style, label, custom_id in buttons:
                button: ui.Button[Self] = ui.Button(style=style, label=label, custom_id=custom_id)
                button.callback = partial(self.compute, button)
                self.add_item(button)

        async def on_timeout(self) -> None:
            item: ui.Button[Self]
            for item in self.children:  # type: ignore
                item.disabled = True
            message = await self.inter.original_response()
            await message.edit(view=self)

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            passed: bool = interaction.user.id == self.inter.user.id

            if not passed:  # TODO : error style
                await interaction.response.send_message(
                    content="Vous ne pouvez pas interagir sur une calculatrice de quelqu'un d'autre, faites vous-même la commande !",
                    ephemeral=True,
                )

            return passed

        async def compute(self, button: ui.Button[Self], interaction: discord.Interaction):
            print(self, button, interaction)
            calcul = self.calcul
            selection = button.custom_id

            numbers = ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9")
            operators = (" / ", " + ", " * ", " - ", " ^ ")

            avertissements: list[str] = []

            if selection in numbers + ("π", "Ans"):
                if calcul.new:
                    calcul.expr = ""
                    calcul.new = False
                calcul.expr += selection

            elif selection == ".":
                if calcul.new:
                    calcul.expr = ""
                    calcul.new = False
                if any(calcul.expr.endswith(nb) for nb in numbers + (".",)):
                    if "." not in calcul.expr.split(" ")[-1]:
                        calcul.expr += "."
                else:
                    calcul.expr += "0."

            elif selection in operators:
                calcul.new = False
                if any(calcul.expr.endswith(sign) for sign in operators):
                    calcul.expr = calcul.expr[:-3] + selection
                else:
                    if selection == " - " and calcul.expr.endswith("("):
                        calcul.expr += "0 - "
                    else:
                        calcul.expr += selection

            elif selection == "(":
                if calcul.new:
                    calcul.expr = ""
                    calcul.new = False
                calcul.expr += selection

            elif selection == ")":
                if calcul.expr.count("(") > calcul.expr.count(")"):
                    if calcul.expr.endswith("("):
                        calcul.expr += "0)"
                    else:
                        calcul.expr += ")"

            elif selection == "pow2":
                calcul.new = False
                if any(calcul.expr.endswith(sign) for sign in operators):
                    calcul.expr = calcul.expr[:-3] + " ^ 2"
                else:
                    calcul.expr += " ^ 2"

            elif selection == "opposite":
                if calcul.expr in ("π", "Ans"):
                    calcul.expr = "-" + calcul.expr
                elif calcul.expr in ("-π", "-Ans"):
                    calcul.expr = calcul.expr[1:]
                else:
                    try:
                        result = decimal.Decimal(calcul.expr)
                    except (ValueError, decimal.FloatOperation, decimal.InvalidOperation):
                        avertissements.append("L'expression doit être un simple nombre.")
                    else:
                        calcul.expr = str(-result)

            elif selection == "result":
                try:
                    calcul.process()
                except decimal.InvalidOperation as error:
                    print(error)
                    avertissements.append("Quelque chose cloche avec votre calcul, vérifiez la syntax.")
                except ZeroDivisionError:
                    avertissements.append("Vous ne pouvez pas diviser par 0.")
                except UnclosedParentheses:
                    avertissements.append("Vous n'avez pas fermé certaines parenthèses.")
                except decimal.Overflow:
                    avertissements.append("On dirait que le résultat est vraiment gros. Trop gros...")

            elif selection == "clear":
                calcul.reset_expr()

            elif selection == "delete":
                if any(calcul.expr.endswith(sign) for sign in operators):
                    calcul.expr = calcul.expr[:-3]
                else:
                    calcul.expr = calcul.expr[:-1]

                if not calcul.expr:
                    calcul.reset_expr()

            if avertissements:
                await interaction.response.send_message(ephemeral=True, content="\n".join(avertissements))
            else:
                await interaction.response.edit_message(content=display_calcul(calcul))

    @app_commands.command(
        name=__("calculator"),
        description=__("Show a calculator you can use."),
        extras={"soon": True},
    )
    async def calculator(self, inter: Interaction, initial_expression: str | None) -> None:
        calcul = Calcul()

        if initial_expression:
            try:
                calcul.expr = initial_expression
                calcul.process()
            except Exception:
                calcul.reset_expr()

        view = self.CalculatorView(self, inter, calcul)
        await inter.response.send_message(content=display_calcul(calcul), view=view)

    @calculator.autocomplete("initial_expression")
    async def calculator_direct_autocomplete(self, inter: Interaction, current: str) -> list[app_commands.Choice[str]]:
        """
        An autocompleter to show the result of the current expression while typing it.
        """
        try:
            result = Calcul.string_process(current)
        except Exception:
            return [app_commands.Choice(name=__("Invalid expression"), value=current)]
        else:
            return [
                app_commands.Choice(name=result, value=current),
            ]


async def setup(bot: MyBot):
    await bot.add_cog(Calculator(bot))
