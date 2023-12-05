docker compose --progress quiet up database -d --quiet-pull
docker compose --progress quiet run --rm -t -v "${PWD}/alembic:/app/alembic" mybot alembic "$@"
