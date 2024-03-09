docker compose --progress quiet build mybot
docker compose --progress quiet run --rm -t -v "${PWD}:/app" mybot python3 ./src/commands_exporter.py
