from __future__ import annotations

import contextlib
import os
from typing import TYPE_CHECKING, Any, Generic, Self

import discord
from discord import ui
from typing_extensions import TypeVar

from core import AsyncInitMixin
from core.i18n import _

from .response import MessageDisplay, UneditedMessageDisplay

if TYPE_CHECKING:
    from discord import Interaction

    from mybot import MyBot


P = TypeVar("P", bound="Menu")


class Menu(ui.View, AsyncInitMixin):
    parent = None

    async def __init__(
        self,
        bot: MyBot,
        message_attached_to: discord.Message | None = None,
        timeout: float | None = 600,
        **kwargs: Any,
    ):
        del kwargs  # unused

        super().__init__(timeout=timeout)
        self._bot = bot
        self.message_attached_to: discord.Message | None = message_attached_to

    @property
    def bot(self) -> MyBot:
        return self._bot

    async def set_menu(self, inter: Interaction, menu: Menu) -> None:
        if isinstance(menu, ui.Modal):
            await inter.response.send_modal(menu)
        else:
            await inter.response.edit_message(**(await menu.message_display()), view=menu)

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


class SubMenu(Menu, Generic[P]):
    async def __init__(
        self,
        parent: P,
        timeout: float | None = 600,
    ):
        await super().__init__(
            bot=parent.bot,
            timeout=timeout,
        )
        self.parent: P = parent
        self.cancel_btn.label = _("Cancel")
        self.validate_btn.label = _("Validate")

    async def set_back(self, inter: Interaction) -> None:
        await inter.response.edit_message(**(await self.parent.message_display()), view=self.parent)

    async def cancel(self):
        pass

    @ui.button(style=discord.ButtonStyle.grey, row=4)
    async def cancel_btn(self, inter: discord.Interaction, button: ui.Button[Self]):
        del button  # unused
        await self.cancel()
        await self.set_back(inter)

    @ui.button(style=discord.ButtonStyle.green, row=4)
    async def validate_btn(self, inter: discord.Interaction, button: ui.Button[Self]):
        del button  # unused
        await self.set_back(inter)


class ModalSubMenu(Generic[P], Menu, ui.Modal):
    async def __init__(
        self,
        parent: P,
        timeout: float | None = 600,
        **kwargs: Any,
    ):
        self.custom_id: str = self.generate_custom_id()
        await Menu.__init__(
            self,
            bot=parent.bot,
            timeout=timeout,
            **kwargs,
        )

        self.parent: P = parent
