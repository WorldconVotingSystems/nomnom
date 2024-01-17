#!/bin/bash

wget -qO - 'https://proget.makedeb.org/debian-feeds/prebuilt-mpr.pub' | gpg --dearmor | sudo tee /usr/share/keyrings/prebuilt-mpr-archive-keyring.gpg 1> /dev/null
echo "deb [arch=all,$(dpkg --print-architecture) signed-by=/usr/share/keyrings/prebuilt-mpr-archive-keyring.gpg] https://proget.makedeb.org prebuilt-mpr $(lsb_release -cs)" | sudo tee /etc/apt/sources.list.d/prebuilt-mpr.list

sudo apt update

sudo apt install --yes just postgresql-client

pipx install pdm

HERE=$(unset CDPATH && cd "$(dirname "$0")/.." && pwd)

just env_file

cat<<EOF
Environment configuration is in .env; it'll be used in docker-compose and justfile scripts.

To install the dependencies locally, run "just setup"

To start the services locally, run "just get_started"

To start running the server, "just serve"

To start the services in docker, run "just initdb seed" followed by "just stack"
EOF
