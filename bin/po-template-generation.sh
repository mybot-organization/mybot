#!/usr/bin/env bash
xgettext -d mybot -p ./data/locale -o mybot.pot -L python -k__ ./src/**/*.py
