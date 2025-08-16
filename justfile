venv_path := justfile_directory() / ".venv"
set dotenv-load := true
os := os()
devcontainer := if env_var_or_default("USER", "nobody") == "vscode" {"true"} else {"false"}
serve_host := if env_var_or_default("CODESPACES", "false") == "true" { "0.0.0.0" } else { "localhost" }

export DEV_SERVER_PORT := env_var_or_default("DEV_SERVER_PORT", "8000")

default:
    @just --choose

clean: clean-build clean-test

clean-build:
    rm -rf build/
    rm -rf dist/
    rm -rf .eggs/
    find . -name '*.egg-info' -exec rm -rf {} +
    find . -not -path './.venv/*' -name '*.egg' -exec rm -f {} +

clean-test:
    rm -f .coverage
    rm -fr htmlcov/
    rm -fr .pytest_cache

lint:
    uv run ruff check
    uv run ruff format --check

lint-fix:
    uv run ruff check --fix
    uv run ruff format

test:
    uv run pytest -s

profile:
    uv run pytest --profile --strip-dirs

dist:
    uvx --from build pyproject-build --installer uv
    ls -l dist

upload-test:
    uvx twine upload dist/* --repository testpypi

upload:
    uvx twine upload dist/*

docs:
    uv run mkdocs build -f docs/mkdocs.yml

dev-bootstrap: dev-environment-check dev-services dev-migrate dev-seed

dev-env:
    scripts/setup-env.sh

dev-environment-check:
    #!/usr/bin/env bash
    if [ ! -f .env ]; then
        echo "No .env file found; the environment is not set up."
        exit 1
    fi

dev-services:
    docker compose up --wait

dev-migrate:
    uv run manage.py migrate

dev-seed:
    #!/usr/bin/env bash
    set -eu -o pipefail
    shopt -s nullglob

    for seed_file in {{ justfile_directory() }}/seed/all/*.json; do
        uv run manage.py loaddata "$seed_file"
    done

    for seed_file in {{ justfile_directory() }}/seed/dev/*.json; do
        uv run manage.py loaddata "$seed_file"
    done

dev-down:
    docker compose down -v

dev-serve:
    uv run manage.py runserver {{ serve_host }}:$DEV_SERVER_PORT

dev-shell:
    uv run manage.py shell

dev-mailcatcher:
    open "http://localhost:$(docker compose port mailcatcher 1080 | cut -d: -f2)"

docs-serve:
    uv run mkdocs serve -f docs/mkdocs.yml

makemigrations:
    uv run manage.py makemigrations

template_test:
    #!/usr/bin/env bash
    # unset every environment variable that starts with NOM_
    for var in $(compgen -A variable | grep "^NOM_"); do
        unset $var
    done

    # unset COMPOSE_FILE so we don't accidentally use it
    unset COMPOSE_FILE

    # hopefully you're not using this ;)
    rm -rf ~/tmp/nomnom-gen

    copier copy --defaults \
      --data 'use_development=true' \
      --data 'development_path={{ justfile_directory() }}' \
      --vcs-ref=HEAD \
      . ~/tmp/nomnom-gen/

    cd ~/tmp/nomnom-gen

    uv venv
    uv sync

    just resetdb bootstrap

    just serve || echo "serve failed"

update_template:
    #!/usr/bin/env bash
    # unset every environment variable that starts with NOM_
    for var in $(compgen -A variable | grep "^NOM_"); do
        unset $var
    done

    # unset COMPOSE_FILE so we don't accidentally use it
    unset COMPOSE_FILE

    copier copy --defaults --overwrite --vcs-ref=HEAD . ~/tmp/nomnom-gen/

update:
    uvx gha-update
    uvx --with pre-commit-uv pre-commit autoupdate -j3
    uv sync --upgrade
