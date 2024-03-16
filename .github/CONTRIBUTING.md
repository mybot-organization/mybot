Feel free to contribute to MyBot.
There is mainly three ways to contribute :

1.  Source code contributions
2.  Translations contributions
3.  Financial contributions

## Source code contributions

If you have any suggestion for the bot, and you think you have the ability to do it yourself, start by contacting me through Discord!
It would be a pleasure to count you from the Mybot's contributors!
Then, fork this project, make the changes you want, and open a Pull Request on `master`.

## Good practices and requirements

### Dependencies

The project is using [pip-tools](https://github.com/jazzband/pip-tools) to manage its dependencies. Then, requirements are declared in [requirements.in](/requirements.in), and developers requirements are in [requirements.dev.in](/requirements.dev.in).

Install the dependencies using `pip-sync` or simply `pip install -r requirements.txt`, as well as the developer dependencies with `pip install -r requirements.dev.txt`.

If you add or change dependencies, edit the `*.in` file, and use `pip-compile` (`pip-compile requirements.dev.in` for developer deps).

### Lint, formatting...

The project use [pyright](https://github.com/microsoft/pyright) for static type checking, [black](https://github.com/psf/black) for general formatting, [isort](https://github.com/PyCQA/isort) for import sorting, [bandit](https://github.com/PyCQA/bandit) for security scans, and [pylint](https://github.com/pylint-dev/pylint) for static code analyses.

Please use these tool to avoid github action failure. [tox](https://github.com/tox-dev/tox) can be used to run every checks before committing. Simply run `tox`.

## Docker watch

The [compose file](/compose.yml) implements [watch](https://docs.docker.com/compose/file-watch/) to help debugging the code. By running `docker compose watch`, the bot will be executed while observing for files changes or deps updates. This will allow extensions reload, and speed up restarts (rebuild not needed).

## Run the code on debug version

You can use [debugpy](https://github.com/microsoft/debugpy) easily when running MyBot on local, for dev and debug purposes.  
Replace `docker compose` by `docker compose -f compose.yml -f compose.debug.yml` when using Docker Compose. Then you can use debugpy within the port `5678`.

Additionally, this will setup the `config.DEBUG` to `True` from the code pov, it will set the logger level to DEBUG, and expose the PostgresSQL port to the host (`5432`).

## Translations contributions

MyBot is a multi-language bot! The codebase is in english, which is then translated in several languages.

Currently, MyBot is translated in :

- French

If you know one of these languages, you can contribute to translations here:
https://crowdin.com/project/mybot-discord

If you are able to add a new language to the bot, please contact me on Discord! It would be a pleasure to add a new language to MyBot!
However, this language must also be available on the Discord application.

## Financial contributions

You can make voluntary donation at https://www.buymeacoffee.com/airopi

---

Thanks !
