# MetaTrader5 Docker Image (Fork)

This is a fork of the original project by [gmag11](https://github.com/gmag11/MetaTrader5-Docker-Image). It provides a Docker image for running MetaTrader5 with remote access via VNC, based on the [KasmVNC](https://github.com/kasmtech/KasmVNC) project and [KasmVNC Base Image from LinuxServer](https://github.com/linuxserver/docker-baseimage-kasmvnc).

Changes in this fork:

- Added Expert Advisor (EA) automation support requiring full Windows .NET Framework under Wine. Mono is removed.
- Split `start.sh` into modular scripts under `Metatrader/scripts/` for clearer install and runtime steps.
- Added data sync: copies EA binaries from `data/ea/` into MT5 `MQL5/Experts`, and `.set` files from `data/set-files/` into the MT5 `Documents` directory.
- Updated to Python 3.13 for better performance and modern language features.
- Updated image metadata and labels following OCI standards.
- General build quality-of-life improvements and better documentation.

## Features

- Run MetaTrader5 in an isolated environment.
- Remote access to MetaTrader5 interface via an integrated VNC client accessible through a web browser.
- Built on the reliable and secure [KasmVNC](https://github.com/kasmtech/KasmVNC) project.
- RPyC server for remote access to Python MetaTrader Library from Windows or Linux using <https://github.com/lucas-campagna/mt5linux>
- Expert Advisors (EAs) support:
  - Full Windows `.NET Framework 4.8` installed inside Wine for EA compatibility.
  - Automatic sync of EA files and settings from the `data/` folder into the MT5 environment.

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

Use this content filling user and password with your own data.

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
      - CUSTOM_USER=<Choose a user>
      - PASSWORD=<Choose a secure password>
      - ENABLE_WIN_DOTNET=1   # install .NET Framework 4.8 in Wine (required for .NET-dependent EAs)
      - ENABLE_DATA_SYNC=1    # enable EA and .set file synchronization from /data
      - TZ=UTC                # optional: set timezone for logs and MT5
## .NET Support

- Windows `.NET Framework` inside Wine:
  - Installed via `winetricks dotnet48` into `WINEPREFIX=/config/.wine`.
  - Enables EAs that depend on .NET Framework when running MT5 under Wine.

Disable by setting `ENABLE_WIN_DOTNET=0` in compose.

## EA and Set File Sync

When `ENABLE_DATA_SYNC=1` is set, the container will:
- Copy EA binaries from `data/ea/` (e.g., `Dark Moon MT5.ex5`) into `config/.wine/drive_c/Program Files/MetaTrader 5/MQL5/Experts`.
- Copy `.set` files from `data/set-files/` (e.g., `myfxbook.set`) into the MT5 `Documents` directory at `config/.wine/drive_c/users/<user>/Documents`.

This is handled by the modular startup scripts (`Metatrader/scripts/35_data_sync.sh`) and runs at container start. Place your files in the `data/` folder before starting or restart the container to re-sync.

Example `data/` folder structure:

```

data/
  ea/
    Dark Moon MT5.ex5
    AnotherEA.ex5
  set-files/
    myfxbook.set
    AnotherEA-EURUSD-M15.set

```

Mounted paths inside container:
- `data/ea/*` -> `config/.wine/drive_c/Program Files/MetaTrader 5/MQL5/Experts/`
- `data/set-files/*` -> `config/.wine/drive_c/users/<user>/Documents/`
```

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

## Python programming

You need to install [mt5linux library](https://github.com/lucas-campagna/mt5linux) in your Python host. It may be in any OS, not only Linux.

**Required library versions for compatibility:**
- mt5linux == 0.2.1
- numpy == 2.3.5
- rpyc == 5.3.1
- plumbum == 1.8.0

This is a simple snippet to run your Python script fron any host

```python
from mt5linux import MetaTrader5
mt5 = MetaTrader5(host='host running docker container',port=8001)
mt5.initialize()
print(mt5.version())
```

Output should be something like this:

```
(mt5linux) linux:~/$ python3
Python 3.13.7 (main, Dec 13 2025, 14:30:45) [GCC 13.2.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> from mt5linux import MetaTrader5
>>> mt5 = MetaTrader5(host='192.168.1.10',port=8001)
>>> mt5.initialize()
True
>>> print(mt5.version())
(500, 4993, '22 Dec 2025')
>>>
```

## Configuration

Key environment variables:

- `CUSTOM_USER` / `PASSWORD`: web UI credentials for KasmVNC.
- `ENABLE_WIN_DOTNET`: install Windows .NET Framework 4.8 inside Wine (required for .NET-dependent EAs). Default `1`.
- `ENABLE_DATA_SYNC`: enable copying EA `.ex5` and `.set` files from `data/` into MT5 paths. Default `1`.
- `TZ`: set container timezone.

Ports:

- `3000`: KasmVNC web interface.
- `8001`: RPyC service for `mt5linux` remote control.

Startup scripts:
The container startup has been modularized. Key scripts under `Metatrader/scripts/` include:

- `30_mt5_install.sh`: installs MetaTrader 5 under Wine.
- `34_config_unpack.sh`: unpacks default config if needed.
- `35_data_sync.sh`: copies EA and `.set` files from `data/` to their respective MT5 directories.
- `36_myfxbook.sh`: optional integration.
- `40_python_wine.sh` / `50_python_linux.sh`: Python environment setup.
- `60_server.sh`: starts services (VNC, RPyC) and MT5.

## Contributions

Feel free to contribute to this project. All contributions are welcome. Open an issue or create a pull request.

## License

This fork retains the original license: [MIT](LICENSE.md). Please review upstream licenses:

- [KasmVNC GPLv2](https://github.com/kasmtech/KasmVNC/blob/master/LICENSE.TXT)
- [LinuxServer KasmVNC Base GPLv3](https://github.com/linuxserver/docker-baseimage-kasmvnc/blob/master/LICENSE)

## Acknowledgments

- Original author: [gmag11](https://github.com/gmag11/MetaTrader5-Docker-Image)
- Projects: [KasmVNC](https://github.com/kasmtech/KasmVNC), [LinuxServer KasmVNC Base](https://github.com/linuxserver/docker-baseimage-kasmvnc), [mt5linux](https://github.com/lucas-campagna/mt5linux)
