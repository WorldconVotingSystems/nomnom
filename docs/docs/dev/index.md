# Development

Before you start working on NomNom, read some documents about the project:

* The [NomNom site overview page](https://nomnom.fans)
* The [Contributor Covenant Code of Conduct](https://nomnom.fans/code_of_conduct.html)
* The [getting started page for admins](https://nomnom.fans/admin/getting_started.html)—don’t follow the instructions on that page, just read it to get a sense of the process an admin follows to set up for production.
* The other admin documentation on the NomNom site, to get a sense of how NomNom works for admins.

## Making Changes

The instructions here are for macOS; where appropriate, they'll proffer a Linux equivalent.

!!! info

    Because I don't develop on Windows, I don't have equivalent instructions for setting up there. I would welcome Windows versions of these instructions!

### Install your dependencies

On macOS, that means installing the following:

* Just
* gsed
* Python 3.12 (ideally using mise)
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

    uv is a Python package and project manager.

    ```shellsession
    $ brew install uv
    ... lots of output
    $ uv -V
    uv 0.3.0 (dd1934c9c 2024-08-20)
    ```

- [ ] Docker compose

    "Installing Docker" is also beyond the scope here. You probably want [Docker Desktop](https://www.docker.com/products/docker-desktop/). Once it's installed and running, this should work:

    ```shellsession
    $ docker compose ps
    NAME                IMAGE               COMMAND                  SERVICE             CREATED             STATUS              PORTS
    ```

### Generate a test convention

Create a new directory to put your test convention in. It doesn't have to be inside your nomnom directory.

Then, using copier, create a new convention project:

```shellsession
$ uvx copier copy --trust gh:WorldconVotingSystems/nomnom <your-project-dir>
```

Note the `--trust` flag; that's because the template uses the `_tasks` key,
which runs some postprocessing on the generated template to verify it all works.

Feel free to check out the contents of the copier configuration to make sure
it's safe.

As part of the convention creation process, copier asks you a series of setup
questions, including the name and URL of the convention. You can accept all of
the default values provided—you don't need to (for example) provide a real
domain name.

When copier finishes, it outputs a series of further steps to follow to
set up and run NomNom.

## Contributing

All contributions should be made through pull requests (yes, I'm a bit of a hypocrite in that regard, as I do frequently develop on `main`. Nevertheless.)

PRs should pass all CI processes currently in place.

## Releases

Releases are done by creating a GitHub release, named for the version. NomNom uses [CalVer](https://calver.org/), although I'm leaning towards [PrideVer](https://pridever.org/). Time will tell.
