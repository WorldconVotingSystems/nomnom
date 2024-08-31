#!/bin/bash
set -eu -o pipefail

# Get the ports for the three services running under docker, and write
# them to .env

# Don't accept compose files from the environment
unset COMPOSE_FILE

get_service_port() {
    docker compose port $1 $2 | cut -d: -f2
}

# get the right sed
if [[ $(uname) == "Darwin" ]]; then
    sed="gsed"
else
    sed="sed"
fi

set_in_dotenv() {
    # replace the existing value if it exists, otherwise append
    if grep -q "^$1=" .env; then
        $sed -i "s/^$1=.*/$1=$2/" .env
    else
        echo "$1=$2" >>.env
    fi
}

set_in_dotenv NOM_DB_PORT $(get_service_port db 5432)
set_in_dotenv NOM_REDIS_PORT $(get_service_port redis 6379)
set_in_dotenv NOM_EMAIL_PORT $(get_service_port mailcatcher 1025)
