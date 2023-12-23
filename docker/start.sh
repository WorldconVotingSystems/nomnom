#!/bin/bash
set -eu

cd /app

if [ $# -eq 0 ]; then
    echo "Usage: start.sh [PROCESS_TYPE](server/beat/worker/flower)"
    exit 1
fi

STATIC_ROOT=$(python manage.py print_settings --format=value STATIC_ROOT)

PROCESS_TYPE=$1
DJANGO_DEBUG=${NOM_DEBUG:-false}

wait_for_bootstrap() {
    sleep 1
    while ! test -f "$STATIC_ROOT/.bootstrapped"; do
        echo "Waiting for the bootstrap indicator in $STATIC_ROOT/.bootstrapped"
        sleep 1
    done
    echo "... done bootstrapping"
}

if [ "$PROCESS_TYPE" = "server" ]; then
    wait_for_bootstrap

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
    wait_for_bootstrap

    celery \
        --app nomnom.celery_app \
        beat \
        --loglevel INFO \
        --scheduler django_celery_beat.schedulers:DatabaseScheduler
elif [ "$PROCESS_TYPE" = "flower" ]; then
    wait_for_bootstrap

    celery \
        --app nomnom.celery_app \
        flower \
        --basic_auth="${CELERY_FLOWER_USER}:${CELERY_FLOWER_PASSWORD}" \
        --loglevel INFO
elif [ "$PROCESS_TYPE" = "worker" ]; then
    wait_for_bootstrap

    celery \
        --app nomnom.celery_app \
        worker \
        --loglevel INFO
elif [ "$PROCESS_TYPE" = "bootstrap" ]; then
    rm -f "$STATIC_ROOT/.bootstrapped"
    python manage.py collectstatic --noinput
    python manage.py migrate
    echo "Bootstrap completed; leaving the boot container running"
    touch "$STATIC_ROOT/.bootstrapped"
    exec /bin/bash -c "trap : TERM INT; sleep infinity & wait"
elif [ "$PROCESS_TYPE" = "bootstrap-healthy" ]; then
    if test -f "$STATIC_ROOT/.bootstrapped"; then
        exit 0
    else
        echo "Can't find $STATIC_ROOT/.bootstrapped; waiting"
        exit 1
    fi
else
    >&2 echo "Unknown process type: $PROCESS_TYPE"
    exit 1
fi
