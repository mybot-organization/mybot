from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.app_commands import locale_str as __
from discord.utils import get

from core import ExtendedCog, db

if TYPE_CHECKING:
    from discord import Interaction

    from mybot import MyBot


logger = logging.getLogger(__name__)


class Stats(ExtendedCog):
    def __init__(self, bot: MyBot):
        super().__init__(bot)

    @ExtendedCog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        # TODO: send a message in the 'bot add' channel
        async with self.bot.async_session.begin() as session:
            await self.bot.get_or_create_db(session, db.GuildDB, guild_id=guild.id)
        await self.update_guild_count()

    @ExtendedCog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        # TODO: send a message in the 'bot add' channel
        await self.update_guild_count()

    async def update_guild_count(self):
        async with self.bot.async_session.begin() as session:
            session.add(db.TSGuildCount(value=len(self.bot.guilds)))

    @ExtendedCog.listener()
    async def on_interaction(self, inter: Interaction) -> None:
        if inter.command is None:
            return

        if isinstance(inter.command, app_commands.Command):
            parent = inter.command.root_parent or inter.command
        else:
            parent = inter.command

        app_command = get(self.bot.app_commands, name=parent.name)
        if app_command is None:
            return

        payload = {
            "command": parent.name,
            "exact_command": inter.command.qualified_name,
            "type": app_command.type.name,
            "locale": inter.locale.name,
            "namespace": inter.namespace.__dict__,
        }

        async with self.bot.async_session.begin() as session:
            if inter.guild:
                await self.bot.get_or_create_db(session, db.GuildDB, guild_id=inter.guild.id)
            session.add(
                db.TSUsage(
                    user_id=inter.user.id,
                    guild_id=inter.guild.id if inter.guild else None,
                    data=payload,
                )
            )

    @app_commands.command(
        name=__("stats"),
        description=__("Get some stats about the bot."),
        extras={"soon": True},
    )
    async def stats(self, inter: Interaction) -> None:
        raise NotImplementedError


async def setup(bot: MyBot):
    await bot.add_cog(Stats(bot))
