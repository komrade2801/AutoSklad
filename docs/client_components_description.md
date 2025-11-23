# Client-Side Components Description

This document provides a comprehensive overview of all client-side components in the AutoSklad system, based on the codebase analysis of the `client/` folder.

## Overview

The client is a PyQt5-based desktop application that provides the primary user interface for tool management and vending operations. It includes an embedded FastAPI server for synchronization, hardware controllers for Arduino and barcode scanner integration, and sophisticated state machine management for GUI navigation. The client supports both real hardware and mock/simulated modes for development.

## 1. PyQt5 GUI Application (`GUI/`)

The main user interface built with PyQt5, consisting of multiple screens and state-driven navigation.

### Structure:
- **`MainWindow.py`**: Central application window with Qt event loops
- **`BaseScreen.py`**: Abstract base class for all GUI screens
- **`screen_*.py`**: Individual screen implementations (30+ screens)
- **`ui/`**: Qt Designer UI files (XML format)
- **`ui_classes/`**: Generated Python classes from UI files
- **`widgets/`**: Custom Qt widgets and custom dialogs
- **`ico/`**: Icons and images (PNG/SVG formats)
- **`img/`**: Graphics assets and button states

### Key Features:
- **State Machine Integration**: Uses Finite State Machine (FMS) for screen navigation
- **Multi-Screen Management**: 30+ screens handling different operational states
- **Custom Widgets**: Reusable UI components (keyboards, error dialogs, tool selectors)
- **Event-Driven Architecture**: Qt signals/slots for hardware integration
- **Platform Detection**: Automatic fullscreen on Raspberry Pi, windowed on Windows/Linux

### State Management (`StateMachine/`):
- **`FMS.py`**: Finite State Machine implementation with transitions
- **`state_map.py`**: Screen transition mappings
- **`screens.py`**: Screen definitions and configurations
- **`NavigationManager.py`**: History and back button management

### Main Application (`main.py`):
- **Database Initialization**: Ensures local SQLite databases are ready
- **Hardware Setup**: Initializes Serial/Barcode managers based on platform/mock mode
- **Embedded Server**: Launches FastAPI server in separate thread
- **Qt Application Loop**: Main event loop for GUI
- **Graceful Shutdown**: Proper cleanup of threads and hardware connections

## 2. Embedded FastAPI Server

A local web server integrated into the client application for synchronization functionality.

### Technical Details:
- **Port Configuration**: Default 8080 (configurable via `config.json` network.port)
- **Router Mounting**: `/sync` endpoints for bidirectional data exchange
- **Threading Model**: Runs in separate QThread (UvicornThread) to avoid blocking GUI
- **Shared Database Access**: Same SQLite databases as GUI thread
- **Lifespan Management**: FastAPI lifespan context manages sync thread startup/shutdown

### Synchronization Endpoints (`dbSync/Transport/routers.py`):
- **`/push`**: Send commands to server (encrypted with AES-CBC)
- **`/pull`**: Receive pending commands from server
- **`/handshake`**: Initial synchronization handshake with schema validation (AES-encrypted)

### Transport Layer (`dbSync/Transport/`):
- **`routers.py`**: FastAPI router with sync endpoints (`/push`, `/pull`, `/handshake`)
- **`TransportService.py`**: HTTP client with AES encryption for sync communication
- **`ws_transport.py`**: WebSocket transport implementation (optional, for future use)
- **`client_ws.py`**: WebSocket client implementation
- **`server_ws.py`**: WebSocket server implementation

## 3. Synchronization Service (`dbSync/`)

Comprehensive bidirectional data synchronization system managing data consistency between local client databases and central server through command-based synchronization protocol.

### Architecture Overview

The client synchronization service implements a **Command Queue Pattern** where all local database changes are captured as commands, queued for transmission, and synchronized with the server through encrypted HTTP communication. This enables offline operation with eventual consistency.

### Core Sync Components Structure

#### Command-Based Architecture:
- **`SyncProcessor`**: Client-side coordinator handling command processing and server communication
- **`CommandQueue`**: In-memory command staging with JSON persistence for crash recovery
- **`CommandRunner`**: Background sync thread orchestrating push/pull cycles
- **`TransportService`**: AES-encrypted HTTP client for server endpoint communication

