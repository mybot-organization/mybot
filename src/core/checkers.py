from __future__ import annotations

import asyncio
import logging
from collections import deque
from typing import TYPE_CHECKING, Any, Callable, Deque, Hashable, TypeVar, Union

import discord
from discord.app_commands import Command, ContextMenu
from typing_extensions import Self

from .errors import BotMissingPermissions, MaxConcurrencyReached
from .misc_command import MiscCommand, MiscCommandContext, misc_check as misc_check

T = TypeVar("T")

logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from discord import Interaction

    from ._types import CoroT

    MaxConcurrencyFunction = Union[Callable[[Interaction], CoroT[T]], Callable[[Interaction], T]]


class MaxConcurrency:
    __slots__ = ("rate", "key", "wait", "_mapping")

    def __init__(self, rate: int, *, key: MaxConcurrencyFunction[Hashable], wait: bool) -> None:
        self._mapping: dict[Any, _Semaphore] = {}
        self.key: MaxConcurrencyFunction[Hashable] = key
        self.rate: int = rate
        self.wait: bool = wait

        if rate <= 0:
            raise ValueError("max_concurrency 'number' cannot be less than 1")

    def copy(self) -> Self:
        return self.__class__(self.rate, key=self.key, wait=self.wait)

    def __repr__(self) -> str:
        return f"<MaxConcurrency key={self.key!r} rate={self.rate} wait={self.wait}>"

    def get_key(self, inter: Interaction) -> Any:
        return self.key(inter)

    async def acquire(self, inter: Interaction) -> None:
        key = self.get_key(inter)

        try:
            sem = self._mapping[key]
        except KeyError:
            self._mapping[key] = sem = _Semaphore(self.rate)

        acquired = await sem.acquire(wait=self.wait)
        if not acquired:
            raise MaxConcurrencyReached(self.rate, inter.command)

    async def release(self, inter: Interaction) -> None:
        # Technically there's no reason for this function to be async
        # But it might be more useful in the future
        key = self.get_key(inter)

        try:
            sem = self._mapping[key]
        except KeyError:
            # ...? peculiar
            return
        else:
            sem.release()

        if sem.value >= self.rate and not sem.is_active():
            del self._mapping[key]


class _Semaphore:
    """This class is a version of a semaphore.

    If you're wondering why asyncio.Semaphore isn't being used,
    it's because it doesn't expose the internal value. This internal
    value is necessary because I need to support both `wait=True` and
    `wait=False`.

    An asyncio.Queue could have been used to do this as well -- but it is
    not as inefficient since internally that uses two queues and is a bit
    overkill for what is basically a counter.
    """

    __slots__ = ("value", "loop", "_waiters")

    def __init__(self, number: int) -> None:
        self.value: int = number
        self.loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()
        self._waiters: Deque[asyncio.Future[Any]] = deque()

    def __repr__(self) -> str:
        return f"<_Semaphore value={self.value} waiters={len(self._waiters)}>"

    def locked(self) -> bool:
        return self.value == 0

    def is_active(self) -> bool:
        return len(self._waiters) > 0

    def wake_up(self) -> None:
        while self._waiters:
            future = self._waiters.popleft()
            if not future.done():
                future.set_result(None)
                return

    async def acquire(self, *, wait: bool = False) -> bool:
        if not wait and self.value <= 0:
            # signal that we're not acquiring
            return False

        while self.value <= 0:
            future = self.loop.create_future()
            self._waiters.append(future)
            try:
                await future
            except Exception:
                future.cancel()
                if self.value > 0 and not future.cancelled():
                    self.wake_up()
                raise

        self.value -= 1
        return True

    def release(self) -> None:
        self.value += 1
        self.wake_up()


def bot_required_permissions(**perms: bool) -> Any:
    invalid = set(perms) - set(discord.Permissions.VALID_FLAGS)
    if invalid:
        raise TypeError(f"Invalid permission(s): {', '.join(invalid)}")

    def compare_permissions(permissions: discord.Permissions) -> bool:
        missing = [perm for perm, value in perms.items() if getattr(permissions, perm) != value]

        if not missing:
            return True

        raise BotMissingPermissions(missing)

    def app_cmd_predicate(inter: Interaction) -> bool:
        permissions = inter.app_permissions
        return compare_permissions(permissions)

    def misc_cmd_predicate(ctx: MiscCommandContext) -> bool:
        return compare_permissions(ctx.bot_permissions)

    def decorator(func: T) -> T:
        if isinstance(func, (Command, ContextMenu)):
            func.extras["bot_required_permissions"] = [perm for perm, value in perms.items() if value is True]
            func.add_check(app_cmd_predicate)
        elif hasattr(func, "__listener_as_command__"):
            misc_command: MiscCommand = getattr(func, "__listener_as_command__")
            misc_command.extras["bot_required_permissions"] = [perm for perm, value in perms.items() if value is True]
            misc_command.add_check(misc_cmd_predicate)
        else:
            logger.critical(f"bot_required_permissions needs to be used before the command decorator ({func}).")
        return func  # type: ignore

    return decorator


async def is_user_authorized(context: MiscCommandContext) -> bool:
    # TODO: check using the database if the user is authorized
    return True


async def is_activated(context: MiscCommandContext) -> bool:
    # TODO: check using the database if the misc command is activated
    return True