# NomNom

A Hugo Awards ballot and nomination management system.

Developed for the Glasgow in 2024 Worldcon.

## Installation

### Production

### Development

Development of this system depends on you having four things installed:

* docker (with the compose addon)
* the postgresql command line tool
* python 3.11 (ideally using pyenv or asdf)
* pdm

The instructions here are for macOS; where appropriate, they'll proffer a Linux equivalent.

> [!NOTE]
> Regrettably, I don't develop on Windows; I would welcome Windows versions of these instructions!

#### Install your dependencies

On macOS, that means

- [ ] Just

    [Just](https://just.systems/) is a task runner; it uses a Justfile to describe steps to run, and I
    use it here to manage the setup and development processes.

    Install it from your package manager:

    ```shellsession
    $ brew install just
    $ just --version
    just 1.16.0
    ```

- [ ] Python

    "How to install Python" is beyond the scope of this README, sorry; I use
    [asdf](https://asdf-vm.com/) but any method will work. When you have it set
    up, you should be able to run this code in the source directory and get
    something vaguely correct:

    ```shellsession
    $ python3.11 --version
    Python 3.11.6
    ```
- [ ] PDM

    PDM should be in your system package manager; on macOS that's probably homebrew:

    ```shellsession
    $ brew install pdm
    ... lots of output
    $ pdm -V
    PDM, version 2.10.4
    ```

- [ ] Docker compose

    "Installing docker" is also beyond the scope here. You probably want [Docker Desktop](https://www.docker.com/products/docker-desktop/). Once it's installed, this should work:

    ```shellsession
    $ docker compose ps
    NAME                IMAGE               COMMAND                  SERVICE             CREATED             STATUS              PORTS
    ```

- [ ] PostgreSQL command line

    This is used during database setup, to wait for the DB to be available; it
    lets you use the database setup helpers during development.

    ```shellsession
    $ pg_isready -V
    pg_isready (PostgreSQL) 16.1
    ```

#### Set up the system

If you've installed all of the dependencies above, then all you need to get started is this command:

``` shellsession
$ just get_working
```

This will set up your development database, populate some initial users for development, and set up a Hugo election to experiment with.

If you stop the service after that, you can run the server again using:

``` shellsession
$ just serve
```

If you want to start over from a brand new database, removing all of your test data:

``` shellsession
$ just nuke
$ just serve
```

### Codespaces

If you are using this from a codespace, here's what you need to do to get started, in the codespace terminal:

``` shellsession
$ scripts/bootstrap-codespaces.sh
$ just get_started
$ just serve
```

## Configuration

To configure the system for your side, you need to take a couple of extra steps beyond just "build the docker image and go".

### Docker Build

Your docker file should refer to the nomnom one, but build on top of it:

``` dockerfile
FROM ghcr.io/worldconvotingsystems/nomnom:latest

WORKDIR /system

RUN . venv/bin/activate && \
    pip install <your-app>
```

### Environment

The environment is the heart of the configuration; it needs to include both the services you will interact with, and references to the site customization.

Here's an example file:

``` shell
NOM_DEBUG=False

NOM_CONVENTION_APP=yourconvention
NOM_CONVENTION_STYLE_STYLESHEET=css/yourconvention.css
NOM_CONVENTION_STYLE_FONT_URL=https://fonts.googleapis.com/css2?family=Roboto&family=Roboto+Slab&family=Gruppo&display=swap
NOM_CONVENTION_HUGO_HELP_EMAIL=nominations@nomnom.nom

NOM_SECRET_KEY=random-string-that-you-generate
NOM_DB_NAME=nominate
NOM_DB_USER=postgres
NOM_DB_PASSWORD=random-string-that-you-generate
NOM_DB_HOST=db
NOM_DB_PORT=5432

NOM_REDIS_HOST=redis

NOM_EMAIL_HOST_USER=nominations@nomnom.nom
NOM_EMAIL_HOST_PASSWORD=random-string-that-you-generate
NOM_EMAIL_HOST=mail.nomnom.nom
NOM_EMAIL_PORT=587

NOM_ALLOWED_HOSTS=nominations.nomnom.nom

NOM_OAUTH_KEY=provided-by-your-oauth-vendor
NOM_OAUTH_SECRET=provided-by-your-oauth-vendor

TIME_ZONE=America/Los_Angeles

CELERY_FLOWER_USER=admin
CELERY_FLOWER_PASSWORD=random-string-that-you-generate
```

### Settings

All settings customization is through the environment, or through a
`settings_override.py` that can be installed in
`/app/nomnom/settings_override.py`; that file will be loaded after the main site
settings have been configured from the environment and can overwrite any
settings in the application.

## Administration
