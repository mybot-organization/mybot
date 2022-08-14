from __future__ import annotations

from typing import TYPE_CHECKING, Any

from discord.app_commands import errors

if TYPE_CHECKING:
    from discord.app_commands import Command, ContextMenu


class BaseError(errors.AppCommandError):
    """
    The base error used for non-specific errors.
    """


class MaxConcurrencyReached(errors.AppCommandError):
    """
    Raised when max concurrency is reached.
    """

    def __init__(self, rate: int, command: Command[Any, (...), Any] | ContextMenu | None) -> None:
        self.rate: int = rate
        self.command: Command[Any, (...), Any] | ContextMenu | None = command
        name = command.name if command is not None else "unknown"
        super().__init__(f'Max concurrency reached for the command "{name}" (rate: {rate})')
