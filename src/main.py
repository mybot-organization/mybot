import asyncio
import logging
import os
from os import environ
from pathlib import Path
from typing import Annotated, Any

import typer

from core._config import define_config
from core._logger import create_logger
from features_exporter import features_exporter

try:
    from dotenv import load_dotenv  # pyright: ignore [reportMissingImports, reportUnknownVariableType]
except ImportError:
    pass
else:
    load_dotenv()

logger = create_logger(level=getattr(logging, environ.get("LOG_LEVEL", "INFO")))
logging.getLogger("discord").setLevel(logging.INFO)

cli = typer.Typer()


@cli.command()
def run(
    config_path: Annotated[
        Path,
        typer.Option("--config", "-c", help="Bind a configuration file."),
    ] = Path("./config.toml"),
    sync: Annotated[
        bool,
        typer.Option("--sync", help="Sync slash command with Discord."),
    ] = False,
):
    required_env_var = {"POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB", "MYBOT_TOKEN"}
    optional_env_var = {
        "TOPGG_TOKEN",
        "TOPGG_AUTH",
        "MS_TRANSLATE_KEY",
        "MS_TRANSLATE_REGION",
        "TRANSLATOR_SERVICES",
        "LOG_WEBHOOK_URL",
    }
    kwargs: dict[str, Any] = {}

    if missing_env_var := required_env_var - set(os.environ):
        raise RuntimeError(f"The following environment variables are missing: {", ".join(missing_env_var)}")

    if len({"MS_TRANSLATE_KEY", "MS_TRANSLATE_REGION"} & set(os.environ)) == 1:
        raise RuntimeError("MS_TRANSLATE_KEY and MS_TRANSLATE_REGION should be either both defined or both undefined.")
    if len({"TOPGG_TOKEN", "TOPGG_AUTH"} & set(os.environ)) == 1:
        raise RuntimeError("TOPGG_TOKEN and TOPGG_AUTH should be either both defined or both undefined.")

    present_env_var = set(os.environ) & (required_env_var | optional_env_var) - {"MYBOT_TOKEN"}
    for env_var in present_env_var:
        kwargs[env_var] = os.environ[env_var]

    define_config(config_path, **kwargs)

    from mybot import MyBot  # MyBot is imported after the config is defined.

    mybot: MyBot = MyBot(True, sync)

    mybot.run(os.environ["MYBOT_TOKEN"], reconnect=True, log_handler=None)


@cli.command()
def export_features(
    filename: Annotated[Path, typer.Argument(help="The json filename for the output.")] = Path("./features.json"),
):
    define_config(EXPORT_MODE=True)
    asyncio.run(features_exporter(filename=filename))


if __name__ == "__main__":
    cli()
