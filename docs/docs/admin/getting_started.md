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

The `just bootstrap` command will set up your development environment with:

- A complete test election ("The Yugo Awards")
- 21 Hugo Award categories
- Test users including an admin account
- Sample nominations, finalists, and votes

You can log into the admin interface at `http://localhost:8000/admin/` with:
- Username: `admin`
- Password: `admin`

# Setting Up Your First Election

Once your environment is running, you'll need to create your convention's election. There are two approaches:

## Option 1: Using Management Commands (Recommended for Development)

For development and testing, you can use the built-in seeding commands to create a fully-populated election:

```shellsession
# Create a complete election with realistic test data
$ uv run manage.py seed_all worldcon-2026 "Worldcon 2026 Hugo Awards"

# Or with more control over dataset size:
$ uv run manage.py seed_all worldcon-2026 "Worldcon 2026 Hugo Awards" --quick  # Small dataset
$ uv run manage.py seed_all worldcon-2026 "Worldcon 2026 Hugo Awards" --full   # Large dataset
```

This creates:
- An election with all Hugo Award categories
- Test members with nominations (including realistic variations and typos)
- Canonicalized works grouped from nominations
- Finalists selected from top-nominated works
- Ranked voting ballots

## Option 2: Manual Setup via Django Admin (Production)

For production use, you'll set up your election through the Django admin interface:

### Step 1: Create the Election

1. Navigate to `http://your-site.com/admin/`
2. Log in with your admin credentials
3. Click on **Elections** under the NOMINATE section
4. Click **Add Election** button
5. Fill in the required fields:
   - **Slug**: URL-friendly identifier (e.g., `worldcon-2026`)
   - **Name**: Display name (e.g., "Worldcon 2026 Hugo Awards")
   - **Year**: Convention year
6. Save the election

### Step 2: Add Categories

You can add categories in two ways:

**A. Using the seed_election command** (faster for standard Hugo categories):

```shellsession
$ uv run manage.py seed_election worldcon-2026 "Worldcon 2026 Hugo Awards"
```

This automatically creates all 21 official Hugo Award categories with proper field definitions.

**B. Manually through the admin interface**:

1. In the admin, click on **Categories** under NOMINATE
2. Click **Add Category**
3. Fill in the category details:
   - **Election**: Select your election
   - **Name**: Category name (e.g., "Best Novel")
   - **Description**: Category description for voters
   - **Ballot Position**: Display order (1, 2, 3, etc.)
   - **Fields**: Number of fields (1-3)
     - 1 field: Typically for single items (e.g., "Best Series")
     - 2 fields: Work + Creator (e.g., "Title, Author")
     - 3 fields: Work + Creator + Publisher/Source
   - **Field Descriptions**: Labels for each field
   - **Required Fields**: Which fields are mandatory
4. Save and repeat for all categories

### Step 3: Configure Permissions

You'll need to set up user permissions for your convention members:

**A. Verify Permission Groups** (one-time setup):

This should be achieved by the seed data.

## Clearing Test Data

```shellsession
# For development: reset everything
$ just resetdb
$ just bootstrap
```

**Important**: Always back up your database before clearing data in production!

## Next Steps

After setting up your election:

- Configure email settings for member communications
- Set up OAuth/SSO integration if using external authentication
- Review the [Nomination Phase](nomination.md) documentation
- Review the [Canonicalization](canonicalization.md) process
- Review the [Voting Phase](voting.md) documentation

# Deployment Guidance

## Docker

## Others

TBD; thus far Docker has been the only deployment model.
