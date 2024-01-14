#!/bin/bash
chars="${1:-16}"

export LC_ALL=C

tr -dc '[:alnum:]' < /dev/urandom | head -c "$chars"; echo
