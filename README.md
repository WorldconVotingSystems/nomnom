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

Production installations are more complex than development, but the easiest way is probably with Docker. The template project will have a suitable Dockerfile included in it, which you can use to build the web and worker images. An example production docker-compose can be found in the `WorldconVotingSystems/nomnom-g24/` repository.

### Development

See [the developer docs](docs/docs/dev/index.md).

## Build Status

[![Python application](https://github.com/WorldconVotingSystems/nomnom/actions/workflows/python-app.yml/badge.svg)](https://github.com/WorldconVotingSystems/nomnom/actions/workflows/python-app.yml)
[![Docker](https://github.com/WorldconVotingSystems/nomnom/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/WorldconVotingSystems/nomnom/actions/workflows/docker-publish.yml)
[![Documentation](https://github.com/WorldconVotingSystems/nomnom/actions/workflows/docs.yml/badge.svg)](https://github.com/WorldconVotingSystems/nomnom/actions/workflows/docs.yml)
