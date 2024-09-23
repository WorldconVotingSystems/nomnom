---
title: Starting a New Convention
---

NomNom is not intended to be run as a standalone application; it is intended to act as a supporting library for your awards site, which will be generated from a template (FIXME: add this template doc here).

Each new convention will perform a one-time process of starting off their site at the current version of NomNom: (FIXME: Version here).

# Creating a new NomNom instance

This set of steps will result in the creation of a new repository with the necessary configuration for starting your custom NomNom instance.

## Install system tools to support development

NomNom is written in [Python](https://python.org) and uses [uv](https://astral.sh/uv) as a development tool, along with [just](https://just.systems/) to simplify repetitive tasks. To get started, follow the `uv` installation instructions, and then the below steps to get your new NomNom set up. This is generally a one-time process; after this, you will update NomNom using standard `uv`/`python` upgrade processes.

All of these steps will assume that you are using `~/projects/nomcon-2025` as your working directory and that your convention is "NomCon 2025"

### Create a project from the template

```shellsession
$ uvx copier copy gh:WorldconVotingSystems/nomnom ~/projects/nomcon-2025
🎤 convention_name
   NomCon 2025
🎤 This will be used in places where the project name needs to be referenced in code, but not as an identi
   nomcon-2025
🎤 The convention website URL
   nomcon-2025.org
🎤 The email domain name, if different
   nomcon-2025.org
🎤 Will your convention enable advisory votes? This updates nomcon_2025_app/convention.py to configure the
   Yes
🎤 hugo_packet_enabled (bool)
   Yes
🎤 Whether to use the checked out version of nomnom
   No
```

### After Setup

Your convention site NomCon 2025 is now set up; the template output will include some instructions that you need to follow next, while working in the new project:

```shellsession
$ cd ~/projects/nomcon-2025
# Set up your development Python and your dependencies
$ uv sync --dev
# Configure your web application ports for local development. This is so that nomnom doesn't collide with any existing ports you use, but still offers local connections to the db and redis and webserver.
$ scripts/get_web_port.sh
```

### Commit the template output

Commit the final template code to your source control system, so that you can easily revert any future changes.

### Set up your development environment (`.env`) with local ports and credentials

```shellsession
$ just resetdb  # note -- this will DELETE ALL YOUR DEVELOPMENT DATA, skip it if you're not sure.
$ just bootstrap
```

# Deployment Guidance

## Docker

## Others

TBD; thus far Docker has been the only deployment model.
