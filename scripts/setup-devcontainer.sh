#!/bin/bash

set -x

HERE=$(unset CDPATH && cd "$(dirname "$0")/.." && pwd)

sudo chown -R $USER $HERE/.venv

direnv allow
