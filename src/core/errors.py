from __future__ import annotations

from typing import TYPE_CHECKING, Any, Iterable

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


class UnexpectedError(Exception):
    """Only raised on place where it shouldn't have exceptions."""

    def __init__(self, *args: Any) -> None:
        super().__init__(*args)


class MiscCommandException(Exception):
    pass


class CheckFail(MiscCommandException):
    pass


class NoPrivateMessage(MiscCommandException):
    pass


class MixinException(MiscCommandException, errors.AppCommandError):
    pass


class BotMissingPermissions(MixinException):
    def __init__(self, perms: Iterable[str]) -> None:
        self.missing_perms = set(perms)
        super().__init__(f"Bot is missing the following permissions: {', '.join(perms)}")


class BadArgument(BaseError):
    pass