#### Data Processing Pipeline:
- **`DataMapper`**: Translates data between client-server schema formats using cached mappings
- **`DataTransformer`**: Applies business rules and validation during sync operations
- **`ConflictManager`**: Handles data conflicts from bidirectional sync operations
- **`BatchProcessor`**: Executes local database changes in atomic transactions
- **`RetryManager`**: Manages re-sync of failed operations with exponential backoff
- **`CDCService`**: Change Data Capture service that tracks database changes and notifies listeners
- **`MappingConfigurator`**: Configures field mappings and conflict resolution strategies

#### Schema & Validation:
- **`SchemaCache`**: Client-side SHA256-hashed mapping cache for schema translations
- **`SchemaAnalyzer`**: Generates field mappings from handshake responses
- **`JSONSchemaValidator`**: Validates incoming/outgoing sync payloads against schemas

### Synchronization Workflow & Protocols

#### 1. Handshake Phase (`/sync/handshake`)
**Purpose**: Establishes client-server compatibility and obtains field mapping schema.

**Client Process**:
1. Client sends SHA256 hash of its database schema (table structures)
2. Receives field mapping object from server (`{mapping: {...}, schema_hash: "hash"}`)
3. `SchemaCache` stores mappings under server-returned hash
4. Cached mappings used for all subsequent data transformations

**Server Response Format**:
```json
{
  "mapping": {
    "Tools": {"name": "tools_name", "type_id": "type_id"},
    "User": {"login": "user_login", "role": "user_role"}
  },
  "schema_hash": "client_hash"
}
```

#### 2. Pull Operation (`/sync/pull?device=<id>&since=<timestamp>`)
**Purpose**: Client receives pending server changes for local application.

**Client Process**:
1. Background sync thread requests pull with last sync timestamp
2. AES-encrypted HTTP request sent to server
3. Receives encrypted command list to apply locally
4. Decrypts and applies commands through `SyncProcessor.process_pull()`
5. Updates local database with server changes
6. Records sync completion timestamp for next pull

**Server Response Format**:
```json
{
  "schema_hash": "<client_hash>",
  "commands": [
    {
      "id": "uuid",
      "table": "Tools",
      "operation": "add",
      "data": {"name": "Drill", "count": 1},
      "last_modified": "2025-09-27T12:18:57Z"
    }
  ]
}
```

#### 3. Push Operation (`/sync/push?device=<id>`)
**Purpose**: Client sends local changes to server for global synchronization.

**Client Process**:
1. Background thread gathers pending commands from `command_queue.json`
2. Applies client→server data transformations using cached schema mappings
3. AES encrypts command batch and sends to `/sync/push`
4. Receives encrypted status response with per-command success/failure
5. Updates local queue based on server acknowledgment
6. Failed commands rescheduled via `RetryManager`

**Push Command Batch Format**:
```json
{
  "device": 1,
  "schema_hash": "<server_hash>",
  "commands": [
    {
      "id": "uuid",
      "table": "Tools",
      "operation": "add",
      "data": {"name": "Hammer", "inventory_number": "123"}
    },
    {
      "id": "uuid2",
      "table": "History",
      "operation": "add",
      "data": {"user_id": 1, "action": "tool_issued"}
    }
  ]
}
```

**Server Status Response Format**:
```json
[
  {"id": "uuid", "status": "COMPLETED"},
  {"id": "uuid2", "status": "FAILED", "error": "Validation error"}
]
```

### Command Queue System (`command_queue.json`)

The command queue serves as **persistent staging area** for all local database changes pending synchronization with the server.

#### Command Structure in JSON:
```json
{
  "id": "uuid",                    // Globally unique command identifier
  "table": "Tools|User|Cell",      // Database table being modified
  "operation": "insert|update|delete", // CRUD operation type (lowercase)
  "data": {                        // Full record data payload
    "name": "Drill Press",
    "inventory_number": "DM-001",
    "count": 5
  },
  "status": "pending|retrying|failed|done",   // Sync processing status
  "timestamp": "RFC3339"           // Command creation time (ISO 8601 format)
}
```

#### Queue Lifecycle & Data Flow:
1. **Command Generation**: Database changes captured via event handlers/decorators
2. **Queue Persistence**: Commands immediately written to `command_queue.json`
3. **Background Processing**: Sync thread reads pending commands periodically
4. **Schema Mapping**: Command data transformed using cached handshake mappings
5. **AES Encryption**: Prepared batch encrypted before HTTP transmission
6. **Server Submission**: Encrypted payload sent to `/sync/push?device=<id>`
7. **Status Processing**: Server response decrypted, statuses applied to queue
8. **Queue Cleanup**: Successfully synced commands (`status: "done"`) removed

