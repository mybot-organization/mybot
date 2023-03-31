from collections import OrderedDict
from collections.abc import Mapping
from datetime import datetime, timedelta
from functools import wraps
from typing import (
    Any,
    Callable,
    Concatenate,
    Generic,
    Iterator,
    MutableMapping,
    NamedTuple,
    ParamSpec,
    Sequence,
    TypeVar,
)

_K = TypeVar("_K")  # Type for Keys
_V = TypeVar("_V")  # Type for Values
_RT = TypeVar("_RT")  # Type for Return Type
_ST = TypeVar("_ST", bound="TemporaryCache[Any, Any]")  # Type for Self
_P = ParamSpec("_P")  # Type for Args

T = TypeVar("T")  # Type for Generic


class TemporaryCache(Mapping[_K, _V]):
    """Create a temporary cache working like python's dict.
    Every time the cache is accessed / modified, it will be cleaned.

    It implements the Mapping ABC, so it can be used like a dict.
    __contains__, keys, items, values, get, setdefault, __eq__, __ne__ are well defined.

    get is also a cleaner, because it call __getitem__.
    """

    @staticmethod
    def as_cleaner(func: Callable[Concatenate[_ST, _P], _RT]) -> Callable[Concatenate[_ST, _P], _RT]:
        """A decorator to tell that a method should clean the cache before executing."""

        @wraps(func)
        def inner(self: _ST, *args: _P.args, **kwargs: _P.kwargs) -> _RT:
            self.clean()
            return func(self, *args, **kwargs)

        return inner

    def __init__(self, expire: timedelta | int, max_size: int | None = None) -> None:
        """Initialize the cache.

        Args:
            expire (timedelta | int): The time after which the cache will be cleaned.
            max_size (int | None, optional): The maximum size of the cache (in number of elements). Defaults to None.
        """
        self._cache: OrderedDict[_K, _CachedValue[_V]] = OrderedDict()
        self._expire: timedelta = expire if isinstance(expire, timedelta) else timedelta(seconds=expire)
        self._max_size: int | None = max_size

    def __iter__(self) -> Iterator[_K]:
        """Iterate over the keys of the cache. Works like dict.__iter__. (Is literally dict.__iter__)

        Returns:
            Iteraror[_K]: An instanced iterator that iter over the keys.
        """
        return iter(self._cache)

    def __len__(self) -> int:
        """Get the length of the cache. Works like dict.__len__. (Is literally dict.__len__)"""
        return self._cache.__len__()

    def __repr__(self) -> str:
        """Get the representation of the cache."""
        return repr({key: value.value for key, value in self._cache.items()})

    @as_cleaner
    def __getitem__(self, key: _K) -> _V:
        """Get an item from the cache. Works like dict.__getitem__. (Is literally dict.__getitem__).
        Will clean the cache before.

        Args:
            key (_K): The key of the item to get.

        Returns:
            _V: The value of the item.

        Raises:
            KeyError: If the key is not in the cache.
        """
        return self._cache.__getitem__(key).value

    @as_cleaner
    def __setitem__(self, key: _K, value: _V) -> None:
        """Set an item in the cache. Works almost like dict.__setitem__.
        Will clean the cache before.

        Args:
            key (_K): The key of the item to set.
            value (_V): The value of the item to set.
        """
        self._set(key, value)

    def clean(self):
        """Clean the cache : loop over the cache and remove the expired items."""
        # Values are sorted by date, so we can just pop the first items until we find one that is not expired.
        while len(self) > 0 and next(iter(self._cache.values())).date < datetime.now():
            self._cache.popitem(last=False)

    def _set(self, key: _K, value: _V) -> None:
        """Private method to set an item in the cache.

        Args:
            key (_K): The key of the item to set.
            value (_V): The value of the item to set.
        """
        cached_value = _CachedValue(date=datetime.now() + self._expire, value=value)
        if self._max_size and len(self) >= self._max_size:
            self._cache.popitem(last=False)
        self._cache[key] = cached_value

    @as_cleaner
    def setdefault(self, key: _K, value: _V) -> None:
        """Set an item in the cache if the key is not already present. Works like dict.setdefault.
        Will clean the cache before.

        Args:
            key (_K): The key of the item to set.
            value (_V): The value of the item to set.
        """
        if key in self:
            return

        self._set(key, value)


class _CachedValue(NamedTuple, Generic[_V]):
    date: datetime
    value: _V


class SizedSequence(Sequence[T]):
    def __init__(self, max_size: int, init: Sequence[T] | None = None) -> None:
        self._max_size: int = max_size

        if init is None:
            self._internal: list[T] = []
        elif len(init) > max_size:
            raise ValueError("The initial sequence is too long.")
        else:
            self._internal = list(init)

    def __getitem__(self, i: int):
        return self._internal.__getitem__(i)

    def __setitem__(self, index: int, value: T):
        return self._internal.__setitem__(index, value)

    def __delitem__(self, index: int):
        return self._internal.__delitem__(index)

    def __len__(self):
        return self._internal.__len__()

    def append(self, value: T):
        if len(self) >= self._max_size:
            self._internal.pop(0)
        return self._internal.append(value)

    def __repr__(self) -> str:
        return self._internal.__repr__()


class SizedMapping(MutableMapping[_K, _V]):
    def __init__(self, max_size: int) -> None:
        self._max_size: int = max_size
        self._internal = OrderedDict[_K, _V]()

    def __getitem__(self, key: _K):
        return self._internal[key]

    def __setitem__(self, key: _K, value: _V) -> None:
        self.append(key, value)

    def __delitem__(self, key: _K) -> None:
        del self._internal[key]

    def __len__(self):
        return len(self._internal)

    def __iter__(self):
        return iter(self._internal)

    def append(self, key: _K, value: _V) -> None:
        if key in self:
            self._internal.move_to_end(key)
            return
        if len(self) >= self._max_size:
            self._internal.popitem(last=False)
        self._internal[key] = value

    def __repr__(self) -> str:
        return self._internal.__repr__()
