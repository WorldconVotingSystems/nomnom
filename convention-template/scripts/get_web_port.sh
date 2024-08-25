#!/bin/bash
set -eu -o pipefail

# Find an open port in the 12000-13000 range and write it
# to .env as DEV_SERVER_PORT

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

# find an open port in the 12000-13000 range
for port in $(seq 12000 13000); do
    if ! nc -z localhost $port; then
        set_in_dotenv DEV_SERVER_PORT $port
        break
    fi
done
