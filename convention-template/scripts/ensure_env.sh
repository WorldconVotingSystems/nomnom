#!/bin/bash

if test -f .env; then
    echo ".env already exists; skipping"
    exit 0
fi

SECRET_KEY=$(head -c 16 /dev/urandom | base64 | tr -dc 'a-zA-Z0-9')
DB_PASSWORD=$(head -c 16 /dev/urandom | base64 | tr -dc 'a-zA-Z0-9')
FLOWER_PASSWORD=$(head -c 16 /dev/urandom | base64 | tr -dc 'a-zA-Z0-9')

cat <<EOF >>.env
# During development, you may not have OAuth; this allows usernames
NOM_ALLOW_USERNAME_LOGIN=true

NOM_DEBUG=True
NOM_SECRET_KEY="$SECRET_KEY"
NOM_DB_NAME=nominate
NOM_DB_USER=postgres
NOM_DB_PASSWORD="$DB_PASSWORD"
NOM_DB_PORT=5432
NOM_DB_HOST=localhost
NOM_REDIS_HOST=localhost
NOM_REDIS_PORT=6379
NOM_ALLOWED_HOSTS=127.0.0.1,localhost

NOM_OAUTH_KEY=bogon
NOM_OAUTH_SECRET=bogon

NOM_EMAIL_HOST=localhost
NOM_EMAIL_PORT=51025

CELERY_FLOWER_USER=flower
CELERY_FLOWER_PASSWORD="$FLOWER_PASSWORD"
EOF
