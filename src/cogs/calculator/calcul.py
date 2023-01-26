"""
This is a complete program to simulate a calculator in python.
It is fully based on regex. So no security issues.
But could be improved.
"""

import decimal
import operator as op
import re
from collections.abc import Sequence
from math import pi
from typing import Callable

Decimal = decimal.Decimal


def regex_builder(sign: str) -> re.Pattern[str]:
    pattern = (
        r"((?:[-+]?\d*\.?\d+)(?:[eE](?:[-+]?\d+))?) *" + "\\" + sign + r" *((?:[-+]?\d*\.?\d+)(?:[eE](?:[-+]?\d+))?)"
    )
    return re.compile(pattern)


re_parentheses = re.compile(r"\((.*?)\)")

addition = (regex_builder("+"), op.add)
subtraction = (regex_builder("-"), op.sub)
division = (regex_builder("/"), op.truediv)
multiplication = (regex_builder("*"), op.mul)
power = (regex_builder("^"), op.pow)


class UnclosedParentheses(Exception):
    ...


class Calcul:
    """
    Hmm... Comments seems important here.
    """

    def __init__(self) -> None:
        self._expression: str = "0"
        self._answer: str = "0"
        self.just_calculated: bool = False
        self.new: bool = True

    @property
    def expr(self) -> str:
        return self._expression

    @expr.setter
    def expr(self, value: str) -> None:
        self.just_calculated = False
        self._expression = value

    @property
    def answer(self) -> str:
        return self._answer

    @answer.setter
    def answer(self, value: str) -> None:
        self.just_calculated = True
        self._answer = value

    def reset_expr(self) -> None:
        self.new = True
        self._expression = "0"

    @staticmethod
    def operator_process(calcul: str, pattern: re.Pattern[str], operator_method: Callable[[Decimal, Decimal], Decimal]):
        while result := pattern.search(calcul):
            operation_result = operator_method(Decimal(result.group(1)), Decimal(result.group(2))).normalize()
            calcul = pattern.sub(str(operation_result), calcul, 1)
        return calcul

    @staticmethod
    def multiple_operators_process(
        calcul: str,
        patterns: Sequence[re.Pattern[str]],
        operator_methods: Sequence[Callable[[Decimal, Decimal], Decimal]],
    ):
        def sort_key(y: re.Match[str]) -> int:
            return y.start(2)

        results: list[re.Match[str]]
        while results := sorted((x for pattern in patterns if (x := pattern.search(calcul))), key=sort_key):
            result = results[0]

            operator_method = operator_methods[patterns.index(result.re)]
            operation_result = operator_method(Decimal(result.group(1)), Decimal(result.group(2))).normalize()

            calcul = result.re.sub(str(operation_result), calcul, 1)
        return calcul

    @staticmethod
    def string_process(calcul: str) -> str:
        decimal.getcontext().prec = 10

        if calcul.count("(") != calcul.count(")"):
            raise UnclosedParentheses()
        while match := re.search(r"([)\d])(\()", calcul):
            calcul = match.re.sub(r"\1 * \2", calcul)
        while match := re.search(r"(\))(\d)", calcul):
            calcul = match.re.sub(r"\1 * \2", calcul)

        while result := re_parentheses.search(calcul):
            operation_result = Calcul.string_process(result.group(1))
            calcul = re_parentheses.sub(str(operation_result), calcul, 1)

        calcul = Calcul.operator_process(calcul, *power)

        calcul = Calcul.multiple_operators_process(calcul, *zip(multiplication, division))  # type: ignore (zip typing issue)
        calcul = Calcul.multiple_operators_process(calcul, *zip(addition, subtraction))  # type: ignore (zip typing issue)

        return calcul

    def process(self) -> None:
        expression = self.expr
        expression = expression.replace("π", "(" + str(pi) + ")")
        expression = expression.replace("Ans", "(" + str(self.answer) + ")")
        result = self.string_process(expression)
        result = decimal.Decimal(result).normalize()  # Check if the result is correct, if not, raise errors.
        self.answer = str(result)


if __name__ == "__main__":
    calcul = Calcul()
    print(Calcul.string_process("1+2+3+4+5+6+7+8+9+10"))