#### Real Example Command Records:
```json
[
  {
    "id": "e53d46a6-4821-44aa-848a-e27b443198c8",
    "table": "Tools",
    "operation": "insert",
    "data": {
      "index": 3,
      "inventory_number": "",
      "plan_id": null,
      "tool_type_id": 1,
      "name": "Фреза 5х30мм",
      "description": "",
      "count": 3,
      "img": "",
      "groups_id": 2
    },
    "status": "done",
    "timestamp": "2025-09-26T16:51:32.002044Z"
  },
  {
    "id": "60a59368-dec0-4a4d-9ede-70f13797c361",
    "table": "History",
    "operation": "insert",
    "data": {
      "index": 1,
      "datetime": "2025-09-27T15:18:57.959816",
      "status": 0,
      "description": "Массовая загрузка инициирована",
      "user_id": 1,
      "user_role_id": 1,
      "tools_id": 4
    },
    "status": "done",
    "timestamp": "2025-09-27T12:18:57.960827Z"
  }
]
```

### Database Models for Sync

#### Client-Side Command Storage Schema:
```sql
CREATE TABLE Command (
  id INTEGER PRIMARY KEY,
  table_name VARCHAR NOT NULL,    -- Target table name
  operation VARCHAR NOT NULL,     -- insert|update|delete
  record_id INTEGER,              -- Local record ID
  created_at TIMESTAMP,
  device_number INTEGER,          -- Device ID
  FOREIGN KEY (id) REFERENCES Record(command_id)
);
```

#### Record Table Structure:
```sql
CREATE TABLE Record (
  id INTEGER PRIMARY KEY,
  command_id INTEGER REFERENCES Command(id),
  data_json TEXT,                 -- JSON-serialized record data
  last_modified TIMESTAMP
);
```

#### CommandStatus Table Structure:
```sql
CREATE TABLE CommandStatus (
  id INTEGER PRIMARY KEY,
  command_id INTEGER REFERENCES Command(id),
  status VARCHAR NOT NULL,        -- pending|in_progress|completed|failed
  updated_at TIMESTAMP
);
```

### Encryption & Security

#### AES-CBC Communication Protocol:
- **Shared Secret**: Symmetric key configured in `config.json` (`aes` field)
- **IV Management**: Random 16-byte initialization vectors for each message
- **PKCS7 Padding**: Variable-length message padding for block cipher
- **Authentication**: Device ID in URL parameters for endpoint routing

#### Bidirectional Communication Flow:
1. **Client Transmission**: `AES_ENCRYPT(IV + JSON_batch, client_aes_key)`
2. **Server Reception**: Uses same key from server config to decrypt
3. **Server Response**: `AES_ENCRYPT(IV2 + JSON_statuses, client_aes_key)`
4. **Client Decryption**: Decrypts status array to update local command statuses

### Threading & Scheduling

#### Client-Side Threading Architecture:
- **GUI Thread**: Qt event loop for user interface interactions
- **FastAPI Thread**: Local web server for embedded sync endpoints
- **Sync Thread**: Background synchronization thread (`UvicornThread` wrapper)
- **Database Threads**: Serial/hardware I/O threads with Qt signal communication

#### Sync Scheduling Model:
- **Push Interval**: Every `sender_timeout` seconds (default 15s from config), commands pushed
- **Pull Interval**: Every `receiver_timeout` seconds (default 30s from config), changes pulled
- **Retry Scheduling**: Failed syncs resubmitted with exponential backoff delays (checked every 30s)
- **Queue Processing**: Continuous monitoring of command queue for new operations via INBOUND_QUEUES

### Error Handling & Conflict Resolution

#### Network Failure Handling:
- **Timeout Management**: Configurable send/receive timeouts with automatic retry
- **Connection Recovery**: Automatic reconnection attempts on network interruptions
- **Duplicate Prevention**: Command deduplication prevents repeated submissions
- **Queue Persistence**: Commands survive application restarts via JSON file

#### Data Conflict Strategies:
- **Server Priority**: In conflicting updates, server version typically wins
- **Manual Resolution**: Administrative interface for complex conflict cases
- **Version Stamping**: Timestamp-based conflict detection and resolution
- **Rollback Support**: Failed operations can rollback local changes if needed

### Monitoring & Diagnostics

#### Client-Side Monitoring:
- **Sync Status Tracking**: Command queue status monitoring in application logs
- **Performance Metrics**: Sync operation timing and success rates
- **Error Reporting**: Failed sync attempts logged with detailed error messages
- **Network Monitoring**: Connection health and latency tracking

