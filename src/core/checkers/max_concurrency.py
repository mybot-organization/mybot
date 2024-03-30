from __future__ import annotations

import asyncio
import logging
from collections import deque
from collections.abc import Callable, Hashable
from typing import TYPE_CHECKING, Any, Self, TypeVar

from ..errors import MaxConcurrencyReached

T = TypeVar("T")


logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from discord import Interaction

    from .._types import CoroT

    MaxConcurrencyFunction = Callable[[Interaction], CoroT[T]] | Callable[[Interaction], T]


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
        self._waiters: deque[asyncio.Future[Any]] = deque()

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
