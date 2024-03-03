venv_path := justfile_directory() / ".venv"
set dotenv-load := true
os := os()
devcontainer := if env_var_or_default("USER", "nobody") == "vscode" {"true"} else {"false"}
serve_host := if env_var_or_default("CODESPACES", "false") == "true" { "0.0.0.0" } else { "localhost" }

default: serve

bootstrap: bootstrap_devcontainer bootstrap_codespaces bootstrap_macos setup

bootstrap_devcontainer:
    if [ "{{ devcontainer }}" = "true" ]; then scripts/setup-devcontainer.sh; fi

bootstrap_codespaces:
    if [ "$$CODESPACES" = "true" ]; then scripts/setup-codespaces.sh; fi

bootstrap_macos:
    # pg_isready is here; this needs to be put on PATH somehow (I use direnv,
    # and put a PATH_add in .envrc)
    #
    # PDM is the dependency manager we're using
    echo {{ os }}
    if [ {{ os }} = "macos" ]; then brew install postgresql@16 pdm; fi

setup: virtualenv env_file
    echo "If this is your first run, also run 'initdb'"

virtualenv:
    #!/usr/bin/env bash
    set -eu -o pipefail

    if [ ! -x {{venv_path}}/bin/python ]; then
        echo "{{venv_path}} doesn't contain an executable python, creating one..."
        python -m venv {{venv_path}}
        pdm sync
    fi

env_file:
    scripts/setup-env.sh

install:
    #!/usr/bin/env bash
    pdm install

# Serve locally
serve: setup
    pdm run manage.py runserver {{ serve_host }}:12333

serve-docs:
    pdm run mkdocs serve -f docs/mkdocs.yml

build-stack:
    docker compose -f docker-compose.yml -f docker-compose.dev.yml build

stack:
    docker compose -f docker-compose.yml -f docker-compose.dev.yml up

stack-shell:
    docker compose -f docker-compose.yml -f docker-compose.dev.yml run --rm web python manage.py shell

resetdb:
    #!/usr/bin/env bash
    docker compose down -v
    rm -rf */migrations

startdb:
    #!/usr/bin/env bash
    docker compose up -d db redis
    export PGPASSWORD=$NOM_DB_PASSWORD
    while ! pg_isready -h $NOM_DB_HOST -p $NOM_DB_PORT -U $NOM_DB_USER; do
        sleep 1
    done

initdb: virtualenv startdb
    #!/usr/bin/env bash
    pdm run manage.py makemigrations hugopacket
    pdm run manage.py makemigrations nominate
    pdm run manage.py migrate

seed:
    #!/usr/bin/env bash
    set -eu -o pipefail
    shopt -s nullglob
    for seed_file in {{ justfile_directory() }}/seed/all/*.json; do
        pdm run manage.py loaddata $seed_file
    done
    for seed_file in {{ justfile_directory() }}/seed/dev/*.json; do
        pdm run manage.py loaddata $seed_file
    done

get_started: initdb seed

get_working: get_started serve

nuke: resetdb initdb seed
