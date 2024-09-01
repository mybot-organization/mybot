from __future__ import annotations

from typing import TYPE_CHECKING

from core.utils import fbgetattr

from ..tables import UserDB
from ..utils import with_session_begin

if TYPE_CHECKING:
    import discord
    from sqlalchemy.ext.asyncio import AsyncSession


@with_session_begin
async def update_or_create_user(session: AsyncSession, user: discord.User | discord.Member) -> None:
    user_db = await session.get(UserDB, user.id)
    if user_db is None:
        print("User not found in the database. Added.")
        user_db = UserDB(user_id=user.id, username=user.name, avatar=user.display_avatar.url)
        session.add(user_db)
        await session.commit()
    else:
        keymap: dict[str, tuple[str, ...] | str] = {
            "username": "name",
            "avatar": ("avatar.url", "default_avatar.url"),
        }
        updated = False
        for db_key, discord_key in keymap.items():
            if getattr(user_db, db_key) != (value := fbgetattr(user, discord_key)):
                setattr(user_db, db_key, value)
                updated = True
        if updated:
            await session.commit()
            print("User found in the database. Updated.")
        else:
            print("User found in the database. Nothing to change.")
