# syntax=docker/dockerfile:1.7-labs
FROM python:3.12-bookworm AS os

RUN apt-get update \
  && apt-get install -y --no-install-recommends bash redis postgresql gettext curl jq \
  && rm -rf /var/lib/apt/lists/*

# Configure the application user and prepare our directories
RUN useradd -U app_user -d /app -M \
    && install -d -m 0755 -o app_user -g app_user /app \
    && install -d -m 0755 -o app_user -g app_user /app \
    && install -d -m 0755 -o app_user -g app_user /staticfiles

VOLUME /staticfiles

FROM os AS build

# Ensure we create a clean install with no bytecode cruft
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Initialize the project virtualenv
wORKDIR /app
RUN uv venv


# Copy the project files
COPY pyproject.toml pdm.lock /app

# install dependencies and project
WORKDIR /app
RUN . venv/bin/activate && \
    pdm install --prod --frozen-lockfile --no-editable --no-self --check

FROM os AS run

WORKDIR /app

COPY --from=build /app /app

COPY . /app

USER app_user:app_user

EXPOSE 8000

ENTRYPOINT ["/app/docker/entrypoint.sh"]
