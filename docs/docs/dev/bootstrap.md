# Developer Environment Setup

The instructions here are for macOS; where appropriate, they'll proffer a Linux equivalent.

!!! info

    Because I don't develop on Windows, I don't have equivalent instructions for setting up there. I would welcome Windows versions of these instructions!

## Install your dependencies

On macOS, that means installing the following:

* Just
* gsed
* uv
* Docker (with the compose addon)

For simplicity, these instructions assume that you have Homebrew installed. After installing each tool,
set your PATH appropriately as needed.

- [ ] Just

    [Just](https://just.systems/) is a task runner; it uses a Justfile to describe steps to run, and I
    use it here to manage the setup and development processes.

    Install it from your package manager:

    ```shellsession
    $ brew install just
    $ just --version
    just 1.16.0
    ```

- [ ] gsed

    gsed is required on MacOS to run several scripts that bootstrap the Python environment. Linux environments are fine with just sed.

    ```shellsession
    $ brew install gnu-sed
    $ gsed --version
    gsed (GNU sed) 4.9
    ```

- [ ] uv

    uv is a Python package and project manager.

    ```shellsession
    $ brew install uv
    ... lots of output
    $ uv -V
    uv 0.6.6 (c1a0bb85e 2025-03-12)
    ```

- [ ] Docker compose

    "Installing Docker" is beyond the scope of this document. You probably want [Docker Desktop](https://www.docker.com/products/docker-desktop/). Once it's installed and running, this should work:

    ```shellsession
    $ docker compose ps
    NAME                IMAGE               COMMAND                  SERVICE             CREATED             STATUS              PORTS
    ```

    For most of the development process, Docker is only used to run the local PostgreSQL, Redis, and mailcatcher components used in testing and locally running the site.
