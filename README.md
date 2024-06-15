# NomNom

[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](https://nomnom.fans/code_of_conduct.html)
[![Documentation](https://img.shields.io/badge/Documentation-34D058)](https://nomnom.fans/)

A Hugo Awards ballot and nomination management system.

Developed for the Glasgow in 2024 Worldcon.

## What this Is

The [Hugo Awards](https://www.thehugoawards.org/about/) are "science fiction’s most prestigious award. The Hugo Awards are voted on by members of the World Science Fiction Convention (“Worldcon”), which is also responsible for administering them."

NomNom is a system for collecting the nominations for the award from members of the current Worldcon to assemble a ballot of finalists, and for voting on those finalists [#27](https://github.com/WorldconVotingSystems/nomnom/issues/27).

It additionally will have (these are TODO in the next few months):

* Support for authenticated access to the Hugo packet, if the convention is providing one
* Support for normalizing the nominees into a collection of potential finalists [#86](https://github.com/WorldconVotingSystems/nomnom/issues/86)
* Support for applying a counting algorithm to select a ballot of finalists from the raw nominees, according to the current process defined in Section 3.8 of the WSFS constitution (EPH, for those following along at home)
* Support for tallying the final votes for the Hugo Awards

## Installation

### Production

### Development

See [the developer docs](docs/docs/dev/index.md).

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

## Customization

To customize NomNom, you create an application with your templates and supporting classes. The original convention that used this system was Glasgow in 2024, whose customizations are directly in this repository, but yours should be a separate installable package.

Your main customizations should be CSS and template overrides. CSS should be in `$APP/static/css/` and you'll reference it by changing the `NOMNOM_SITE_STYLESHEET` setting.

## Build Status

[![Python application](https://github.com/WorldconVotingSystems/nomnom/actions/workflows/python-app.yml/badge.svg)](https://github.com/WorldconVotingSystems/nomnom/actions/workflows/python-app.yml)
[![Docker](https://github.com/WorldconVotingSystems/nomnom/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/WorldconVotingSystems/nomnom/actions/workflows/docker-publish.yml)
[![Documentation](https://github.com/WorldconVotingSystems/nomnom/actions/workflows/docs.yml/badge.svg)](https://github.com/WorldconVotingSystems/nomnom/actions/workflows/docs.yml)
