#!/bin/bash
if [ ! -z $CODESPACE_NAME ]; then
    echo "$CODESPACE_NAME"-12333."$GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN"
fi