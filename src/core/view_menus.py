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
    """Menus are special views that can be used to create interactive menus.

    For example, when you use the /poll command, the menu is the view that allow to chose what you want to edit.
    Each edit menu (edit title, edit choices...) is a sub-menu of the main menu.
    These sub-menu have by default a "Cancel" and a "Validate" button.

    When clicking Validate button, the parent menu is displayed again.
    When clicking Cancel button, the method `cancel` is called and the parent menu is displayed again.
    A sub-menu can have multiple sub-menus, creating a tree of menus.

    When the Validate or Cancel button is clicked, the parent's method `update` is called to update the view.

    A sub-menu can be a Modal.

    We can attach a message to a menu. This is useful to edit the view when the menu timeout.
    """

    parent = None

    async def __init__(
        self,
        bot: MyBot,
        timeout: float | None = 600,
        inter: Interaction | None = None,
        **kwargs: Any,
    ):
        del kwargs  # unused
        self._default_timeout = timeout

        super().__init__(timeout=timeout)
        self.bot = bot
        self.inter: Interaction | None = inter

    async def set_menu(self, inter: Interaction, menu: Menu) -> None:
        """Set the display to a new menu."""
        self.inter = inter

        if not isinstance(menu, ui.Modal):
            self.timeout = None
        menu.timeout = menu._default_timeout

        await menu.update()
        if isinstance(menu, ui.Modal):
            await inter.response.send_modal(menu)
        else:
            await inter.response.edit_message(**await menu.message_display(), view=menu)

    async def edit_message(self, inter: Interaction):
        """A convenient await to update a message with self."""
        await self.set_menu(inter, self)

    async def update(self) -> None:
        """Update the components to match the datas.

        The default behavior is to set the selected values as default for ui.Select children, so the user can see what
        he selected.
        """
        for item in self.children:
            if isinstance(item, ui.Select):
                for option in item.options:
                    option.default = option.value in item.values

    def disable_view(self):
        """A utility method to disable all buttons and selects in the view."""
        for item in self.children:
            if isinstance(item, ui.Button | ui.Select):
                item.disabled = True

    async def on_timeout(self) -> None:
        if self.inter is not None:
            self.disable_view()
            with contextlib.suppress(discord.NotFound, discord.HTTPException):
                await self.inter.edit_original_response(view=self)

    async def message_display(self) -> MessageDisplay | UneditedMessageDisplay:
        """This function can be defined and used in order to add a message content (embeds, etc...) within the menu.

        Then the message content is synchronized with the view.
        """
        return UneditedMessageDisplay()

    @staticmethod
    def generate_custom_id() -> str:
        """A utility method to generate a random custom id for the menu."""
        return os.urandom(16).hex()


# TODO: try to implement the following two classes with some sort of Mixin ?
class SubMenuWithoutButtons(Menu, Generic[P]):
    async def __init__(
        self,
        parent: P,
        timeout: float | None = 600,
    ):
        await super().__init__(
            bot=parent.bot,
            timeout=timeout,
            inter=parent.inter,
        )
        self.parent: P = parent


class SubMenu(Menu, Generic[P]):
    async def __init__(
        self,
        parent: P,
        timeout: float | None = 600,
    ):
        await super().__init__(
            bot=parent.bot,
            timeout=timeout,
            inter=parent.inter,
        )
        self.parent: P = parent
        self.cancel_btn.label = _("Cancel")
        self.validate_btn.label = _("Validate")

    async def on_cancel(self):
        """Method called when the cancel button is clicked."""

    async def on_validate(self):
        """Method called when the validate button is clicked."""

    @ui.button(style=discord.ButtonStyle.grey, row=4)
    async def cancel_btn(self, inter: discord.Interaction, button: ui.Button[Self]):
        del button  # unused
        await self.on_cancel()
        await self.set_menu(inter, self.parent)

    @ui.button(style=discord.ButtonStyle.green, row=4)
    async def validate_btn(self, inter: discord.Interaction, button: ui.Button[Self]):
        del button  # unused
        await self.on_validate()
        await self.set_menu(inter, self.parent)


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

    async def on_submit(self, inter: discord.Interaction) -> None:
        await self.set_menu(inter, self.parent)
