#!/bin/bash
set -eu

cd /app

python -mvenv .venv

. .venv/bin/activate && \
  pdm install --no-lock --no-editable --no-self

# just seed
just serve
