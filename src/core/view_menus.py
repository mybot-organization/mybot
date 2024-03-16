from __future__ import annotations

import contextlib
import os
from typing import TYPE_CHECKING, Any, Generic, Self

import discord
from discord import ui
from typing_extensions import TypeVar

from .response import MessageDisplay, UneditedMessageDisplay

if TYPE_CHECKING:
    from discord import Interaction

BotT = TypeVar("BotT", bound=discord.Client, default=discord.Client)


class Menu(ui.View, Generic[BotT]):
    bot: BotT

    def __init__(
        self,
        bot: BotT | None = None,
        parent: Menu[BotT] | None = None,
        message_attached_to: discord.Message | None = None,
        timeout: float | None = 600,
        **kwargs: Any,
    ):
        """
        While building the view needs to be async, you shouldn't use __init__ to create a new Menu.
        Instead, always use the `new` method.
        """
        del kwargs  # unused
        if parent is None and bot is None:
            raise ValueError("You must provide a parent or the bot.")

        super().__init__(timeout=timeout)
        self.bot = bot or parent.bot  # pyright: ignore[reportOptionalMemberAccess]
        self.parent = parent
        self.message_attached_to: discord.Message | None = message_attached_to

    async def set_back(self, inter: Interaction) -> None:
        if not self.parent:
            raise ValueError(f"This menu has no parent. Menu : {self}")
        await inter.response.edit_message(**(await self.parent.message_display()), view=self.parent)

    async def set_menu(self, inter: Interaction, menu: Menu[BotT]) -> None:
        if isinstance(menu, ui.Modal):
            await inter.response.send_modal(menu)
        else:
            await inter.response.edit_message(**(await menu.message_display()), view=menu)

    async def build(self) -> Self:
        """
        Add buttons label, selects values, etc... Called with the `new` method.
        """
        await self.update()
        return self

    async def update(self) -> None:
        """
        Update the view with new values. Will set selected values as default for selects by default.
        """
        for item in self.children:
            if isinstance(item, ui.Select):
                for option in item.options:
                    option.default = option.value in item.values

    def disable_view(self):
        for item in self.children:
            if isinstance(item, ui.Button | ui.Select):
                item.disabled = True

    async def on_timeout(self) -> None:
        if self.message_attached_to:
            self.disable_view()
            with contextlib.suppress(discord.NotFound, discord.HTTPException):
                await self.message_attached_to.edit(view=self)

    async def message_display(self) -> MessageDisplay | UneditedMessageDisplay:
        """This function can be defined and used in order to add a message content (embeds, etc...) within the menu."""
        return UneditedMessageDisplay()

    async def message_refresh(self, inter: Interaction, refresh_display: bool = True):
        await self.update()
        if refresh_display:
            await inter.response.edit_message(view=self, **await self.message_display())
        else:
            await inter.response.edit_message(view=self)

    @staticmethod
    def generate_custom_id() -> str:
        return os.urandom(16).hex()


class ModalMenu(Menu[BotT], ui.Modal):
    def __init__(
        self,
        bot: BotT | None = None,
        parent: Menu[BotT] | None = None,
        timeout: float | None = 600,
        **kwargs: Any,
    ):
        self.custom_id: str = self.generate_custom_id()
        Menu[BotT].__init__(
            self,
            bot=bot,
            parent=parent,
            timeout=timeout,
            **kwargs,
        )
