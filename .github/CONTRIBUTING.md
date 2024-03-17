# Contribution Guidelines

Feel free to contribute to MyBot.
There is mainly three ways to contribute:

1.  Source code contributions
2.  Translations contributions
3.  Financial contributions

## Source code contributions

If you have any suggestions for the bot and you think you have the ability to do it yourself, consider contacting me through [Discord](https://discord.gg/GRsAy4aUgu)!
It would be a pleasure to count you to the Mybot's contributors!
Then, fork this project, make the changes you want, and open a Pull Request on `master`.

## Good practices and requirements

### Dependencies

The project is using [pip-tools](https://github.com/jazzband/pip-tools) to manage its dependencies. The requirements are declared in [requirements.in](/requirements.in) and developers requirements are in [requirements.dev.in](/requirements.dev.in).

Install the dependencies using `pip-sync` or simply `pip install -r requirements.txt`, as well as the developer dependencies with `pip install -r requirements.dev.txt`.

If you add or change dependencies, edit the corresponding `.in` file, then use `pip-compile` (`pip-compile requirements.dev.in` for developer deps).

### Lint, formatting...

The project use [pyright](https://github.com/microsoft/pyright) for static type checking and [ruff](https://github.com/astral-sh/ruff) for general formatting, import sorting, security scans and static code analyses.

Please use these tool to avoid Github Actions failure. [tox](https://github.com/tox-dev/tox) can be used to run every checks before committing by running `tox`.

## Docker watch

The [compose file](/compose.yml) implements [watch](https://docs.docker.com/compose/file-watch/) to help debugging the code. By running `docker compose watch`, the bot will be executed while observing for files changes or deps updates. This will allow extensions reload, and speed up restarts (it avoids rebuilds).

## Run the code on debug version

You can use [debugpy](https://github.com/microsoft/debugpy) easily when running MyBot locally, for dev and debug purposes.  
Replace `docker compose` with `docker compose -f compose.yml -f compose.debug.yml` when using Docker Compose. You can then use debugpy with the port `5678`.

Additionally, this will setup `config.DEBUG` to `True` from the code perspective, which will also set the logger level to `DEBUG`, and expose the PostgresSQL port to the host (`5432`).

### VSCode debug config

As an example, here is a json configuration that can be added inside your local `.vscode/launch.py` to use the integrated debugger:
```json
{
    "name": "debug",
    "type": "debugpy",
    "request": "attach",
    "connect": {
        "host": "localhost",
        "port": 5678
    },
    "pathMappings": [
        {
            "localRoot": "${workspaceFolder}/src",
            "remoteRoot": "/app"
        }
    ]
}
```

After you run the code in debug mode, click on the "play" icon inside VSCode to attach the debug console. You can then use breakpoints, etc.  
To make the restart button actually restart the bot and not just re-attach the debugger, you can add pre&post tasks:
```json
"preLaunchTask": "bot up",
"postDebugTask": "bot restart",
```
And in `.vscode/tasks.json`, add the tasks:
```json
{
    "label": "bot up",
    "type": "shell",
    "presentation": {
        "reveal": "silent"
    },
    "command": "docker compose -f compose.yml -f compose.debug.yml up -d",
},
{
    "label": "bot restart",
    "type": "shell",
    "presentation": {
        "reveal": "silent"
    },
    "command": "docker-compose restart mybot"
}
```

If the bot is executed with the up task, you should then use the `watch` command with `--no-up`.
More information here: https://code.visualstudio.com/docs/python/debugging

## Database revisions

The project use [alembic](https://github.com/sqlalchemy/alembic) to manage database revisions.  
When the bot is started using Docker, `alembic upgrade head` is [automatically executed](https://github.com/mybot-organization/mybot/blob/cleanup/Dockerfile#L30).
To create revisions, you can use [`alembic.sh`](bin/alembic.sh) in the `bin` directory. This script allow you to use the alembic CLI inside the container, and will mount the [`/alembic`](/alembic/) directory.

If you are unfamiliar with alembic, [`here is some information`](/alembic/README). Check also the [documentation](https://alembic.sqlalchemy.org/en/latest/tutorial.html#create-a-migration-script) as well.

## Configuration and environnement

In order to run the bot without any issue, there are some prerequisites.

First, a `.env` file with the following values:
| Key                   | Requirement | Description                                                                    |
|-----------------------|-------------|--------------------------------------------------------------------------------|
| `POSTGRES_USER`       | Required    | Used to create the database                                                    |
| `POSTGRES_PASSWORD`   | Required    | Used to create the database                                                    |
| `POSTGRES_DB`         | Required    | Used to create the database                                                    |
| `MYBOT_TOKEN`         | Required    | [Create a bot](https://discord.com/developers/applications) and copy the token |
| `TOPGG_AUTH`          | Optional    | Used to sync top.gg                                                            |
| `TOPGG_TOKEN`         | Optional    | Used to sync top.gg                                                            |
| `TRANSLATOR_SERVICES` | Optional    | Will be deprecated                                                             |
| `MS_TRANSLATE_KEY`    | Optional    | Required if "microsoft" is set in `TRANSLATOR_SERVICES`                        |
| `MS_TRANSLATE_REGION` | Optional    | Required if "microsoft" is set in `TRANSLATOR_SERVICES`                        |


Then, create a `config.toml` ([TOML](https://toml.io/en/)) with the following values:
| Key                | Requirement | Description                                                |
|--------------------|-------------|------------------------------------------------------------|
| `SUPPORT_GUILD_ID` | Required    | The bot needs to be member and administrator of this guild |
| `BOT_ID`           | Required    | Used for links and top.gg (if enabled)                     |
| `BOT_NAME`         | Required    | Used for the webhook logs                                  |
| `LOG_WEBHOOK_URL`  | Optional    | Used to send bot logs using a webhook                      |
| `OWNER_IDS`        | Required    | Grant permissions such eval, extensions reload...          |

## Extra informations

In the project structure, `main.py` serves as the entry point executed by Docker. It provides a compact CLI utility with various options that can be used with pre-created shell files in the `bin/` directory.
`mybot.py` is the base of MyBot, containing the `MyBot` class, instantiated once at launch, and available in many places in the code.

The `MyBot` class has some utility functions like `getch_user`, `getch_channel`, or `get_or_create_db`. Refer to their docstring for more information.

The `core` directory container internally used code for MyBot, while `cogs` contains the implementation of features exposed by MyBot. Additionally, `libraries` holds wrappers for external APIs and tools used by the project.

### i18n

All strings should be passed into the `_` function (available in module `core.i18n`), to have them being translated automatically, e.g. `_("Hello World")`. The function also supports format options like the `str.format()` function (e.g., `_("Hello {}", name)`).

`_` allows `msgfmt` to extract the strings from the code automatically, but it will also ✨ magically ✨ translate the strings in the good language by walking through the callstack to find an `Interaction` object. (This is generally not recommended, but in this case it is justified in my opinion.)  
Consequently, using `_` outside a command callback will not retrieve the language. You can then specify it using `_locale` argument. Set `_locale` to `None` if the string should not be translated at this time in the execution.

Additionally, `_` also accepts a `_l` parameter to set a maximum size, to avoid any bugs due to translations being too long.

Strings in command parameters, descriptions, etc., should be surrounded with the `discord.app_commands.locale_str` (aliased as `__`), to make `discord.py` send the translations directly to Discord.

## Translations contributions

MyBot is a multi-language bot! The codebase is in English, which is then translated in several languages.

Currently, MyBot is translated in :

- French

If you know one of these languages, you can contribute to translations here:
https://crowdin.com/project/mybot-discord

If you want to add a new language to the bot, please contact me on Discord! It would be a pleasure to add a new language to MyBot!
However, this language must also be available on the Discord application.

## Financial contributions

You can make voluntary donations at https://www.buymeacoffee.com/airopi

---

Thanks !