#### Diagnostic Features:
- **Mock Mode Integration**: `AUTOSKLAD_USE_MOCKS=1` enables offline development
- **Verbose Logging**: Detailed sync operation logging for troubleshooting
- **Health Checkpoints**: Regular validation of sync system status
- **Performance Profiling**: Measurement of sync operation performance metrics

### Integration with Client Architecture

#### With Qt Application (`main.py`):
- **Thread Launch**: Sync thread initialized during Qt app startup sequence
- **Shared Resources**: Database sessions shared between GUI and sync threads
- **Signal Communication**: Qt signals bridge hardware events to sync processing
- **Shutdown Coordination**: Graceful stop coordination between GUI and sync threads

#### With Local Database:
- **Change Interception**: Decorators/triggers capture database changes
- **Queue Population**: Successful commit creates command in queue file
- **Concurrent Access**: SQLite WAL mode enables multi-threaded database access
- **Transaction Coordination**: Sync operations coordinate with user UI transactions

#### With Hardware Systems:
- **Command Generation**: Hardware actions (tool loading/dispensing) create sync commands
- **Real-Time Sync**: Critical operations trigger immediate sync attempts
- **Offline Buffering**: Hardware operation succeeds locally even without network
- **Sync Prioritization**: Critical state changes prioritized over background operations

## 4. Hardware Managers

Physical device interfaces for vending machine and barcode scanner integration.

### Serial Manager (`BarcodeScanner/SerialManager.py`):
- **Arduino Communication**: RS-232 serial protocol for mechanical control
- **Command Format**: `$<command_number>\r\n` protocol
- **Response Handling**: Parse controller responses and emit Qt signals
- **Threading**: Background serial I/O without blocking GUI

### Barcode Manager (same `SerialManager.py`):
- **Scanner Interface**: Serial communication with barcode/RFID readers
- **Data Parsing**: Extract barcode data and emit to GUI
- **Multiple Formats**: Support for different scanner protocols

### Mock Managers (`BarcodeScanner/MockSerialManager.py`):
- **Simulation Mode**: Software-emulated hardware behavior
- **Development Support**: Full functionality without physical hardware
- **Signal Emission**: Same Qt signals as real hardware
- **Activation**: Enabled via `AUTOSKLAD_USE_MOCKS=1` environment variable

## 5. Events System (`EventsSystem/`)

Event-driven architecture connecting GUI actions to business logic and hardware.

### Components:
- **`Executor.py`**: Central event processor orchestrating operations
- **`events.py`**: Event definitions and handlers
- **`action_*.py`**: Action implementations (DB, HTTP, serial, etc.)
- **`hendlers.py`**: Event handler implementations
- **`state_router.py`**: State-based event routing

### Integration Points:
- **Hardware Response Handler**: Processes Serial/Barcode manager signals
- **GUI Event Dispatcher**: Routes Qt button clicks to appropriate actions
- **Database Integration**: Executes CRUD operations based on events
- **UI State Updates**: Changes screen content in response to events

## 6. Local Database System (`DB/`)

SQLite-based local data storage for offline operation and caching.

### Structure:
- **`Data/`**: Database connection and schema management
- **`Models/`**: SQLAlchemy model definitions
- **`Engine/`**: CRUD operation classes (40+ specific to entities)
- **`BaseCRUD.py`**: Common database operations base class

### Database Files:
- **`DB/Data/vending.db`**: Main application data
- **`dbSync/Model/sync.db`**: Synchronization metadata and queue state
- **`command_queue.json`**: Sync command persistence (in client root directory)

### Initialization (`Create_db.py`):
- Automatic database creation on first run
- Schema setup with foreign keys and constraints
- Seed data population (roles, initial configuration)

## 7. Configuration System (`config.json`)

Centralized JSON configuration file with environment-specific settings.

### Key Sections:
#### Network Configuration:
```json
{
  "network": {
    "ip": "127.0.0.1",
    "port": 8080
  }
}
```

#### Server Connection:
```json
{
  "server": {
    "ip": "127.0.0.1",
    "port": 8000,
    "token": "token11111",
    "secret": "hmac_secret_key",
    "aes": "16byteslongkey!!",
    "sender_timeout": 15,
    "receiver_timeout": 30
  }
}
```

