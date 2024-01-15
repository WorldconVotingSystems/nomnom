#!/bin/bash

HERE=$(unset CDPATH && cd "$(dirname "$0")/.." && pwd)

sudo chown -R $HERE/.venv $USER
