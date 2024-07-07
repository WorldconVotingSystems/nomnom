### Development

Development of this system depends on you having four things installed:

* docker (with the compose addon)
* the postgresql command line tool
* python 3.12 (ideally using mise)
* pdm

The instructions here are for macOS; where appropriate, they'll proffer a Linux equivalent.

!!! info

    Regrettably, I don't develop on Windows; I would welcome Windows versions of these instructions!

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
    $ python3.12 --version
    Python 3.12.3
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
