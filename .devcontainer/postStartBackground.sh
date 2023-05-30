#!/usr/bin/env bash

export PTYME_WATCHED_DIRS=.:./.devcontainer:./.vscode
poetry run ptyme-track --standalone
