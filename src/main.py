import logging
from os import environ
from typing import Any

import click

from core._config import config, define_config
from core._logger import create_logger
from mybot import MyBot

logger = create_logger(level=getattr(logging, environ.get("LOG_LEVEL", "INFO")))
logging.getLogger("discord").setLevel(logging.INFO)


@click.group()
def cli():
    pass


@cli.command()
@click.option("--postgres-user", default=None, type=str, envvar="POSTGRES_USER")
@click.option("--postgres-db", default=None, type=str, envvar="POSTGRES_DB")
@click.option("--postgres-password", required=True, type=str, envvar="POSTGRES_PASSWORD")
def db(
    postgres_user: str | None,
    postgres_db: str | None,
    postgres_password: str,
):
    kwargs: dict[str, Any] = {}
    if postgres_user is not None:
        kwargs["POSTGRES_USER"] = postgres_user
    if postgres_db is not None:
        kwargs["POSTGRES_DB"] = postgres_db
    kwargs["POSTGRES_PASSWORD"] = postgres_password

    define_config(None, **kwargs)

    # this part will probably contains some migrations informations.
    # I need to take a look at Alembic. There is no use currently.

    import asyncio

    from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

    from core import db

    engine: AsyncEngine = create_async_engine(
        f"postgresql+asyncpg://{config.POSTGRES_USER}:{config.POSTGRES_PASSWORD}@database:5432/{config.POSTGRES_DB}",
        echo=False,
    )
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async def manipulation():
        async with async_session.begin() as session:
            poll = await session.get(db.Poll, 1)

            if poll:
                result = await session.execute(db.select(db.PollChoice).where(db.PollChoice.poll_id == poll.id))
                print(result.all())

    asyncio.run(manipulation())


@cli.command()
@click.option(
    "-c",
    "--config",
    "config_path",
    default=None,
    type=click.Path(exists=True),
    help="Bind a configuration file.",
)
@click.option("--sync", is_flag=True, default=False, help="Sync slash command with Discord.")
@click.option("--sync-only", is_flag=True, default=False, help="Don't start the bot: just sync commands.")
@click.option("--token", required=True, type=str, envvar="MYBOT_TOKEN")
@click.option("--postgres-user", default=None, type=str, envvar="POSTGRES_USER")
@click.option("--postgres-db", default=None, type=str, envvar="POSTGRES_DB")
@click.option("--postgres-password", required=True, type=str, envvar="POSTGRES_PASSWORD")
def bot(
    config_path: str | None,
    sync: bool,
    sync_only: bool,
    token: str,
    postgres_user: str | None,
    postgres_db: str | None,
    postgres_password: str,
):
    kwargs: dict[str, Any] = {}
    if postgres_user is not None:
        kwargs["POSTGRES_USER"] = postgres_user
    if postgres_db is not None:
        kwargs["POSTGRES_DB"] = postgres_db
    kwargs["POSTGRES_PASSWORD"] = postgres_password

    define_config(config_path, **kwargs)

    if sync_only:
        raise NotImplementedError("The option is not implemented yet. Will probably never be.")

    mybot: MyBot = MyBot(True, sync)

    mybot.run(token, reconnect=True, log_handler=None)


if __name__ == "__main__":
    cli()
