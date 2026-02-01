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

## Bootstrap Your Development Environment

Once you have all the dependencies installed, you can bootstrap your development environment:

```shellsession
$ just bootstrap
```

This command will:

1. Check for the `.env` file (creates it if missing)
2. Start Docker services (PostgreSQL, Redis, Mailcatcher)
3. Collect static files
4. Run database migrations
5. Load initial fixture data
6. Seed a complete test election with realistic data

### What Gets Created

The `just bootstrap` command creates a complete test election called "The Yugo Awards" with:

- **Election & Categories**: 21 official Hugo Award categories with proper field definitions
- **Test Users**: Admin user (username: `admin`, password: `admin`) and test members
- **Nominations**: 100 members with realistic nomination variations and typos
- **Canonicalizations**: Grouped nominations into works
- **Finalists**: Top 6 nominated works per category, plus "No Award"
- **Votes**: 50 members with ranked ballots

You can access the admin interface at `http://localhost:8000/admin/` using the admin credentials.

## Manual Seeding Commands

If you need more control over the test data, you can use individual seeding commands:

### Quick Start: All-in-One Command

```shellsession
# Create a complete election with default settings
$ uv run manage.py seed_all my-election "My Test Election"

# Quick mode: smaller dataset (20 nominators, 30 voters)
$ uv run manage.py seed_all my-election "My Test Election" --quick

# Full mode: larger dataset (200 nominators, 300 voters)
$ uv run manage.py seed_all my-election "My Test Election" --full

# Clear existing data before seeding
$ uv run manage.py seed_all my-election "My Test Election" --clear
```

### Individual Commands

For granular control, use these commands in order:

1. **Create Election and Categories**:
   ```shellsession
   $ uv run manage.py seed_election my-election "My Test Election"
   ```

2. **Generate Nominations** (creates members and their nominations):
   ```shellsession
   $ uv run manage.py seed_nominations my-election --count 50
   ```

3. **Canonicalize Nominations** (group similar nominations):
   ```shellsession
   $ uv run manage.py seed_canonicalizations my-election
   ```

4. **Create Finalists** (select top nominated works):
   ```shellsession
   $ uv run manage.py seed_finalists my-election --count 6
   ```

5. **Generate Votes** (create ranked ballots):
   ```shellsession
   $ uv run manage.py seed_ranks my-election --count 100 --new-members
   ```

### Useful Flags

- `--clear`: Remove existing data before seeding
- `--count N`: Specify number of members/voters to create
- `--quick` / `--full`: Preset dataset sizes (for `seed_all`)
- `--new-members`: Create new voters instead of reusing existing members
- `--categories "Category Name"`: Limit to specific categories

## Resetting Your Environment

To completely reset your development database:

```shellsession
$ just down      # Stop and remove Docker containers
$ just bootstrap # Rebuild from scratch
```

## Running the Development Server

After bootstrapping, start the development server:

```shellsession
$ just serve
```

The site will be available at `http://localhost:8000/` (or the port configured in your `.env` file).

## Viewing Emails

All emails sent by the application are captured by Mailcatcher. To view them:

```shellsession
$ just mailcatcher
```

This opens Mailcatcher's web interface in your browser.
