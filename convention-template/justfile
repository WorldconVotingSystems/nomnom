venv_path := justfile_directory() / ".venv"
set dotenv-load := true
os := os()
devcontainer := if env_var_or_default("USER", "nobody") == "vscode" {"true"} else {"false"}
serve_host := if env_var_or_default("CODESPACES", "false") == "true" { "0.0.0.0" } else { "localhost" }

@default:
    just --list

bootstrap:
    #!/usr/bin/env bash
    set -eu -o pipefail

    # if our .env isn't there, this is probably a checkout;
    # we want to generate it instead.
    scripts/ensure_env.sh

    docker compose up --wait

    scripts/get_local_docker_ports.sh
    scripts/get_web_port.sh

    # we run this again to get the new environment locked in
    docker compose up --wait

    # initialize our DB; this has to be in a separate task to reload the environment
    unset NOM_DB_PORT
    just migrate
    just seed

# Serve locally
serve:
    uv run manage.py runserver {{ serve_host }}:$DEV_SERVER_PORT

worker:
    uv run celery -A nomnom worker -l INFO

serve-docs:
    uv run mkdocs serve -f docs/mkdocs.yml

build-stack:
    docker compose -f docker-compose.yml -f docker-compose.dev.yml build

stack:
    docker compose -f docker-compose.yml -f docker-compose.dev.yml up

stack-shell:
    docker compose -f docker-compose.yml -f docker-compose.dev.yml run --rm web python manage.py shell

resetdb:
    docker compose down -v

startdb:
    docker compose up -d db redis

migrate:
    uv run manage.py migrate

initdb: startdb migrate

seed:
    #!/usr/bin/env bash
    set -eu -o pipefail
    shopt -s nullglob
    for seed_file in {{ justfile_directory() }}/seed/all/*.json; do
        uv run manage.py loaddata $seed_file
    done
    for seed_file in {{ justfile_directory() }}/seed/dev/*.json; do
        uv run manage.py loaddata $seed_file
    done

@db_data:
    mkdir -p "{{ justfile_directory() }}/data/"

# dump database to file
@pg_dump file='db.dump': db_data
    docker compose run \
        --no-deps \
        --rm \
        --volume "{{ justfile_directory() }}/data/:/_data/" \
        db pg_dump \
            --dbname "${DATABASE_URL:=postgres://postgres@db/nominate}" \
            --file /_data/{{ file }} \
            --format=c \
            --verbose

# restore database dump from file
@pg_restore file='db.dump': db_data
    docker compose run \
        --no-deps \
        --rm \
        --volume "{{ justfile_directory() }}/data/:/_data/" \
        db pg_restore \
            --clean \
            --dbname "${DATABASE_URL:=postgres://postgres@db/nominate}" \
            --if-exists \
            --no-owner \
            --verbose \
            /_data/{{ file }}
