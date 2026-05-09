# Developer Environment Setup (Windows)

The instructions here are for Windows development. For macOS/Linux instructions, see [bootstrap.md](bootstrap.md).

## Install your dependencies

On Windows, you'll need to install the following:

* MSYS2 (provides Unix/bash utilities that Just needs)
* Just
* uv
* Rancher Desktop
* Git (for version control)

These instructions provide multiple installation methods for each tool. Choose whichever works best for your setup.

### Important: MSYS2 (Required for Just recipes)

Just requires Unix/bash tools to run recipes. While Git Bash can provide some of these, **MSYS2** provides the complete set including `cygpath`, which Just needs to translate file paths when running bash recipes.

**Install MSYS2:**

Choose one of the following installation methods:

**Option 1: Chocolatey (Recommended for ease)**
```powershell
choco install msys2
```
Chocolatey automatically adds MSYS2 to your PATH during installation.

**Option 2: winget**
```powershell
winget install MSYS2.MSYS2
```
After installation, you'll need to manually add the PATH (see below).

**Option 3: Direct Download**
1. Download from [msys2.org](https://www.msys2.org/) and run the installer
2. Choose the default installation path (`C:\msys64`)
3. Complete the installation

**Manual PATH Configuration (if not using Chocolatey):**

If Chocolatey didn't automatically configure your PATH, add MSYS2 manually:

1. Open "Edit the system environment variables" in Windows
2. Click "Environment Variables"
3. Under "System variables", select "Path" and click "Edit"
4. Click "New" and add: `C:\msys64\usr\bin`
5. Click OK and close the dialogs
6. Restart your terminal/PowerShell for PATH changes to take effect

**Verify MSYS2 is installed:**
```powershell
cygpath --version
bash --version
```

### Installation Methods

You can install Just, uv, and Git using one of the following package managers:

- **[Chocolatey](https://chocolatey.org/)** - A Windows package manager (requires admin privileges)
- **[Windows Package Manager (winget)](https://github.com/microsoft/winget-cli)** - Microsoft's modern package manager
- **Direct downloads** - Manual installation from official websites

- Just

    [Just](https://just.systems/) is a task runner; it uses a Justfile to describe steps to run, and we use it here to manage the setup and development processes.

    **Option 1: Chocolatey**
    ```powershell
    choco install just
    just --version
    ```

    **Option 2: winget**
    ```powershell
    winget install Casey.Just
    just --version
    ```

    **Option 3: Cargo (if you have Rust installed)**
    ```powershell
    cargo install just
    ```

    **Option 4: Direct Download**
    Download the latest release from [just releases](https://github.com/casey/just/releases) and add it to your PATH.

- uv

    uv is a Python package and project manager. It's faster and easier to use than pip and virtualenv.

    **Option 1: Chocolatey**
    ```powershell
    choco install uv
    uv --version
    ```

    **Option 2: winget**
    ```powershell
    winget install Astral-sh.uv
    uv --version
    ```

    **Option 3: Direct from Python**
    ```powershell
    pip install uv
    ```

    **Option 4: Direct Download**
    Download from [astral.sh/uv](https://astral.sh/uv/) and add to your PATH.

- Git

    Git is required for version control. If you haven't installed it yet:

    **Option 1: Chocolatey**
    ```powershell
    choco install git
    ```

    **Option 2: winget**
    ```powershell
    winget install Git.Git
    ```

    **Option 3: Direct Download**
    Download from [git-scm.com](https://git-scm.com/download/win)

- Rancher Desktop

    [Rancher Desktop](https://rancherdesktop.io/) is a lightweight container management tool for Windows that provides Docker/containerd and Kubernetes. We use it to run the local PostgreSQL, Redis, and mailcatcher components used in testing and locally running the site.

    **Installation Options:**

    **Option 1: Chocolatey**
    ```powershell
    choco install rancher-desktop
    ```

    **Option 2: winget**
    ```powershell
    winget install Suse.RancherDesktop
    ```

    **Option 3: Direct Download**
    Download from [rancherdesktop.io](https://rancherdesktop.io/)

    **Important Setup Steps:**
    1. Download and install [Rancher Desktop](https://rancherdesktop.io/)
    2. Start Rancher Desktop (you can find it in your Start menu or by searching for "Rancher Desktop")
    3. Wait for it to fully initialize (this may take a few minutes on first start)
    4. Open PowerShell as Administrator and verify installation:
       ```powershell
       docker --version
       docker compose version
       ```

    Rancher Desktop can be configured to start automatically with Windows. You can enable this in Rancher Desktop preferences under "General" → "Start Rancher Desktop when you log in".

    !!! note
        Rancher Desktop requires either WSL 2 or Hyper-V. Most Windows 10/11 systems have WSL 2 available by default. If you encounter issues, consult the [Rancher Desktop installation guide](https://docs.rancherdesktop.io/getting-started/installation).

    **Rancher Desktop vs Docker Desktop:**
    - Rancher Desktop is open-source and free
    - Lower resource overhead than Docker Desktop
    - Supports both containerd and Docker APIs
    - Includes optional Kubernetes support (not required for this project)
    - Works well with WSL 2

## Bootstrap Your Development Environment

Once you have all the dependencies installed and Docker Desktop is running, you can bootstrap your development environment:

```powershell
just bootstrap
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

```powershell
# Create a complete election with default settings
uv run manage.py seed_all my-election "My Test Election"

# Quick mode: smaller dataset (20 nominators, 30 voters)
uv run manage.py seed_all my-election "My Test Election" --quick

# Full mode: larger dataset (200 nominators, 300 voters)
uv run manage.py seed_all my-election "My Test Election" --full

# Clear existing data before seeding
uv run manage.py seed_all my-election "My Test Election" --clear
```

### Individual Commands

For granular control, use these commands in order:

1. **Create Election and Categories**:
   ```powershell
   uv run manage.py seed_election my-election "My Test Election"
   ```

2. **Generate Nominations** (creates members and their nominations):
   ```powershell
   uv run manage.py seed_nominations my-election --count 50
   ```

3. **Canonicalize Nominations** (group similar nominations):
   ```powershell
   uv run manage.py seed_canonicalizations my-election
   ```

4. **Create Finalists** (select top nominated works):
   ```powershell
   uv run manage.py seed_finalists my-election --count 6
   ```

5. **Generate Votes** (create ranked ballots):
   ```powershell
   uv run manage.py seed_ranks my-election --count 100 --new-members
   ```

### Useful Flags

- `--clear`: Remove existing data before seeding
- `--count N`: Specify number of members/voters to create
- `--quick` / `--full`: Preset dataset sizes (for `seed_all`)
- `--new-members`: Create new voters instead of reusing existing members
- `--categories "Category Name"`: Limit to specific categories

## Resetting Your Environment

To completely reset your development database:

```powershell
just down      # Stop and remove Docker containers
just bootstrap # Rebuild from scratch
```

## Running the Development Server

After bootstrapping, start the development server:

```powershell
just serve
```

The site will be available at `http://localhost:8000/` (or the port configured in your `.env` file).

## Viewing Emails

All emails sent by the application are captured by Mailcatcher. To view them:

```powershell
just mailcatcher
```

This opens Mailcatcher's web interface in your browser.

## Required Unix Utilities

Just recipes in this project require several Unix/bash utilities. These are all provided by **MSYS2**:

**Core tools:**
- `bash` - Shell interpreter for Just recipes
- `cygpath` - Converts Windows paths to Unix paths (required by Just)
- `sed` - Stream editor for text manipulation
- `find` - File search utility
- `cut` - Text column extraction

**Used by specific recipes:**
- `rm` - Remove files
- `ls` - List files  
- `python`/`python3` - Python interpreter

MSYS2 provides all of these tools. Make sure `C:\msys64\usr\bin` is in your PATH as described above.

## Troubleshooting

### Admin Privileges Required for Docker

Rancher Desktop on Windows requires elevated (Administrator) privileges to run Docker commands. If you see errors like "Access is denied" or "docker client must be run with elevated privileges":

**Solution:**
1. Open PowerShell as Administrator:
   - Right-click on PowerShell and select "Run as administrator"
   - Or search for "PowerShell" in the Start menu, right-click and select "Run as administrator"
2. Navigate to your project directory: `cd C:\Users\chris\projects\nomnom`
3. Run `just bootstrap` again

Alternatively, you can configure Rancher Desktop to not require admin:
- Open Rancher Desktop
- Go to Preferences → General
- Look for "Docker Socket" or "Privileged" settings and adjust as needed

### `cygpath` command not found or Could not find cygpath executable

This is the most common Windows issue with Just. The error occurs when Just can't find the `cygpath` utility needed to translate file paths for bash recipes.

**Solution:**
1. Install MSYS2 from [msys2.org](https://www.msys2.org/)
2. Add `C:\msys64\usr\bin` to your Windows PATH:
   - Open "Edit the system environment variables"
   - Click "Environment Variables"
   - Under "System variables", select "Path" and click "Edit"
   - Click "New" and add: `C:\msys64\usr\bin`
   - Click OK and restart PowerShell
3. Verify installation: `cygpath --version`
4. Try running `just bootstrap` again

If using Git Bash instead of MSYS2, you may not have `cygpath` available. Install MSYS2 for full compatibility.

### Docker Containers Not Running (subprocess.CalledProcessError)

If you see an error like `Command 'docker compose port 'db' 5432' returned non-zero exit code 1`:

This means the Docker containers failed to start. Common causes:

1. **PowerShell not running as Administrator** - Rancher Desktop requires admin privileges
   - Open PowerShell as Administrator (right-click → "Run as administrator")
   - Run `just bootstrap` again

2. **Rancher Desktop not fully initialized** - First-time startup takes time
   - Wait 2-3 minutes after starting Rancher Desktop
   - Check the Rancher Desktop window to see if initialization is complete
   - Then try `just bootstrap` again

3. **Docker socket issues** - Try restarting Rancher Desktop:
   - Close Rancher Desktop completely
   - Wait 30 seconds
   - Start Rancher Desktop again
   - Wait for full initialization before running `just bootstrap`

4. **Verify Docker is working:**
   ```powershell
   docker --version
   docker compose ps
   ```

### Docker Commands Not Recognized

If you see "docker is not recognized" errors:
1. Ensure Rancher Desktop is actually running (check the system tray or taskbar)
2. Open a new PowerShell window after Rancher Desktop fully starts
3. Restart your terminal if you installed Rancher Desktop after opening it
4. Rancher Desktop takes time to initialize on first start - wait a few minutes before trying docker commands

### Permission Denied with Chocolatey

Run PowerShell as Administrator (right-click → "Run as administrator") when installing packages with Chocolatey.

### Just or uv Commands Not Found

After installing with a package manager, you may need to:
1. Restart your terminal
2. Add the installation directory to your PATH
3. If using Chocolatey, run `refreshenv` in PowerShell to refresh environment variables

### WSL vs Rancher Desktop Backends

Rancher Desktop uses WSL 2 by default on Windows 11 and newer systems. If you're using Windows 10 or prefer a different setup, you can configure this in Rancher Desktop preferences under "General" → "Container Runtime". Rancher Desktop automatically manages the container runtime for you, so minimal additional configuration is usually needed.

### Alternative: Using WSL 2 Instead of MSYS2

If you prefer not to install MSYS2, you can use Windows Subsystem for Linux (WSL 2):

1. Install WSL 2 with Ubuntu: `wsl --install -d Ubuntu`
2. Install Just and other tools in WSL: `sudo apt install just python3-pip`
3. Clone the repository in WSL
4. Install Rancher Desktop with WSL 2 backend support
5. Run `just bootstrap` from within WSL

This approach provides a complete Unix environment, but adds the overhead of running a Linux subsystem.
