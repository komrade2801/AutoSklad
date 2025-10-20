# Server-Side Components Description

This document provides a comprehensive overview of all server-side components in the AutoSklad system, based on the codebase analysis of the `server/` folder.

## Overview

The server is built with **FastAPI** and provides a REST API, web frontend, and bidirectional data synchronization capabilities for tool management and warehouse operations. It supports both SQLite (local sync) and MySQL databases.

## 1. Core FastAPI Web Server (`main.py`)

The primary application entry point that orchestrates all server functionality.

### Key Features:
- **Asynchronous FastAPI Application**: Uses `uvicorn` for serving on configurable host/port
- **Lifespan Management**: Handles startup and shutdown of background synchronization threads
- **Router Mounting**: Integrates multiple API routers under different paths
- **Database Initialization**: Automatically creates SQLite database on first run
- **Static File Serving**: Serves frontend assets, scripts, and styles

### Mounted Components:
- `/frontend`: HTML pages and frontend routing (`front_router`)
- `/sync`: Data synchronization endpoints (`sync_router`)
- `/backend`: Business logic API endpoints (`backend_router`)
- `/assets`: Static CSS/JS/images
- `/scripts`: JavaScript files
- `/style`: CSS stylesheets
- `/JSONs`: Configuration/data JSON files

### Startup Sequence:
1. Database initialization check (`initialize_database_if_needed()`)
2. Device synchronization threads startup (for each configured device)
3. FastAPI application startup with lifespan handler
4. Background sync runners for each vending device

## 2. Configuration System (`options.py`)

Centralizes all server configuration in a single Python file.

### Configuration Parameters:
- **Network**: `Host = "127.0.0.1"`, `port = 8000`
- **Security**: `AES_KEY = b"16byteslongkey!!"` (16-byte key for sync encryption)
- **Database Paths**:
  - `db_path = "web_vending.db"` (main SQLite file)
  - `db_path_work = "vending.db"` (work database)
  - `db_path_test = ":memory:"` (memory database for testing)
- **MySQL Configuration** (optional alternative to SQLite):
  - `DB_HOST = "127.0.0.1"`
  - `DB_PORT = 3306`
  - `DB_NAME = "vending"`
  - `DB_USER = "root"`
  - `DB_PASSWORD = "Fury1488!"`
- **Sync Timers**: `SENDER_TIMEOUT = 30`, `RECEIVER_TIMEOUT = 60`

## 3. Frontend Web Interface (`frontend/`)

Serves the web-based user interface using Jinja2 templates and static assets.

### Structure:
- **`front_router.py`**: Main frontend router handling HTML page serving
- **`page/`**: HTML templates (screen_*.html files)
- **`assets/`**: Static files (images, CSS, JS)
- **`scripts/`**: Client-side JavaScript
- **`style/`**: CSS stylesheets
- **`JSONs/`**: Data files used by frontend

### Features:
- **Dynamic Page Registration**: Automatically discovers and registers screen_*.html files
- **Role-Based Authorization**: Access control based on user roles and rights
- **Navigation System**: Dynamic navbar and button generation based on permissions
- **Session Management**: User authentication and token validation
- **Progress Tracking**: Database setup progress interface with real-time updates

### Key Endpoints:
- `/`: Authorization page (default landing)
- `/screen_*.html`: Various application screens (users, tools, history, etc.)
- `/assets/html/nav_btn.html`: Navigation button component
- `/assets/html/navbar.html`: Top navigation bar
- `/progress`: Database setup progress status
- `/start`: Initiates database setup process in background

## 4. Backend API System (`API/backend/`)

Provides REST API endpoints for all business logic operations.

### Structure:
- **`routers.py`**: Main backend router aggregating all endpoint routers
- **`endpoints/`**: Individual endpoint modules for different data domains

### API Endpoint Categories:

#### Data Management:
- **`all_users_router`**: User management operations
- **`all_groups_router`**: User groups and permissions
- **`all_plans_router`**: Work plans management
- **`all_tools_router`**: Tool inventory operations
- **`actual_norms_router`**: Tool usage norms
- **`cells_map_router`**: Warehouse cell layouts
- **`tool_library_router`**: Tool library operations

#### History & Operations:
- **`history_router`**: General history operations
- **`history_loads_router`**: Tool loading history
- **`history_operation_router`**: Operation history
- **`history_error_router`**: Error logs
- **`history_write_off_router`**: Tool write-off history

