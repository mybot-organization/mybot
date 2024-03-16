from collections.abc import AsyncIterable, Iterator, Sequence
from enum import Enum, auto
from typing import Literal, TypeVar

T = TypeVar("T")


class CommandType(Enum):
    MISC = auto()
    APP = auto()


def chunker(seq: Sequence[T], size: int) -> Iterator[Sequence[T]]:
    return (seq[pos : pos + size] for pos in range(0, len(seq), size))


def splitter(seq: Sequence[T], number: int) -> Iterator[Sequence[T]]:
    size = (len(seq) + number - 1) // number
    return chunker(seq, size)


async def async_any(iterable: AsyncIterable[bool]) -> bool:
    async for element in iterable:
        if element:
            return True
    return False


async def async_all(iterable: AsyncIterable[bool]) -> bool:
    async for element in iterable:
        if not element:
            return False
    return True


def size_text(string: str, size: int, mode: Literal["end", "middle"] = "end") -> str:
    if len(string) < size:
        return string
    if mode == "end":
        return f"{string[: size - 1]}…"
    elif mode == "middle":
        return f"{string[: size // 2 - 10]}\n… {len(string) - size} more …{string[-size // 2 :]}"
