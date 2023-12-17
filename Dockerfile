# Base this on Debian Bookworm + Python 3.11
FROM python:3.11-bookworm AS os

RUN apt-get update \
  && apt-get install -y --no-install-recommends build-essential libpq-dev redis postgresql \
  && rm -rf /var/lib/apt/lists/*

# Configure the application user and prepare our directories
RUN useradd -U app_user \
    && install -d -m 0755 -o app_user -g app_user /app/static

FROM os AS build

# Ensure we create a clean install with no bytecode cruft
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN pip install -U pip
RUN pip install pdm

# Initialize the project virtualenv
RUN python -mvenv /app/venv

# Copy the project files
COPY pyproject.toml pdm.lock /app

# install dependencies and project
WORKDIR /app
RUN . venv/bin/activate && \
    pdm install --prod --no-lock --no-editable --no-self

FROM os AS run

WORKDIR /app

USER app_user:app_user

COPY . /app

COPY --from=build /app/venv /app/venv

ENTRYPOINT docker/entrypoint.sh
