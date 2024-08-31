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

On macOS, that means installing copier, uv, and just. For simplicity these
instructions will assume that you have homebrew installed, and follow the
instructions to set your PATH for each tool.

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
    [mise](https://mise.jdx.dev/) but any method will work. When you have it set
    up, you should be able to run this code in the source directory and get
    something vaguely correct:

    ```shellsession
    $ python3.12 --version
    Python 3.12.3
    ```

- [ ] uv

    uv should be in your system package manager; on macOS that's probably homebrew:

    ```shellsession
    $ brew install uv
    ... lots of output
    $ uv -V
    uv 0.3.0 (dd1934c9c 2024-08-20)
    ```

- [ ] Docker compose

    "Installing docker" is also beyond the scope here. You probably want [Docker Desktop](https://www.docker.com/products/docker-desktop/). Once it's installed, this should work:

    ```shellsession
    $ docker compose ps
    NAME                IMAGE               COMMAND                  SERVICE             CREATED             STATUS              PORTS
    ```

#### Generate a test convention

Using copier, create a new convention project:

```shellsession
$ uvx copier copy --trust gh:WorldconVotingSystems/nomnom <your-project-dir>
```

Note the `--trust` flag; that's because the template uses the `_tasks` key,
which runs some postprocessing on the generated template to verify it all works.

Feel free to check out the contents of the copier configuration to make sure
it's safe.
