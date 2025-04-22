#!/bin/bash
set -eu

cd /app

if [ $# -eq 0 ]; then
    echo "Usage: start.sh [PROCESS_TYPE](server/beat/worker/flower/bootstrap)"
    exit 1
fi

PROCESS_TYPE=$1
DJANGO_DEBUG=${NOM_DEBUG:-false}
WEB_CONCURRENCY=${WEB_CONCURRENCY:-2}
WEB_WORKER_TIMEOUT=${WEB_WORKER_TIMEOUT:-300}

if [ "$PROCESS_TYPE" = "server" ]; then
    if [ "$DJANGO_DEBUG" = "true" ]; then
        python manage.py runserver 0.0.0.0:8000
    else
        granian \
            --host 0.0.0.0 \
            --port 8000 \
            --workers "$WEB_CONCURRENCY" \
            --workers-lifetime "$WEB_WORKER_TIMEOUT" \
            --interface asginl \
            --access-log \
            config.asgi:application
    fi
elif [ "$PROCESS_TYPE" = "beat" ]; then

    celery \
        --app nomnom.celery_app \
        beat \
        --loglevel INFO \
        --scheduler django_celery_beat.schedulers:DatabaseScheduler
elif [ "$PROCESS_TYPE" = "flower" ]; then

    celery \
        --app nomnom.celery_app \
        flower \
        --port=8000 \
        --basic_auth="${CELERY_FLOWER_USER}:${CELERY_FLOWER_PASSWORD}" \
        --loglevel INFO
elif [ "$PROCESS_TYPE" = "worker" ]; then

    celery \
        --app nomnom.celery_app \
        worker \
        --loglevel INFO
elif [ "$PROCESS_TYPE" = "bootstrap" ]; then
    python manage.py collectstatic --noinput
    python manage.py migrate
    python manage.py compilemessages
    echo "Bootstrap completed"
    exit 0
elif [ "$PROCESS_TYPE" = "dev-seed" ]; then
    for seed_file in /app/seed/all/*.json; do
        echo "Seeding $seed_file"
        python manage.py loaddata "$seed_file"
    done
    for seed_file in /app/seed/dev/*.json; do
        echo "Seeding $seed_file"
        python manage.py loaddata "$seed_file"
    done
    echo "Seeding completed"
    exit 0
else
    >&2 echo "Unknown process type: $PROCESS_TYPE"
    exit 1
fi