#### Mass Operations:
- **`mass_load_router`**: Bulk tool loading
- **`mass_drop_router``: Bulk tool dropping
- **`json_random_load_router`**: Random load operations

#### Device Management:
- **`all_device_router`**: Vending device management

### Features:
- **Pydantic Models**: Type-safe request/response validation
- **Dependency Injection**: Database session management
- **CRUD Operations**: Full create, read, update, delete for all entities

## 5. Database System (`DB/`)

Comprehensive database layer with support for SQLite and MySQL.

### Structure:
- **`DB/Data/`**: Database connection and schema setup
- **`DB/Engine/`**: CRUD operation classes (one per entity)
- **`DB/Models/`**: SQLAlchemy model definitions
- **`DB/BaseCRUD.py`**: Common database operations base class

### Database Options:
- **SQLite** (`sqlite_db.py`): Local file-based database for sync operations
- **MySQL** (`mysql_db.py`): Remote database for larger deployments
- **Auto-Initialization** (`init_db.py`): Creates database schema if missing

### Key Entities (50+ CRUD classes):
- **User Management**: User, Role, Rights
- **Tool Management**: Tools, ToolTypes, ToolsNorm
- **Operations**: Load, Drop, MassLoad, MassDrop, OperationsConsumption
- **Warehouse**: Cell, CellHasDevice, ToolLocation
- **History**: History, HistoryLoad, HistoryError
- **Plans**: Plan, PlanToolTypes, ActualNorm

### Initialization Process:
1. Check if SQLite file exists (`web_vending.db`)
2. If missing: run `rebuild_db()` (create tables) and `execute()` (seed data)
3. Restart application to reload with new database

## 6. Synchronization Service (`dbSync/`)

Handles bidirectional data synchronization between server and client devices.

### Structure:
- **`Transport/routers.py`**: HTTP sync endpoints (`/sync/push`, `/sync/pull`, `/sync/handshake`)
- **`Logic_v2/`**: Core sync logic with conflict management
- **`Runner.py`**: Background sync thread management
- **`Models/`**: Sync-specific models and schemas

### Key Components:
- **CommandQueue**: Background task processing
- **CDCService**: Change Data Capture handling
- **ConflictManager**: Sync conflict resolution
- **DataMapper**: Schema mapping between databases
- **RetryManager**: Failed sync retry logic
- **JSONSchemaValidator**: Sync payload validation

### Sync Endpoints:
- **`/push?device=<id>`**: Receives commands from client with AES encryption
- **`/pull?device=<id>`**: Sends pending commands to client
- **`/handshake`**: Schema synchronization and validation

### Encryption:
- **AES-CBC** encryption for all sync communication
- 16-byte keys (configured in `options.py`)
- PKCS7 padding for variable-length data

### Thread Management:
- Per-device sync threads (started in lifespan handler)
- Background queues for async processing
- Automatic thread cleanup on shutdown

## 7. Core Utilities (`Core/`)

Supporting infrastructure and business logic.

### Components:
- **`authorization.py`**: User authentication and authorization logic
- **`documenter.py`**: Database schema documentation
- **`Parser.py`**: HTML parsing and navigation generation
- **`Create_db.py`**: Database schema creation scripts
- **`default.py`**: Application defaults and setup processes
- **`DatabaseMigrator.py`**: Database migration utilities

## 8. Logic Layer (`Logic/`)

Business logic implementations for complex operations.

- **`HistoryOperationCRUD.py`**: History-specific operations
- **`NormCRUD.py`**: Tool usage normalization logic

## 9. Deployment and Development

### Entry Points:
- **`main.py`**: Production server startup
- **`run.bat`**: Windows batch file for running
- **`run.txt`**: Command-line arguments documentation

### Requirements (`requirements.txt`):
- FastAPI, Uvicorn (web server)
- SQLAlchemy, PyMySQL (database)
- Jinja2 (templating)
- PyCryptodome (AES encryption)
- python-multipart (file uploads)
- Additional utilities for development

### Configuration Flow:
1. `options.py` sets host/port and database config
2. `main.py` initializes database and routers
3. Synchronization threads start for configured devices
4. Static assets are served from `frontend/` directories
5. API endpoints become available under `/backend` and `/sync`

## 10. Monitoring and Logging

- **Crash Logging**: `crash.log` for fault analysis
- **Sync Logging**: Logs under `logs/` directory
- **Command Queue**: `command_queue.json` for sync status
- **Progress Tracking**: Real-time setup progress for DB initialization

## Architecture Benefits

- **Scalable**: Supports multiple vending devices with independent sync
- **Secure**: AES encryption for all client-server communication
- **Flexible**: SQLite for simple deployments, MySQL for enterprise
- **Maintainable**: Clean separation between API, sync, and frontend
- **Extensible**: Modular architecture for adding new features

This comprehensive server architecture enables a modern tool management system with real-time synchronization, role-based access control, and a rich web interface for warehouse operations.
