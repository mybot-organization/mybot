#!/usr/bin/env bash
xgettext -d mybot -p ./data/locale -L python -k__ ./src/**/*.py
