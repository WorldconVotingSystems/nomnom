#!/bin/bash
set -eux -o pipefail

# .env must exist, but it can be empty
touch .env

docker compose -f docker-compose.yml up -d db redis mailcatcher
counter=1
while ! pg_isready -h $NOM_DB_HOST -p $NOM_DB_PORT -U $NOM_DB_USER; do
    if [ $counter -le 20 ]; then
        ((counter++))
        sleep 1
    else
        docker compose ps db
        docker compose logs db
        break
    fi
done
