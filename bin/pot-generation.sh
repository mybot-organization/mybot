#!/usr/bin/env bash
pybabel extract \
    --msgid-bugs-address="pi@airopi.dev" \
    --project="MyBot" \
    --version="1.0" \
    -k "_ __" \
    -o ./resources/locale/mybot.pot \
    ./src/
