venv_path := justfile_directory() / ".venv"
set dotenv-load := true
os := os()
devcontainer := if env_var_or_default("USER", "nobody") == "vscode" {"true"} else {"false"}
serve_host := if env_var_or_default("CODESPACES", "false") == "true" { "0.0.0.0" } else { "localhost" }

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
    uv run pytest

dist:
    uvx --from build pyproject-build --installer uv
    ls -l dist

upload-test:
    uvx twine upload dist/* --repository testpypi

upload:
    uvx twine upload dist/*

docs:
    uv run mkdocs build -f docs/mkdocs.yml

docs-serve:
    uv run mkdocs serve -f docs/mkdocs.yml

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
