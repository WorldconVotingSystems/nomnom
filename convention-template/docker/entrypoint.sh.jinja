#!/bin/sh

# entrypoint.sh file of Dockerfile
# Section 1- Bash options
set -o errexit
set -o nounset

NOM_DB_PORT=${NOM_DB_PORT:-5432}
NOM_REDIS_PORT=${NOM_REDIS_PORT:-6379}

DJANGO_SETTINGS_MODULE="config.settings"
export DJANGO_SETTINGS_MODULE

postgres_ready() {
  (
    export PGPASSWORD=$NOM_DB_PASSWORD

    pg_isready -h $NOM_DB_HOST \
      -p $NOM_DB_PORT \
      -U $NOM_DB_USER
  )
}

redis_ready() {
  (
    redis-cli -h $NOM_REDIS_HOST --raw incr _ping
  )
}

until postgres_ready; do
  >&2 echo "Waiting for PostgreSQL to become available..."
  sleep 1
done
>&2 echo "PostgreSQL is available"
until redis_ready; do
  >&2 echo "Waiting for Redis to become available..."
  sleep 1
done
>&2 echo "Redis is available"

>&2 echo "Running '$@'"
exec "$@"
