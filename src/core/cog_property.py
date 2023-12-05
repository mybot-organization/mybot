from typing import TYPE_CHECKING, Any, Callable, TypeVar

from .errors import NonSpecificError

if TYPE_CHECKING:
    from discord.ext.commands import Cog  # pyright: ignore[reportMissingTypeStubs]


C = TypeVar("C", bound="Cog")


def cog_property(cog_name: str):
    """Transform a method into a property that return the cog with the name passed in argument.
    Type is not truly correct because we force it to be a Cog value while it is a property that return a Cog.

    Args:
        cog_name (str): the cog name to return
    """

    def inner(_: Callable[..., C]) -> C:
        @property
        def cog_getter(self: Any) -> C:  # self is a cog within the .bot attribute (because every Cog should have it)
            cog: C | None = self.bot.get_cog(cog_name)
            if cog is None:
                raise NonSpecificError(f"Cog named {cog_name} is not loaded.")
            return cog

        return cog_getter  # type: ignore

    return inner
