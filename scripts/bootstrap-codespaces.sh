#!/bin/bash

wget -qO - 'https://proget.makedeb.org/debian-feeds/prebuilt-mpr.pub' | gpg --dearmor | sudo tee /usr/share/keyrings/prebuilt-mpr-archive-keyring.gpg 1> /dev/null
echo "deb [arch=all,$(dpkg --print-architecture) signed-by=/usr/share/keyrings/prebuilt-mpr-archive-keyring.gpg] https://proget.makedeb.org prebuilt-mpr $(lsb_release -cs)" | sudo tee /etc/apt/sources.list.d/prebuilt-mpr.list

sudo apt update

sudo apt -Y install just postgresql-client

pipx install pdm

HERE=$(unset CDPATH && cd "$(dirname "$0")/.." && pwd)

just setup

cat<<EOF
To start the services, run "just get_started"

To start running the server, "just serve"
EOF
