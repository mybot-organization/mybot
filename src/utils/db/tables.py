from sqlalchemy import Column, Integer, MetaData, Table

metadata = MetaData()

guilds = Table(
    "guilds",
    metadata,
    Column("id", Integer, primary_key=True),
)
