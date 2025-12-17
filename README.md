# MetaTrader5 Docker Image (Fork)

This is a fork of the original project by
[gmag11](https://github.com/gmag11/MetaTrader5-Docker-Image).
It provides a Docker image for running MetaTrader5 with remote access via VNC, based on the
[KasmVNC](https://github.com/kasmtech/KasmVNC) project and
[KasmVNC Base Image from LinuxServer](https://github.com/linuxserver/docker-baseimage-kasmvnc).

## What's New in This Fork

### v2.2.x (Latest)

- **Dual Python Architecture**: System Python 3.13 + Wine Python 3.12 for optimal compatibility
- **Poetry Integration**: Modern dependency management with local path dependencies
- **Dependabot Compatibility**: Automatic dependency updates (mt5linux ignored for local dev)
- **Enhanced Testing**: 67 comprehensive tests covering static analysis and runtime validation
- **Production Ready**: Automated dependency setup for different environments

### Core Features

- **Expert Advisor Support**: Windows .NET Framework 4.8 under Wine (Mono removed)
- **Consolidated Scripts**: Single `start.sh` + `setup.sh` for reliable startup
- **Auto-Login**: Environment-based MT5 authentication
- **Health Monitoring**: Auto-recovery for MT5 and RPyC server failures
- **RPyC Bridge**: Bundled standalone bridge from mt5linux
- **OCI Standards**: Modern container metadata and labels
- **Fail-Fast Design**: Immediate exit on critical startup failures

### Technical Improvements

- **Python Versions**: 3.13 (system) + 3.12 (Wine) for numpy/MT5 compatibility
- **Dependency Management**: Poetry with local path dependencies for development
- **Testing Framework**: pytest with comprehensive coverage (static + runtime)
- **GitHub Integration**: Dependabot, automated releases, CI/CD pipeline

## Features

- Run MetaTrader5 in an isolated Docker environment.
- Remote access to MetaTrader5 interface via KasmVNC web browser interface.
- RPyC server for remote Python access using [mt5linux](https://github.com/marlonsc/mt5linux).
- Auto-login with environment variables (no manual login needed).
- Health monitoring with auto-recovery for MT5 terminal and RPyC server.
- Expert Advisors (EAs) support:
  - Optional Windows `.NET Framework 4.8` for .NET-dependent EAs.
  - Full Wine environment for native EA execution.

![MetaTrader5 running inside container and controlled through web browser](https://imgur.com/v6Hm9pa.png)

----------

**NOTICE:**
Due to some compatibility issued, version 2 has switched its base from Alpine to Debian Linux.
This and adding Python environment makes that container size is considerably bigger from about 600 MB to 4 GB.

If you just need to run Metatrader for running your MQL5 programs without any Python programming
I recommend to go on using version 1.0. MetaTrader program is updated independently from image so you will
always have latest MT5 version.

## Project Structure

```bash
mt5docker/
├── docker/                         # Docker-related files
│   ├── Dockerfile                  # Multi-stage build (Python 3.12 for Wine, 3.13 for system)
│   ├── compose.yaml                # Docker Compose configuration
│   ├── versions.env                # Component versions (Wine Python: 3.12, System: 3.13)
│   └── container/                  # Files copied into container
│       ├── Metatrader/            # Startup scripts and services
│       └── root/                  # LinuxServer defaults
├── scripts/                       # Development and setup scripts
│   └── setup-dependencies.sh      # Configure mt5linux dependency (local/git)
├── tests/                         # Test suite (pytest with Poetry)
├── .env                          # Your credentials (gitignored)
├── .github/                       # GitHub configuration
│   └── dependabot.yml            # Dependabot config (ignores mt5linux)
├── pyproject.toml                # Poetry configuration (Python 3.13, mt5linux path dep)
├── poetry.lock                   # Locked dependencies
└── README.md
```

## Requirements

- **Docker**: installed on your machine
- **Architecture**: Only x86_64/amd64 hosts supported
- **Python**: >= 3.13 (system), 3.12 (Wine container)
- **Poetry**: for dependency management (optional, see Makefile)
- **Internet connectivity**: Required on first run (downloads MT5, Wine components, and optional .NET)
- **Environment file**: `.env` with required credentials (see setup below)

## Quick Start with Makefile

For the fastest setup, use the provided Makefile:

```bash
# Clone and setup everything automatically
git clone https://github.com/marlonsc/mt5-docker
cd mt5-docker

# Setup development environment
make setup

# Run tests to verify everything works
make test

# Build and run the container
make build
make run
```

See `make help` for all available commands.

## Development Setup

### Python Version Architecture

This project uses a dual Python version setup:

- **System Python (Linux)**: 3.13+ for mt5linux compatibility and modern tooling
- **Wine Python (Windows)**: 3.12 for numpy 1.26.4 compatibility (MetaTrader5 requirement)

### Dependency Management

The project uses Poetry with local path dependencies for development:

```toml
# pyproject.toml
[tool.poetry.dependencies]
python = ">=3.13,<3.14"        # System Python requirement
mt5linux = { path = "../mt5linux", develop = true }  # Local development
```

For production deployment, use the setup script to configure git dependencies:

```bash
# Automatically detects environment and configures dependencies
./scripts/setup-dependencies.sh
```

### GitHub Integration

- **Dependabot**: Configured to ignore mt5linux updates (uses local version)
- **CI/CD**: Poetry-based testing and linting
- **Releases**: Automated Docker image builds

## Usage from repository

1. Clone this repository:

   ```bash
   git clone https://github.com/marlonsc/mt5-docker
   cd mt5-docker
   ```

2. Build the Docker image:

   ```bash
   docker build -f docker/Dockerfile -t marlonsc/mt5-docker:debian docker/
   ```

3. Run the Docker image:

```bash
docker run -d -p 3000:3000 -p 8001:8001 -v config:/config marlonsc/mt5-docker:debian
```

Now you can access MetaTrader5 via a web browser at localhost:3000.

On first run it may take a few minutes to install MT5, Wine dependencies,
and optionally .NET Framework. Normally it takes less than 10 minutes.
The process is automatic and you should end up with MetaTrader5 running in your web session.

## Usage with docker compose (preferred way)

1. Create a folder in a path where you have permission. For instance in your home.

   ```bash
   mkdir MT5
   cd MT5
   ```

2. Create `docker-compose.yaml` file.

   ```bash
   nano docker-compose.yaml
   ```

   Use this content, optionally adding your MT5 credentials for auto-login.

   ```yaml
   version: '3'

   services:
     mt5:
       image: marlonsc/mt5-docker
       container_name: mt5
       volumes:
         - ./config:/config
       ports:
         - 3000:3000
         - 8001:8001
       environment:
         # Auto-login credentials (optional - can login manually via VNC instead)
         - MT5_LOGIN=your_account_number
         - MT5_PASSWORD=your_password
         - MT5_SERVER=MetaQuotes-Demo
         # Optional features
         - ENABLE_WIN_DOTNET=1   # Install .NET Framework 4.8 for .NET EAs (default: 1)
         - AUTO_RECOVERY_ENABLED=1  # Auto-restart on failures (default: 1)
         - TZ=UTC                # Timezone for logs and MT5
   ```

   .NET Support

   Windows `.NET Framework` inside Wine:
   Installed via `winetricks dotnet48` into `WINEPREFIX=/config/.wine`.
   Enables EAs that depend on .NET Framework when running MT5 under Wine.

   Disable by setting `ENABLE_WIN_DOTNET=0` in compose.

   **Notice**: If you do not need to do remote python programming you can get a much  smaller installation changing this line:

   ```yaml
   image: marlonsc/mt5-docker
   ```

   by this one

   ```yaml
   image: marlonsc/mt5-docker:1.1
   ```

3. Start the container

   ```bash
   docker compose -f docker/compose.yaml up -d
   ```

   In some systems `docker compose` command does not exists. Try to use
    `docker-compose -f docker/compose.yaml up -d` instead.

4. Connect to web interface

   Start your browser pointing http://&lt;your ip address&gt;:3000

   On first run it may take a few minutes to install MT5, Wine dependencies,  andoptionally .NET Framework and should take aprox 5 minutes.
   The process is automatic and you should end up with MetaTrader5 running in your web  session.

## Where to place MQ5 and EX5 files

In the case you want to run your own MQL5 bots inside the container you can find MQL5 folder structure in

```text
config/.wine/drive_c/Program Files/MetaTrader 5/MQL5
```

All files that you place there can be accessed from your MetaTrader container without the need to restart anything.

You can access MetaEditor program clicking in `IDE` button in MetaTrader5 interface.

**Notice**: If you will run MQL5 only bots (without Python) you can run perfectly
with gmag11/metatrader5_vnc:1.0 image as pointed before.
Remember that **image version is not stuck to a specific MetaTrader 5 version**.

**Metatrader will always be updated automatically to latest version as it does when it is nativelly installed in Windows.**

## Python Programming

Install [mt5linux](https://github.com/marlonsc/mt5linux) on your Python host (any OS):

```bash
# From PyPI (recommended for production)
pip install mt5linux

# Or from git (latest development version)
pip install git+https://github.com/marlonsc/mt5linux.git@main
```

**Required library versions:**

- **Python**: >= 3.13 (system), 3.12 (Wine container)
- **mt5linux**: >= 0.6.0 (from main branch)
- **numpy**: >= 1.26.4 (Wine), >= 1.26.4 (system)
- **grpcio**: >= 1.60.0
- **protobuf**: >= 4.25.0

**Example usage (synchronous):**

```python
from mt5linux import MetaTrader5

mt5 = MetaTrader5(host='host-running-docker', port=8001)
mt5.initialize()
print(mt5.version())
```

**Expected output:**

```python
>>> from mt5linux import MetaTrader5
>>> mt5 = MetaTrader5(host='192.168.1.10', port=8001)
>>> mt5.initialize()
True
>>> print(mt5.version())
(500, 4993, '22 Dec 2025')
```

**Example usage (asynchronous):**

For async operations, use `mt5linux.AsyncMetaTrader5` (when available):

```python
import asyncio
from mt5linux import AsyncMetaTrader5

async def main():
    mt5 = AsyncMetaTrader5(host='localhost', port=8001)
    await mt5.initialize()

    # Parallel data fetching (non-blocking)
    account, tick = await asyncio.gather(
        mt5.account_info(),
        mt5.symbol_info_tick("EURUSD"),
    )
    print(f"Balance: {account.balance}, EURUSD: {tick.ask}")

asyncio.run(main())
```

**RPyC 6.x numpy array handling:**

RPyC 6.x blocks `__array__` access for security. Use `rpyc.classic.obtain()` for local copies:

```python
import rpyc
from rpyc.utils.classic import connect

conn = connect('localhost', 8001)
np = conn.modules.numpy

# Create remote array
remote_array = np.array([1, 2, 3])

# Get local copy (required in RPyC 6.x)
local_array = rpyc.classic.obtain(remote_array)
print(local_array)  # [1 2 3]
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| **MT5 Auto-Login** |||
| `MT5_LOGIN` | - | MetaTrader 5 account number |
| `MT5_PASSWORD` | - | Account password |
| `MT5_SERVER` | `MetaQuotes-Demo` | Broker server name |
| **Features** |||
| `AUTO_RECOVERY_ENABLED` | `1` | Auto-restart MT5/RPyC on failures |
| `HEALTH_CHECK_INTERVAL` | `30` | Health check interval (seconds) |
| `ENABLE_WIN_DOTNET` | `1` | Install .NET Framework 4.8 for .NET EAs |
| `MT5_DEBUG` | `1` | Enable debug logging in RPyC bridge |
| `MT5_UPDATE` | `1` | Update MetaTrader5 pip package on startup |
| **Container Settings** |||
| `TZ` | `UTC` | Container timezone |
| `PUID` | `911` | User ID for file permissions (KasmVNC) |
| `PGID` | `911` | Group ID for file permissions (KasmVNC) |
| **Advanced** |||
| `WINEPREFIX` | `/config/.wine` | Wine environment directory |
| `WINEDEBUG` | `-all` | Wine debug output (silent by default) |
| `STAGING_DIR` | `/opt/mt5-staging` | MT5 staging directory |

### Ports

| Port | Protocol | Description |
|------|----------|-------------|
| `3000` | HTTP | KasmVNC web interface (browser access) |
| `8001` | TCP | RPyC service for mt5linux remote control |

### Volumes

| Path | Description |
|------|-------------|
| `/config` | **Required**: Persistent Wine prefix, MT5 data, and settings |
| `/data` | **Optional**: Pre-configured archives for faster startup |

**Volume contents** (`/config`):

- `.wine/` - Wine prefix with MT5 installation
- `.wine/drive_c/Program Files/MetaTrader 5/` - MT5 program files
- `.wine/drive_c/Program Files/MetaTrader 5/MQL5/` - Your EAs, indicators, scripts

### Startup Scripts

The container startup is handled by two consolidated scripts in `docker/container/Metatrader/`:

| Script | Purpose |
|--------|---------|
| `start.sh` | Container entrypoint: configuration, environment setup, orchestration |
| `setup.sh` | All setup operations: Wine prefix init, winetricks, MT5 installation, bridge copy |
| `health_monitor.sh` | Background health monitoring and auto-recovery |

**Setup operations** (performed by `setup.sh`):

- **Config unpack**: Unpack pre-configured Wine prefix if archive exists (<5s)
- **Wine prefix init**: Copy template to /config (<30s)
- **Winetricks**: Install vcrun2019, restore win10 version (30-60s)
- **MT5 pip**: Install MetaTrader5 Python package (<30s)
- **MT5 terminal**: Download and install MT5 terminal (5-10min first run)
- **MT5 config**: Generate auto-login config if credentials provided (<5s)
- **Bridge copy**: Copy bridge.py to Wine Python site-packages (<5s)

**Note**: Python and packages (rpyc, numpy) are pre-installed in Wine at build time. Only MetaTrader5 is installed at runtime to get the
latest version.

### Startup Dependency Categories

Dependencies are categorized by criticality:

| Category | Behavior | Examples |
|----------|----------|----------|
| **REQUIRED** | Fail-fast, exit on failure | Python, MT5, Wine, Gecko |
| **RECOMMENDED** | Warn on failure, continue | vcrun2019, dotnet48 |
| **OPTIONAL** | Debug log if skipped | corefonts, gdiplus, msxml6 |

**Winetricks dependencies** (vcrun2019, corefonts, gdiplus, msxml6, win10):

- All are optional - MT5 can run without them
- Failures are logged as warnings but don't stop startup
- Some EAs may require vcrun2019 or dotnet48

**Python packages** (MetaTrader5, rpyc):

- Required for RPyC server functionality
- Installation is verified before proceeding

### Troubleshooting Startup

If startup fails, check logs for specific error messages:

```bash
docker logs mt5

# Look for [ERROR] tags to find critical failures
docker logs mt5 2>&1 | grep ERROR

# Check health monitor diagnostics
docker logs mt5 2>&1 | grep health
```

## Development & Testing

The project uses Poetry for dependency management and includes comprehensive automated tests using pytest.

### Prerequisites

1. **Install Poetry** (if not already installed):

   ```bash
   curl -sSL https://install.python.org/ | python3 -
   # Or using pip
   pip install poetry
   ```

2. **Install dependencies**:

   ```bash
   # Install all dependencies (including dev dependencies)
   poetry install

   # Or use the setup script (detects environment automatically)
   ./scripts/setup-dependencies.sh
   ```

3. **Configure credentials**: Copy the template file and fill in your credentials:

   ```bash
   cp config.env.template .env
   ```

4. **Edit `.env`** with your required credentials:

   ```bash
   # REQUIRED for production builds
   MT5_LOGIN=your_login_number
   MT5_PASSWORD=your_password
   MT5_SERVER=MetaQuotes-Demo
   VNC_PASSWORD=your_secure_vnc_password

   # Optional settings available in template
   ```

   **⚠️ IMPORTANT**: `MT5_LOGIN`, `MT5_PASSWORD`, and `VNC_PASSWORD` are **mandatory** for builds and runs.

   To create a MetaQuotes Demo account:

   - Open MT5 in the container (`http://localhost:3000`)
   - File → Open an Account → MetaQuotes-Demo
   - Fill in the registration form
   - Copy your login and password to `.env`

### Running Tests

```bash
# Run all tests through Poetry
poetry run pytest tests/ -v

# Run specific test file
poetry run pytest tests/test_static.py -v

# Run specific test class
poetry run pytest tests/test_static.py::TestVersionsEnv -v

# Run with coverage
poetry run pytest tests/ --cov=src --cov-report=html
```

### Test Categories

- **Static Tests** (`test_static.py`): Configuration validation, file checks, no container needed
- **Runtime Tests** (`test_runtime.py`): Container functionality, requires Docker
- **Bridge Tests** (`test_bridge_validation.py`): RPyC bridge validation

### Environment Variables

Test configuration can be overridden via environment variables or `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `MT5_LOGIN` | (required) | MT5 account login |
| `MT5_PASSWORD` | (required) | MT5 account password |
| `MT5_SERVER` | MetaQuotes-Demo | MT5 server name |
| `MT5_CONTAINER_NAME` | mt5docker-test | Test container name |
| `MT5_RPYC_PORT` | 48812 | RPyC service port for tests |
| `MT5_VNC_PORT` | 43000 | VNC web interface port for tests |
| `MT5_HEALTH_PORT` | 48002 | Health check port for tests |

## Contributions

Feel free to contribute to this project. All contributions are welcome. Open an issue or create a pull request.

## License

This fork retains the original license: [MIT](LICENSE.md). Please review upstream licenses:

- [KasmVNC GPLv2](https://github.com/kasmtech/KasmVNC/blob/master/LICENSE.TXT)
- [LinuxServer KasmVNC Base GPLv3](https://github.com/linuxserver/docker-baseimage-kasmvnc/blob/master/LICENSE)

## Troubleshooting

### Common Issues

**Dependabot failures with mt5linux:**

```bash
# mt5linux is configured to use local path in development
# For production, run setup script:
./scripts/setup-dependencies.sh
```

**Python version conflicts:**

- System uses Python 3.13+ (mt5linux requirement)
- Wine container uses Python 3.12 (numpy/MT5 requirement)
- Both versions are automatically managed

**Test failures:**

```bash
# Ensure dependencies are installed
poetry install

# Run tests through Poetry
poetry run pytest tests/ -v
```

**Container startup issues:**

```bash
# Check logs for specific errors
docker logs mt5

# Verify MT5 credentials in .env
cat .env

# Test with minimal configuration
docker run -e MT5_DEBUG=1 marlonsc/mt5-docker:debian
```

### Dependency Architecture

**Development Environment:**

- Uses local `../mt5linux` path dependency
- Automatic detection by `setup-dependencies.sh`
- Poetry manages all dependencies

**Production Environment:**

- Uses git dependency: `https://github.com/marlonsc/mt5linux.git`
- Configured automatically by setup script
- Dependabot ignores mt5linux updates

**Docker Build:**

- System: Python 3.13+ base image
- Wine: Python 3.12 pre-installed for MT5 compatibility
- NumPy 1.26.4 in both environments

## Makefile Commands

The project includes a comprehensive Makefile for development and operations:

### Development Workflow

```bash
make setup          # Complete development setup (creates .env)
make show-env-status # Check if required credentials are set
make validate-env   # Validate .env configuration
make test           # Run all tests
make lint           # Code quality checks
make format         # Format code
make check          # Run all checks (lint + test)
```

### Docker Operations

```bash
make build          # Build Docker image
make run            # Start container
make stop           # Stop container
make logs           # View logs
make shell          # Open shell in container
```

### Maintenance

```bash
make clean          # Clean build artifacts
make update-deps    # Update dependencies
make health         # System health check
make version        # Show version info
make help           # Show all commands
```

### Environment Validation

```bash
make validate-env   # Validate required credentials in .env
make show-env-status # Show status of environment variables
```

### CI/CD

```bash
make ci            # Run full CI pipeline
make export-requirements  # Export requirements.txt
```

## Acknowledgments

- **Original Author**: [gmag11](https://github.com/gmag11/MetaTrader5-Docker-Image)
- **Core Technologies**: [KasmVNC](https://github.com/kasmtech/KasmVNC), [mt5linux](https://github.com/marlonsc/mt5linux)
- **Infrastructure**: [LinuxServer.io](https://github.com/linuxserver/docker-baseimage-kasmvnc), [WineHQ](https://winehq.org)
- **Community**: MetaTrader5, Docker, and open-source contributors
