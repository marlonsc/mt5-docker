# MetaTrader5 Docker Image (Fork)

This is a fork of the original project by [gmag11](https://github.com/gmag11/MetaTrader5-Docker-Image). It provides a Docker image for running MetaTrader5 with remote access via VNC, based on the [KasmVNC](https://github.com/kasmtech/KasmVNC) project and [KasmVNC Base Image from LinuxServer](https://github.com/linuxserver/docker-baseimage-kasmvnc).

Changes in this fork:

- Added Expert Advisor (EA) automation support with Windows .NET Framework under Wine. Mono is removed.
- Split `start.sh` into modular scripts under `Metatrader/scripts/` for clearer install and runtime steps.
- Added auto-login support via environment variables (`MT5_LOGIN`, `MT5_PASSWORD`, `MT5_SERVER`).
- Added health monitoring and auto-recovery for MT5 and RPyC server.
- Integrated `mt5linux` from GitHub with resilient RPyC server.
- Updated image metadata and labels following OCI standards.
- Fail-fast startup: scripts exit immediately on critical failures.

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
Due to some compatibility issued, version 2 has switched its base from Alpine to Debian Linux. This and adding Python environment makes that container size is considerably bigger from about 600 MB to 4 GB.

If you just need to run Metatrader for running your MQL5 programs without any Python programming I recommend to go on using version 1.0. MetaTrader program is updated independently from image so you will always have latest MT5 version.

-----------

## Requirements

- Docker installed on your machine.
- Only intelx86/amd64 host is supported
- Internet connectivity on first run (downloads MT5, Wine components, and optional .NET).

## Usage from repository

1. Clone this repository:

```bash
git clone https://github.com/glendekoning/mt5-docker
cd mt5-docker
```

2. Build the Docker image:

```bash
docker build -t glendekoning/mt5-docker:local .
```

3. Run the Docker image:

```bash
docker run -d -p 3000:3000 -p 8001:8001 -v config:/config glendekoning/mt5-docker:local
```

Now you can access MetaTrader5 via a web browser at localhost:3000.

On first run it may take a few minutes to install MT5, Wine dependencies, and optionally .NET Framework. Normally it takes less than 10 minutes The process is automatic and you should end up with MetaTrader5 running in your web session.

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
    image: glendekoning/mt5-docker
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

## .NET Support

- Windows `.NET Framework` inside Wine:
  - Installed via `winetricks dotnet48` into `WINEPREFIX=/config/.wine`.
  - Enables EAs that depend on .NET Framework when running MT5 under Wine.

Disable by setting `ENABLE_WIN_DOTNET=0` in compose.


**Notice**: If you do not need to do remote python programming you can get a much smaller installation changing this line:

```yaml
image: glendekoning/mt5-docker
```

by this one

```yaml
image: glendekoning/mt5-docker:1.1
```

3. Start the container

```bash
docker compose up -d
```

In some systems `docker compose` command does not exists. Try to use `docker-compose up -d` instead.

4. Connect to web interface
   Start your browser pointing http://<your ip address>:3000

On first run it may take a few minutes to install MT5, Wine dependencies, and optionally .NET Framework and should take aprox 5 minutes. The process is automatic and you should end up with MetaTrader5 running in your web session.

## Where to place MQ5 and EX5 files

In the case you want to run your own MQL5 bots inside the container you can find MQL5 folder structure in

```
config/.wine/drive_c/Program Files/MetaTrader 5/MQL5
```

All files that you place there can be accessed from your MetaTrader container without the need to restart anything.

You can access MetaEditor program clicking in `IDE` button in MetaTrader5 interface.

**Notice**: If you will run MQL5 only bots (without Python) you can run perfectly with gmag11/metatrader5_vnc:1.0 image as pointed before. Remember that **image version is not stuck to a specific MetaTrader 5 version**.

**Metatrader will always be updated automatically to latest version as it does when it is nativelly installed in Windows.**

## Python Programming

Install [mt5linux](https://github.com/marlonsc/mt5linux) on your Python host (any OS):

```bash
pip install git+https://github.com/marlonsc/mt5linux.git@master
```

**Required library versions:**

- mt5linux >= 0.2.1
- numpy >= 2.1.0
- rpyc >= 5.2.0, < 6.0.0
- plumbum >= 1.8.0

**Example usage:**

```python
from mt5linux import MetaTrader5

mt5 = MetaTrader5(host='host-running-docker', port=8001)
mt5.initialize()
print(mt5.version())
```

**Expected output:**

```
>>> from mt5linux import MetaTrader5
>>> mt5 = MetaTrader5(host='192.168.1.10', port=8001)
>>> mt5.initialize()
True
>>> print(mt5.version())
(500, 4993, '22 Dec 2025')
```

## Configuration

### Environment Variables

**Auto-Login (optional):**
- `MT5_LOGIN`: MetaTrader 5 account number
- `MT5_PASSWORD`: Account password
- `MT5_SERVER`: Broker server (default: MetaQuotes-Demo)

**Optional Features:**
- `ENABLE_WIN_DOTNET`: Install .NET Framework 4.8 for .NET EAs (default: `1`)
- `AUTO_RECOVERY_ENABLED`: Auto-restart on failures (default: `1`)
- `HEALTH_CHECK_INTERVAL`: Health check interval in seconds (default: `30`)

**Advanced (usually no need to change):**
- `WINEPREFIX`: Wine environment directory (default: `/config/.wine`)
- `WINEDEBUG`: Wine debug output (default: `-all` for silent)
- `TZ`: Container timezone

### Ports

- `3000`: KasmVNC web interface
- `8001`: RPyC service for mt5linux remote control

### Startup Scripts

The container startup is modularized under `Metatrader/scripts/`:

- `05_config_unpack.sh`: Unpack pre-configured Wine prefix (if available)
- `10_prefix_init.sh`: Initialize Wine prefix and install Gecko
- `20_winetricks.sh`: Install winetricks dependencies (vcrun2019, fonts, etc.)
- `30_mt5.sh`: Install, configure, and launch MetaTrader 5
- `40_python_wine.sh`: Install Python and packages in Wine
- `50_python_linux.sh`: Install mt5linux on Linux
- `60_server.sh`: Configure s6-overlay RPyC server

Health monitoring is handled by `Metatrader/health_monitor.sh` which runs in the background.

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

## Testing

The project includes automated tests using pytest. Tests run against an isolated test container (`mt5docker-test`) with separate ports to avoid conflicts with production or other test environments.

### Prerequisites

1. **Configure credentials**: Copy the example file and fill in your MT5 credentials:

```bash
cp .env.example .env
```

2. **Edit `.env`** with your MetaTrader 5 credentials:

```bash
# Required for tests
MT5_LOGIN=your_login_number
MT5_PASSWORD=your_password
MT5_SERVER=MetaQuotes-Demo
```

To create a MetaQuotes Demo account:
- Open MT5 in the container (`http://localhost:3000`)
- File → Open an Account → MetaQuotes-Demo
- Fill in the registration form
- Copy your login and password to `.env`

3. **Install test dependencies**:

```bash
pip install pytest rpyc
```

### Running Tests

```bash
# Start the isolated test container
./scripts/test-container.sh

# Run all tests
pytest tests/ -v

# Run specific test class
pytest tests/test_container.py::TestContainerIsolation -v

# Stop test container when done
./scripts/test-container.sh --stop
```

### Test Container Isolation

The test container uses isolated ports to avoid conflicts:

| Service | Production | mt5docker-test |
|---------|------------|----------------|
| VNC     | 3000       | 43000          |
| RPyC    | 8001       | 48812          |
| Health  | 8002       | 48002          |

### Environment Variables

All test configuration can be overridden via environment variables or `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `MT5_LOGIN` | (required) | MT5 account login |
| `MT5_PASSWORD` | (required) | MT5 account password |
| `MT5_SERVER` | MetaQuotes-Demo | MT5 server name |
| `MT5_CONTAINER_NAME` | mt5docker-test | Container name |
| `MT5_RPYC_PORT` | 48812 | RPyC service port |
| `MT5_VNC_PORT` | 43000 | VNC web interface port |
| `MT5_HEALTH_PORT` | 48002 | Health check port |

## Contributions

Feel free to contribute to this project. All contributions are welcome. Open an issue or create a pull request.

## License

This fork retains the original license: [MIT](LICENSE.md). Please review upstream licenses:

- [KasmVNC GPLv2](https://github.com/kasmtech/KasmVNC/blob/master/LICENSE.TXT)
- [LinuxServer KasmVNC Base GPLv3](https://github.com/linuxserver/docker-baseimage-kasmvnc/blob/master/LICENSE)

## Acknowledgments

- Original author: [gmag11](https://github.com/gmag11/MetaTrader5-Docker-Image)
- Projects: [KasmVNC](https://github.com/kasmtech/KasmVNC), [LinuxServer KasmVNC Base](https://github.com/linuxserver/docker-baseimage-kasmvnc), [mt5linux](https://github.com/lucas-campagna/mt5linux)
