#!/bin/bash
set -eu

cd /app

if [ $# -eq 0 ]; then
    echo "Usage: start.sh [PROCESS_TYPE](server/beat/worker/flower)"
    exit 1
fi

PROCESS_TYPE=$1
DJANGO_DEBUG=${NOM_DEBUG:-false}

if [ "$PROCESS_TYPE" = "server" ]; then
    if [ "$DJANGO_DEBUG" = "true" ]; then
        gunicorn \
            --reload \
            --bind 0.0.0.0:8000 \
            --workers 2 \
            --worker-class eventlet \
            --log-level DEBUG \
            --access-logfile "-" \
            --error-logfile "-" \
            --access-logformat '%({X-Forwarded-For}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"' \
            nomnom.wsgi
    else
        gunicorn \
            --bind 0.0.0.0:8000 \
            --workers 2 \
            --worker-class eventlet \
            --log-level DEBUG \
            --access-logfile "-" \
            --error-logfile "-" \
            --access-logformat '%({X-Forwarded-For}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"' \
            nomnom.wsgi
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
        --basic_auth="${CELERY_FLOWER_USER}:${CELERY_FLOWER_PASSWORD}" \
        --loglevel INFO
elif [ "$PROCESS_TYPE" = "worker" ]; then
    celery \
        --app nomnom.celery_app \
        worker \
        --loglevel INFO
elif [ "$PROCESS_TYPE" = "bootstrap" ]; then
    static_root=$(python manage.py print_settings --format=value STATIC_ROOT)
    rm -f "$static_root/.bootstrapped"
    python manage.py collectstatic --noinput
    python manage.py migrate
    echo "Bootstrap completed; leaving the boot container running"
    touch "$static_root/.bootstrapped"
    exec /bin/bash -c "trap : TERM INT; sleep infinity & wait"
elif [ "$PROCESS_TYPE" = "bootstrap-healthy" ]; then
    static_root=$(python manage.py print_settings --format=value STATIC_ROOT)
    if test -f "$static_root/.bootstrapped"; then
        exit 0
    else
        echo "Can't find $static_root/.bootstrapped; waiting"
        exit 1
    fi
else
    >&2 echo "Unknown process type: $PROCESS_TYPE"
    exit 1
fi
