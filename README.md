# mybot

The official repository of Mybot project!

In order to generate auto-migration scripts using alembic, stop the bot (docker-compose down), run the database (docker-compose up -d database) and enter in shell :
`docker-compose run --rm -it --entrypoint=/bin/bash mybot -i`

Then, apply eventual migrations :
`alembic upgrade head`

And finally, create a migration script :
`alembic revision --autogenerate -m "your message"`
