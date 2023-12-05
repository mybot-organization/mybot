#!/usr/bin/env bash
pybabel extract \
    --msgid-bugs-address="contact@mybot-discord.com" \
    --project="MyBot" \
    --version="1.0" \
    -k "_ __" \
    -o ./resources/locale/mybot.pot \
    ./src/
