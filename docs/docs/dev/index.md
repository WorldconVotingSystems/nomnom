# Development

Before you start working on NomNom, read some documents about the project:

* The [NomNom site overview page](https://nomnom.fans)
* The [Contributor Covenant Code of Conduct](https://nomnom.fans/code_of_conduct.html)
* The [getting started page for admins](https://nomnom.fans/admin/getting_started.html)—don’t follow the instructions on that page, just read it to get a sense of the process an admin follows to set up for production.
* The other admin documentation on the NomNom site, to get a sense of how NomNom works for admins.

## Making Changes

First, [set up your developer environment](./bootstrap.md)

From there you have two choices:

1. Use the built in development convention. It is bare bones visually, but has all of the NomNom features enabled, and is ready to iterate on

2. Create a test convention and work on that, using source links to integrate nomnom changes as you work.

Option 1 is probably easiest, but option 2 gives you a slightly more faithful replica of a real convention instance.

### Option 1: NomNomCon

First, run the one-time setup steps; these only need to be done the first time you set this up, _or_ if you clean up the dev site:

```shellsession
$ just dev-env
$ just dev-bootstrap
docker compose up --wait
[+] Building 0.0s (0/0)                                                                   docker:orbstack
[+] Running 3/3
 ✔ Container nomnom-mailcatcher-1  Healthy                                                           0.0s
 ✔ Container nomnom-redis-1        Healthy                                                           0.0s
 ✔ Container nomnom-db-1           Healthy                                                           0.0s
uv run manage.py migrate
DEBUG (0.001) CREATE EXTENSION IF NOT EXISTS pg_trgm;; args=None; alias=default

...much SQL and seeding follows
```

Note that `dev-boostrap` will fail if run a second time; the seeds are not 100% idempotent.

Now, you can run the server thusly:

```shellsession
$ just dev-serve
```

That will auto-reload changes as you make them, and reload your web views too, so you can iterate rapidly.

To run the background worker, so that emailing will occur, you can run this:

```shellsession
$ just dev-worker
```

That does _not_ auto-reload; you will need to restart it when you make changes.

If you want to have all of that done for you automatically, without needing to think about it, you can install the optional `overmind` and `entr` binaries, and then just run this:

```shellsession
overmind start
```

That'll run both the worker and the webserver, with restarts based on most code changes.


### Option 2: Generate a test convention

Create a new directory to put your test convention in. It doesn't have to be inside your nomnom directory.

Then, using copier, create a new convention project:

```shellsession
$ uvx copier copy gh:WorldconVotingSystems/nomnom <your-project-dir>
```

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
