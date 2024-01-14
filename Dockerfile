# Base this on Debian Bookworm + Python 3.11
FROM python:3.11-bookworm AS os

RUN apt-get update \
  && apt-get install -y --no-install-recommends build-essential libpq-dev redis postgresql gettext curl jq \
  && rm -rf /var/lib/apt/lists/*

# Configure the application user and prepare our directories.
# --create-home is a nicety that allows us to use devcontainers
# effectively. It is otherwise unnecessary.
RUN useradd -U app_user \
    --create-home \
    && install -d -m 0755 -o app_user -g app_user /app \
    && install -d -m 0755 -o app_user -g app_user /system \
    && install -d -m 0755 -o app_user -g app_user /staticfiles

VOLUME /staticfiles

FROM os AS build

# Ensure we create a clean install with no bytecode cruft
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN pip install -U pip
RUN pip install pdm

# Initialize the project virtualenv
RUN python -mvenv /system/venv

# Copy the project files
COPY pyproject.toml pdm.lock /system

# install dependencies and project
WORKDIR /system
RUN . venv/bin/activate && \
    pdm install --prod --no-lock --no-editable --no-self

FROM os AS run

WORKDIR /app

COPY . /app

COPY --from=build /system /system

# used in devcontainer
COPY --from=build /home/app_user /home/app_user

RUN chown -R app_user:app_user /app/*/locale/zh/LC_MESSAGES

USER app_user:app_user

ENTRYPOINT ["/app/docker/entrypoint.sh"]
