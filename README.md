# AutoSklad

A client–server system for warehouse tooling accounting and synchronization. The project contains:
- Server (FastAPI) with web frontend and synchronization services
- Client (PyQt5 GUI + embedded FastAPI) running on Windows or Raspberry Pi
- Local/remote databases and background sync pipelines


### Repository layout
- `server/`: Web API, frontend assets, sync services, DB models/CRUD, and options
- `client/`: PyQt5 GUI app, embedded FastAPI, serial/barcode managers, local DB/sync
- `client/Arduino/`: Microcontroller sketches used by the mechanics
- `client/GUI/`: Qt UI files and generated Python classes
- `client/dbSync` and `server/dbSync`: synchronization infrastructure used by both sides
- `client/DB` and `server/DB`: database engines, models, init scripts


## Prerequisites
- OS: Windows 10/11 or Linux (Ubuntu/Debian, Raspberry Pi OS)
- Python: 3.10–3.12 (x64), added to PATH
- Network: open ports according to config
- GUI: for PyQt5 client, run in a GUI session (not plain SSH)

Linux system packages (recommended):
```bash
sudo apt update && sudo apt install -y build-essential python3-venv \
  libxcb-xinerama0 libmysqlclient-dev
# Optional for images/barcodes on server:
sudo apt install -y libjpeg-turbo-progs zlib1g-dev
```


## Quick start

### 1) Server
From repository root:
```bash
cd server
python -m venv venv
# Linux/macOS
source venv/bin/activate
# Windows PowerShell
# .\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip wheel
pip install -r requirements.txt
```
Configure `server/options.py` (host/port, AES key, DB params):
```python
Host = "0.0.0.0"
port = 8000
AES_KEY = b"16byteslongkey!!"  # must be 16 bytes, match client
```
Initialize database if needed (SQLite sync DB), or just start once to auto-init:
```bash
# Optionally:
python -m dbSync.sync_db
```
Run server:
```bash
python main.py
# or
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
Basic check:
```bash
curl -sI http://127.0.0.1:8000 | head -n1
```

### 2) Client
From repository root:
```bash
cd client
python -m venv venv
# Linux/macOS
source venv/bin/activate
# Windows PowerShell
# .\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip wheel
pip install -r requirements.txt
```
If PyQt5 builds from sources on Linux, prefer system package and comment it out in `requirements.txt`:
```bash
sudo apt install -y python3-pyqt5
```

Configure `client/config.json`:
- `server.ip`, `server.port`: server address/port
- `network.ip`, `network.port`: local FastAPI of the client (e.g. `0.0.0.0:8081`)
- `dev/serial/barcode`: device ports (ignored in mock mode)
- `aes`: string of exactly 16 chars, must match server AES key

Initialize local client DB (first run only):
```bash
python -m DB.Create_db
```

Run in mock mode (no hardware required):
```bash
# Linux/macOS
export AUTOSKLAD_USE_MOCKS=1
# Windows PowerShell
# $env:AUTOSKLAD_USE_MOCKS="1"
python main.py
```
The client starts a local FastAPI on `network.ip:network.port` and opens the PyQt GUI.


## Configuration details

### Client (`client/config.json`)
- `server.ip` / `server.port`: server URL the client syncs to
- `network.ip` / `network.port`: where the client’s embedded FastAPI listens
- `serial`, `barcode`, `dev`: serial device ports; Windows uses `serial/barcode`, Raspberry Pi uses `dev`
- `aes`: 16-char key (example: `"16byteslongkey!!"`)

Environment variables:
- `AUTOSKLAD_USE_MOCKS=1` enables mock serial/barcode and GPIO stubs

### Server (`server/options.py`)
- `Host`, `port`: server bind address and port
- `AES_KEY`: 16-byte key; must match client’s `aes` (same bytes)
- MySQL config (optional): `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`


## Architecture overview
- FastAPI servers on both sides provide HTTP APIs and a `/sync` router for bidirectional data sync
- Client GUI is built with PyQt5 and interacts with serial controller and barcode scanner
- Mock mode replaces hardware with software simulators for development
- SQLite/MySQL supported depending on deployment; DB layers are split under `DB/Engine` and `DB/Models`

Key entry points:
- Server: `server/main.py`
- Client: `client/main.py`


## Troubleshooting
- PyQt5 build issues on Linux:
  - Install via system packages: `sudo apt install -y python3-pyqt5`
  - Comment out `PyQt5` in `client/requirements.txt` before `pip install`
- `cryptography/jsonschema` build problems:
  - Use PyCryptodome (already preferred), pin `jsonschema<4.18` if required
  - Upgrade build tools: `python -m pip install --upgrade pip wheel setuptools`
- GUI not visible over SSH:
  - Run in a local GUI session or configure X11 forwarding
- Authorization/data mismatch:
  - Recreate client local DB: `python -m DB.Create_db`
  - Check user roles and rights; logs should show detected role
- Ports/firewall:
  - Ensure server `port` is open and client `network.port` is free
  - On Windows, allow Python in Defender Firewall; on Linux, open with `ufw`
 
## Maintenance scripts
- `cleanup_databases.ps1`: утилита из корня репозитория удаляет рабочие SQLite (`server/dbSync/Model/sync.db`, `client/dbSync/Model/sync.db`, `server/DB/Data/web_vending.db`, `client/DB/Data/vending.db`), очереди команд и очищает кэш схем/полей (`server|client/dbSync/Logic_v2/cache/{schema,fields}`). Аргументы: `-ProjectRoot "<path>"` для явной директории и `-Force` для пропуска подтверждения. После очистки кэши пересоздаются на следующем handshake.
 
## Development
- Python versions: 3.10–3.12
- Activate virtual environments for both `server/` and `client/`
- To tweak sync during UI work, you can temporarily use unreachable `server.ip` in client config or comment the sync start/stop in `client/main.py`


## License
Not specified. Add your license of choice (e.g., MIT) to `LICENSE` if needed. 
