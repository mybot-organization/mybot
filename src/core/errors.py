from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any
from collections.abc import Iterable

from discord.app_commands import errors

if TYPE_CHECKING:
    from discord.app_commands import Command, ContextMenu


logger = logging.getLogger(__name__)


# INTERACTIONS RELATED ERRORS


class BadArgument(errors.AppCommandError):
    pass


class MaxConcurrencyReached(errors.AppCommandError):
    """
    Raised when max concurrency is reached.
    """

    def __init__(self, rate: int, command: Command[Any, (...), Any] | ContextMenu | None) -> None:
        self.rate: int = rate
        self.command: Command[Any, (...), Any] | ContextMenu | None = command
        name = command.name if command is not None else "unknown"
        super().__init__(f'Max concurrency reached for the command "{name}" (rate: {rate})')


class BotUserNotPresent(errors.AppCommandError):
    pass


# MISC COMMANDS RELATED ERRORS


class MiscCommandError(Exception):
    pass


class MiscCheckFailure(MiscCommandError):
    pass


class MiscNoPrivateMessage(MiscCommandError):
    pass


# MIXED ERRORS


class MixedError(MiscCommandError, errors.AppCommandError):
    pass


class NonSpecificError(MixedError):
    """
    The base error used for non-specific errors.
    """


class BotMissingPermissions(MixedError):
    def __init__(self, perms: Iterable[str]) -> None:
        self.missing_perms = set(perms)
        super().__init__(f"Bot is missing the following permissions: {", ".join(perms)}")


class NotAllowedUser(MixedError):
    def __init__(self, user_id: int) -> None:
        self.user_id = user_id
        super().__init__(f"User with id {user_id} is not allowed to use this command.")


# OTHER ERRORS


class UnexpectedError(Exception):
    """Only raised on place where it shouldn't have exceptions."""

    def __init__(self, *args: Any) -> None:
        logger.error("An unexpected error has occurred. Should not happen.", exc_info=self)
        super().__init__(*args)
