venv_path := justfile_directory() / ".venv"
python := venv_path / "bin/python"

setup:
    #!/usr/bin/env bash
    set -eu -o pipefail

    if [ ! -d {{venv_path}} ]; then
        echo "{{venv_path}} not found, creating one..."
        python -m venv {{venv_path}}
        pdm sync
    fi

deps: setup
    pdm sync

# Serve locally
serve: setup
    {{ python }} manage.py runserver localhost:12333


nuke:
    #!/usr/bin/env bash
    docker compose down
    rm -rf data/db
    rm -rf */migrations
    docker compose up -d
    export PGPASSWORD=$NOM_DB_PASSWORD
    while ! pg_isready -h localhost -p 52432 -U postgres; do
        sleep 1
    done
    echo "create database $NOM_DB_NAME;" | psql -h localhost -d postgres -U postgres -p 52432
    {{ python }} manage.py makemigrations wsfs
    {{ python }} manage.py makemigrations nominate
    {{ python }} manage.py migrate
