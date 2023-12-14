venv_path := justfile_directory() / ".venv"
python := venv_path / "bin/python"
set dotenv-load := true

bootstrap_macos:
    # pg_isready is here; this needs to be put on PATH somehow (I use direnv,
    # and put a PATH_add in .envrc)
    #
    # PDM is the dependency manager we're using
    brew install postgresql@16 pdm

setup: virtualenv env_file
    echo "If this is your first run, also run 'initdb'"

virtualenv:
    #!/usr/bin/env bash
    set -eu -o pipefail

    if [ ! -d {{venv_path}} ]; then
        echo "{{venv_path}} not found, creating one..."
        python -m venv {{venv_path}}
        pdm sync
    fi

env_file:
    #!/usr/bin/env bash
    set -eu -o pipefail
    if [ ! -f {{ justfile_directory() }}/.env ]; then
        new_password=$(LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom | head -c 10; echo)
        cat {{ justfile_directory() }}/.env.sample \
            | sed -e 's/NOM_DB_PASSWORD=.*$/NOM_DB_PASSWORD='$new_password'/' \
            > {{ justfile_directory() }}/.env
        echo "Sample environment set up in .env; please change the password!"
    fi

install:
    #!/usr/bin/env bash
    pdm install

# Serve locally
serve: setup
    {{ python }} manage.py runserver localhost:12333


resetdb:
    #!/usr/bin/env bash
    docker compose down -v
    rm -rf */migrations

startdb:
    #!/usr/bin/env bash
    docker compose up -d
    export PGPASSWORD=$NOM_DB_PASSWORD
    while ! pg_isready -h $NOM_DB_HOST -p $NOM_DB_PORT -U $NOM_DB_USER; do
        sleep 1
    done

initdb: startdb
    #!/usr/bin/env bash
    {{ python }} manage.py makemigrations wsfs
    {{ python }} manage.py makemigrations nominate
    {{ python }} manage.py migrate

seed:
    #!/usr/bin/env bash
    set -eu -o pipefail
    shopt -s nullglob
    for seed_file in {{ justfile_directory() }}/seed/all/*.json; do
        {{ python }} manage.py loaddata $seed_file
    done
    for seed_file in {{ justfile_directory() }}/seed/dev/*.json; do
        {{ python }} manage.py loaddata $seed_file
    done

nuke: resetdb initdb seed
