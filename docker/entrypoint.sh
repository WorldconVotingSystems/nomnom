#!/bin/bash

# entrypoint.sh file of Dockerfile
# Section 1- Bash options
set -o errexit
set -o pipefail
set -o nounset

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
        export REDIS_ARGS="-h $NOM_REDIS_HOST"
        redis-cli --raw incr _ping
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

# Section 3- Idempotent Django commands
. venv/bin/activate

python manage.py collectstatic --noinput
python manage.py makemigrations
python manage.py migrate

exec "$@"