#### Hardware Ports (Platform-Specific):
```json
{
  "serial": { "port": "COM29", "baudrate": 9600 },
  "barcode": { "port": "COM1", "baudrate": 9600 },
  "dev": { "ttyUSB": "/dev/ttyUSB0", "serial": "/dev/serial0" }
}
```

#### Operational Locks and Logs:
```json
{
  "locks": { "load_locked": 0, "drop_locked": false },
  "logs": { "critical_errors": [] }
}
```

## 8. State Machine Management

Finite State Machine (FSM) driving GUI navigation and workflow control.

### Core Components:
- **`FMS.py`**: Transitions library-based FSM implementation
- **`state_map.py`**: Transition definitions and conditions
- **`converter_xml_2.py`**: State machine YAML/JSON processing
- **`maps.py`**: Map definitions and current state tracking

### Workflow States (33+ screens):
- **Authentication**: `screen_3_authorization`
- **User Selection**: `screen_6_user`, `screen_7_select_group`
- **Tool Operations**: `screen_8_select_tool`, `screen_11_tool_issued`
- **Mass Operations**: `screen_15_mass_load`, `screen_17_mass_drop`
- **Management**: `screen_19_management_group`, `screen_20_management_tool`
- **Administrative**: `screen_26_admin`, `screen_28_net_options`

## 9. Arduino/BarcodeScanner Integration

External hardware directories with embedded system code.

### Arduino Controller (`client/Arduino/`):
- **Firmware**: Microcontroller code for mechanical vending operations
- **Protocols**: Serial command sets for motor control and sensors
- **Safety**: Timeout handling and error recovery

### BarcodeScanner (`client/BarcodeScanner/`):
- **Handling Modules**: Encrypted and secure serial communication
- **Manager Classes**: Hardware abstraction layer
- **Mock Implementation**: Full simulation for development

## 10. Utility Modules

Supporting functionality and cross-cutting concerns.

### Core Platform Detection (`Core/platforms.py`):
- **OS Recognition**: Windows vs Linux vs Raspberry Pi detection
- **Platform-Specific Logic**: Hardware configuration differences

### Synchronization Configuration (`Core/sync_config.py`):
- **Sync Parameters**: Server connection and AES key management
- **Dynamic Configuration**: Runtime database-driven settings

### System Integration (`Core/System.py`):
- **Platform Abstractions**: OS-specific system calls
- **Process Management**: Application lifecycle handling

### Logging and Testing (`client/logs/`, `client/Tests/`):
- **Log Analysis**: Event and error logging infrastructure
- **Test Suites**: Unit and integration test frameworks

## 11. Application Startup Sequence

### Multi-Threaded Initialization:
1. **Database Check**: Ensure `vending.db` and `sync.db` exist and are valid
2. **Configuration Load**: Read `config.json` settings
3. **Embedded Server**: Start FastAPI server on configured port
4. **Hardware Managers**: Initialize Serial/Barcode managers
5. **GUI Initialization**: Create Qt application and main window
6. **State Machine**: Load initial screen transition maps
7. **Event Binding**: Connect GUI signals to hardware/services

### Thread Management:
- **Qt Main Thread**: GUI rendering and user interaction
- **FastAPI Thread**: HTTP server and sync processing
- **Hardware Threads**: Serial communication and data processing
- **Sync Runner**: Background synchronization operations

## 12. Development and Testing Features

### Mock Mode Activation:
```bash
# On Linux/MacOS
export AUTOSKLAD_USE_MOCKS=1
python main.py

# On Windows PowerShell
$env:AUTOSKLAD_USE_MOCKS="1"
python main.py
```

Enables full application testing without physical hardware by replacing managers with software simulations that emit the same signals as real hardware.

### Platform-Specific Behavior:
- **Windows**: `COM` ports for hardware communication
- **Linux/Raspberry Pi**: `/dev/ttyUSB*` and `/dev/serial*` devices
- **Mock Mode**: Environment variable overrides hardware detection

## Architecture Benefits

- **Offline Operation**: Local database allows complete functionality without network
- **Hardware Abstraction**: Mock mode enables full development/testing without physical devices
- **Real-Time Synchronization**: Background sync maintains data consistency with server
- **Robust State Management**: FSM ensures logical workflow progression
- **Multi-Threaded**: GUI remains responsive during I/O operations
- **Cross-Platform**: Supports Windows development and Linux deployment
- **Event-Driven**: Clean separation between UI, business logic, and hardware layers

This comprehensive client architecture creates a sophisticated tool management system capable of both standalone operation and seamless integration with centralized server infrastructure.
