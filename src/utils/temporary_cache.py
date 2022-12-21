from collections import OrderedDict
from collections.abc import Mapping
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Generic, Iterator, NamedTuple, Self, TypeVar

_K = TypeVar("_K")
_V = TypeVar("_V")
_T = TypeVar("_T")


class TemporaryCache(Mapping[_K, _V]):  # TODO: add comments
    @staticmethod
    def as_cleaner(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def inner(self: Self, *args: Any, **kwargs: Any) -> Any:
            self.clean()
            return func(self, *args, **kwargs)

        return inner

    def __init__(self, expire: timedelta | int, max_size: int | None = None) -> None:
        self._cache: OrderedDict[_K, CachedValue[_V]] = OrderedDict()
        self._expire: timedelta = expire if isinstance(expire, timedelta) else timedelta(seconds=expire)
        self._max_size: int | None = max_size

    def __iter__(self) -> Iterator[_K]:
        return iter(self._cache)

    @as_cleaner
    def __getitem__(self, key: _K) -> _V:
        return self._cache.__getitem__(key).value

    def __len__(self) -> int:
        return self._cache.__len__()

    def __repr__(self) -> str:
        return repr({key: value.value for key, value in self._cache.items()})

    @as_cleaner
    def __setitem__(self, key: _K, value: _V) -> None:
        self.set(key, value)

    def clean(self):
        while len(self) > 0 and next(iter(self._cache.values())).date < datetime.now():
            self._cache.popitem(last=False)

    @as_cleaner
    def get(self, key: _K, default: _T | None = None) -> _V | _T | None:  # TODO: fix this
        tmp = self._cache.get(key)
        return default if tmp is None else tmp.value

    @as_cleaner
    def set(self, key: _K, value: _V) -> None:
        cached_value = CachedValue(date=datetime.now() + self._expire, value=value)
        if self._max_size and self.__len__() >= self._max_size:
            self._cache.popitem(last=False)
        self._cache[key] = cached_value


class CachedValue(NamedTuple, Generic[_V]):
    date: datetime
    value: _V
