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
- **`mass_drop_router`**: Bulk tool dropping
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

Comprehensive bidirectional data synchronization system managing multi-device data consistency through command-based synchronization protocol.

### Architecture Overview

The synchronization service implements a sophisticated **Command Pattern** architecture where all data changes are captured as commands that flow bidirectionally between server and client devices. This ensures eventual consistency across distributed warehouse systems.

### Core Components

#### Command-Based Synchronization Architecture:
- **`SyncProcessor`**: Central coordinator handling handshake, push, and pull operations with conflict resolution
- **`CommandQueue`**: In-memory queues for staging commands before sync operations
- **`CommandRunner`**: Background thread managing per-device synchronization cycles
- **`TransportService`**: HTTP client with AES-encrypted communication to remote sync endpoints

#### Data Processing Pipeline:
- **`DataMapper`**: Translates field mappings between differing database schemas
- **`DataTransformer`**: Handles business logic validation and data preprocessing/postprocessing
- **`ConflictManager`**: Detects and resolves data conflicts using configurable strategies
- **`BatchProcessor`**: Executes atomic database operations in transaction blocks with ALL_OR_NOTHING rollback strategy
- **`RetryManager`**: Manages failed sync attempts with exponential backoff

#### Rollback & Compensation Components (NEW):
- **`SnapshotManager`**: Captures record state before modifications for compensation-based rollback
- **`IdempotencyManager`**: Prevents duplicate batch execution using unique tokens
- **`BatchExecutionCRUD`**: Tracks batch execution metadata and status

#### Schema Management:
- **`SchemaCache`**: SHA256-hashed cache of schema mappings to avoid repeated analysis
- **`SchemaAnalyzer`**: Generates field mappings between client/server schema differences
- **`JSONSchemaValidator`**: Validates incoming/outgoing JSON payloads against predefined schemas

### Synchronization Protocol & Workflow

#### 1. Initial Handshake (`/sync/handshake`)
**Purpose**: Establishes schema compatibility and creates field mappings between client and server databases.

**Process**:
1. Client sends SHA256 hash of its database schema (table field definitions)
2. Server validates schema JSON structure
3. Server checks `SchemaCache` for existing mapping by hash
4. If cache miss: `SchemaAnalyzer` generates field mappings between client and server schemas
5. Mappings stored in cache under client schema hash
6. Server returns `{mapping: {...}, schema_hash: "client_hash"}`
7. Client stores mappings for data transformation during sync

#### 2. Pull Operation (`/sync/pull?device=<id>&since=<timestamp>`)
**Purpose**: Server sends pending changes to client for local application.

**Process**:
1. Client requests pull with `since` timestamp (last successful sync)
2. Server queries `Command` table for pending commands on device queue
3. Retrieves associated data from `Record` table for each command
4. Applies `DataMapper` to transform server data → client format using cached mappings
5. Applies `DataTransformer.postprocess()` for business rule adjustments
6. Returns `{"schema_hash": "client_hash", "commands": [{id, table, operation, data, last_modified}]}`

#### 3. Push Operation (`/sync/push?device=<id>`)
**Purpose**: Client sends local changes to server for global synchronization.

**Process**:
1. Client encrypts command list with AES-CBC and sends via HTTP
2. Server validates JSON schema and decrypts payload
3. **Duplicate Filter**: Checks for existing records (prevents duplicate ADD operations)
4. **Preprocessing**: Each command validated and preprocessed through `DataTransformer`
5. **Conflict Detection**: `ConflictManager` identifies structural/data conflicts
6. **Data Mapping**: Converts client field names to server equivalents
7. **Batch Execution**: `BatchProcessor` applies changes atomically in transactions
8. **Status Update**: Command statuses logged to `CommandStatus` table
9. **Retry Planning**: Failed commands scheduled for retry with `RetryManager`
10. Returns `[{"id": "cmd_id", "status": "COMPLETED|FAILED", "error": "..."}]`

### Command Queue System (`command_queue.json`)

The command queue is a **persistence layer** for sync commands, ensuring no commands are lost during server restarts or network interruptions.

#### Stored Command Structure:
```json
{
  "id": "uuid",                 // Unique command identifier
  "table": "Tools",             // Target database table
  "operation": "add|update|delete", // CRUD operation type
  "data": { ... },              // Record data payload
  "status": "pending|done|failed", // Processing status
  "timestamp": "RFC3339"        // When command was created
}
```

#### Queue Purpose & Data Flow:
1. **Client-Side Generation**: UI/database changes captured via decorators/interceptors
2. **Queue Persistence**: Commands stored in `command_queue.json` for crash recovery
3. **Sync Transmission**: AES-encrypted commands pushed to server's `/sync/push`
4. **Server Processing**: Commands validated, applied to main database
5. **Status Response**: Client receives completion status per command
6. **Queue Cleanup**: Successfully processed commands removed from queue

#### Example Command Records:
- `{"table": "Tools", "operation": "add", "data": {"name": "Drill 5mm"}, "status": "done", "timestamp": "2025-09-26T16:51:32Z"}`
- `{"table": "Cell", "operation": "update", "data": {"id": 3, "status_id": 5, "tools_id": 4}, "status": "done", "timestamp": "2025-09-27T12:18:57Z"}`
- `{"table": "History", "operation": "add", "data": {"user_id": 1, "tools_id": 4, "description": "Tool issued"}, "status": "done", "timestamp": "2025-09-27T12:18:57Z"}`

### Database Models for Sync

#### Command Table Structure:
```sql
CREATE TABLE Command (
  id INTEGER PRIMARY KEY,
  table_name VARCHAR NOT NULL,    -- Target table name
  operation VARCHAR NOT NULL,     -- add|update|delete
  record_id INTEGER,              -- Affected record ID (for updates/deletes)
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  device_number INTEGER NOT NULL  -- Source device ID
);
```

#### Record Table Structure:
```sql
CREATE TABLE Record (
  id INTEGER PRIMARY KEY,
  command_id INTEGER REFERENCES Command(id),
  table_name VARCHAR NOT NULL,
  record_id INTEGER,              -- The actual data record ID
  data BLOB,                      -- JSON-serialized record data
  last_modified TIMESTAMP
);
```

#### CommandStatus Table Structure:
```sql
CREATE TABLE CommandStatus (
  id INTEGER PRIMARY KEY,
  command_id INTEGER REFERENCES Command(id),
  status VARCHAR NOT NULL,        -- pending|processing|completed|failed
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  error_message TEXT              -- Optional error details
);
```

### Encryption & Security

#### AES-CBC Encryption Protocol:
- **Key Source**: Configured in `options.py` (`AES_KEY`)
- **IV Generation**: Random 16-byte IV prepended to ciphertext
- **Encryption**: AES-CBC with PKCS7 padding
- **Transport**: Base64-encoded for HTTP transport
- **Authentication**: Device ID parameters for routing

#### Secure Communication Flow:
1. Client encrypts sync payload: `AES_ENCRYPT(IV + data, AES_KEY)`
2. HTTP POST to `/sync/push?device=<id>` with encrypted body
3. Server derives key from config and decrypts
4. Response encrypted with new IV and returned
5. Client decrypts to get sync status results

### Threading & Performance

#### Per-Device Threading Model:
- **Main Thread**: Server lifespan launches device-specific threads
- **Sync Thread/Thread**: Dedicated thread per vendor device
- **Scheduler Threads**: Background job scheduling for sync cycles
- **HTTP Threads**: FastAPI thread pool for concurrent sync requests

#### Sync Scheduling:
- **Sender Job**: Every `SENDER_TIMEOUT` seconds (default 30), pending commands pushed
- **Receiver Job**: Every `RECEIVER_TIMEOUT` seconds (default 60), server pulls new data
- **Retry Schedule**: Failed pushes retried with exponential backoff via RetryManager

### Error Handling & Resilience

#### Conflict Resolution Strategies:
- **Structure Conflicts**: SchemaAnalyzer generates field mappings
- **Data Conflicts**: `ConflictManager` applies merge strategies (server-wins, client-wins, etc.)
- **Validation Failures**: Commands marked failed with detailed error messages
- **Network Failures**: Automatic retry with increasing delays
- **Schema Changes**: Handshake renegotiation on schema mismatch

### Monitoring & Diagnostics

#### SyncMonitor Metrics:
- Success/failure counts per operation type
- Average operation duration
- Failed command analysis

#### DiagnosticLogger Events:
- Handshake schema validation results
- Push/pull operation timing
- Command processing status
- Conflict detections and resolutions

### Rollback & Compensation Architecture (NEW)

The server now implements a sophisticated **compensation-based rollback** system using the **Saga Pattern** to ensure data integrity during batch synchronization operations from multiple client devices. This prevents partial failures from leaving the database in an inconsistent state.

#### SnapshotManager (`dbSync/Logic_v2/SnapshotManager.py`)

**Purpose**: Captures database record state BEFORE modifications to enable precise rollback through compensation when batch operations fail.

**Key Responsibilities**:
- Capture current record state before UPDATE/DELETE operations
- Store snapshots in `sync.db` (survives `work.db` transaction rollback)
- Generate inverse operations from snapshots on batch failure
- Automatic cleanup of old snapshots (configurable retention period, default 30 days)

**Core Methods**:

1. **`capture_snapshot(command_id, table, record_id, operation)`**
   - Called synchronously BEFORE each UPDATE/DELETE operation in a batch
   - Queries current record state from `work.db` (or MySQL)
   - Serializes complete record state to JSON
   - Stores in `CommandSnapshot` table in `sync.db`
   - Returns `True` on successful capture, `False` on failure

2. **`generate_compensation_for_command(command_id)`**
   - Retrieves snapshot for a specific failed command
   - Generates the inverse operation based on original operation type:
     - INSERT → DELETE (remove the newly created record)
     - UPDATE → UPDATE (restore to previous field values)
     - DELETE → INSERT (restore the deleted record completely)
   - Returns compensation operation dictionary or `None` if unavailable

3. **`cleanup_old_snapshots(older_than_days=30)`**
   - APScheduler job executed daily at 3:00 AM
   - Deletes snapshots older than the retention period
   - Prevents unbounded database growth
   - Returns count of deleted snapshot records

**Example Workflow**:
```python
# Scenario: Updating a Cell record during mass load
snapshot_manager.capture_snapshot(
    command_id=456,
    table="Cell",
    record_id=12,
    operation="update"
)
# Snapshot stored: {"id": 12, "status_id": 1, "tools_id": None, "device_id": 2}

# If batch fails later, generate compensation:
compensation = snapshot_manager.generate_compensation_for_command(456)
# Returns: {
#   "table": "Cell",
#   "operation": "update",
#   "id": 12,
#   "data": {"status_id": 1, "tools_id": None}
# }
```

**Database Schema (in sync.db)**:
```sql
CREATE TABLE CommandSnapshot (
  id INTEGER PRIMARY KEY,
  command_id INTEGER NOT NULL,   -- FK to Command.id
  table_name VARCHAR NOT NULL,   -- Target table: "Cell", "Tools", "History", etc.
  record_id INTEGER,             -- ID of record being modified
  snapshot_data TEXT,            -- JSON snapshot: {"field": "value", ...}
  operation VARCHAR NOT NULL,    -- "insert", "update", or "delete"
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### IdempotencyManager (`dbSync/Logic_v2/IdempotencyManager.py`)

**Purpose**: Ensures exactly-once processing of client batch operations using unique idempotency tokens, preventing duplicate execution when clients retry failed requests.

**Key Responsibilities**:
- Generate cryptographically unique tokens (UUID v4) for batch operations
- Track token status throughout batch lifecycle
- Detect and reject duplicate batch submissions
- Automatic cleanup of expired tokens (default 24-hour TTL)

**Core Methods**:

1. **`generate_token(batch_id=None)`**
   - Creates a new UUID v4 token
   - Stores `IdempotencyToken` record with PENDING status
   - Sets expiration timestamp (+24 hours from creation)
   - Returns token string for client to include in request headers

2. **`is_duplicate(token)`**
   - Queries `IdempotencyToken` table for existing token
   - Validates token hasn't expired
   - Returns `True` if token already processed, `False` if new
   - Used by sync endpoints to short-circuit duplicate requests

3. **`mark_completed(token, batch_id, status='COMPLETED')`**
   - Updates token status after successful/failed batch processing
   - Links token to `BatchExecution` record via `batch_id`
   - Records completion timestamp
   - Enables cache-based response for future duplicate requests

4. **`cleanup_expired_tokens()`**
   - APScheduler job (daily execution)
   - Removes tokens past their expiration timestamp
   - Returns count of purged tokens

**Example Idempotency Flow**:
```python
# Endpoint receives batch with idempotency token
token = request.headers.get('Idempotency-Token')

# Check for duplicate submission
if idempotency_manager.is_duplicate(token):
    # Return cached result from previous execution
    cached_result = get_cached_batch_result(token)
    return JSONResponse(cached_result)

# First time processing this token
batch_id = str(uuid.uuid4())
results = batch_processor.execute_batch(commands)

# Mark token as processed
idempotency_manager.mark_completed(token, batch_id, 
    'COMPLETED' if all_success(results) else 'FAILED')

return JSONResponse(results)
```

**Database Schema (in sync.db)**:
```sql
CREATE TABLE IdempotencyToken (
  id INTEGER PRIMARY KEY,
  token VARCHAR UNIQUE NOT NULL, -- UUID v4 token from client
  batch_id VARCHAR,              -- FK to BatchExecution.batch_id
  status VARCHAR NOT NULL,       -- PENDING, COMPLETED, FAILED
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  expires_at TIMESTAMP           -- created_at + 24 hours
);
```

#### Enhanced BatchProcessor

The `BatchProcessor` implements **ALL_OR_NOTHING** transaction semantics with automatic rollback on any failure:

**Key Enhancements**:
1. **Nested Transactions (Savepoints)**: Uses `session.begin_nested()` for atomic batch execution
2. **Pre-Execution Snapshot Capture**: Records state before each destructive operation
3. **Immediate Rollback**: Any single command failure triggers complete batch rollback
4. **Granular Result Tracking**: Per-command success/failure with error details

**Execution Flow**:
```python
def execute_batch(self, operations: List[Operation]) -> List[OperationResult]:
    results = []
    try:
        with self.session.begin_nested():  # Create SAVEPOINT
            for op in operations:
                try:
                    # 1. Capture pre-modification snapshot
                    snapshot_manager.capture_snapshot(
                        command_id=op['command_id'],
                        table=op['table'],
                        record_id=op.get('id'),
                        operation=op['operation']
                    )
                    
                    # 2. Execute the database operation
                    result = self.sync_manager.process_sync_command(op)
                    
                    # 3. Record success
                    results.append({
                        "command_id": op['command_id'],
                        "success": True,
                        "new_id": result.get('id')
                    })
                    
                except Exception as e:
                    # 4. Record failure and abort batch
                    results.append({
                        "command_id": op['command_id'],
                        "success": False,
                        "error": str(e)
                    })
                    raise  # Trigger savepoint rollback
                    
    except SQLAlchemyError:
        # ROLLBACK SAVEPOINT - all work.db changes undone
        # snapshots in sync.db preserved for audit
        pass
    
    return results
```

**Rollback Guarantees**:
- **All-or-Nothing**: Either all commands succeed or none persist
- **Database Consistency**: Work database returns to pre-batch state on failure
- **Audit Trail**: Snapshots remain in sync.db even after rollback
- **Error Propagation**: Detailed error messages returned for failed commands

#### BatchExecution Tracking

All batch executions are logged in the `BatchExecution` table for monitoring and diagnostics:

**Tracked Metadata**:
```python
batch_execution = BatchExecution(
    batch_id=str(uuid.uuid4()),
    status='IN_PROGRESS',
    total_commands=len(commands),
    successful_commands=0,
    failed_commands=0,
    started_at=datetime.now(),
    error_message=None
)

# After batch completes
batch_execution.status = 'COMPLETED' if all_success else 'FAILED'
batch_execution.successful_commands = sum(1 for r in results if r['success'])
batch_execution.failed_commands = sum(1 for r in results if not r['success'])
batch_execution.completed_at = datetime.now()
batch_execution.error_message = first_error_message if failed else None
```

**Database Schema (in sync.db)**:
```sql
CREATE TABLE BatchExecution (
  id INTEGER PRIMARY KEY,
  batch_id VARCHAR UNIQUE NOT NULL,
  status VARCHAR NOT NULL,       -- PENDING, IN_PROGRESS, COMPLETED, FAILED, ROLLED_BACK
  total_commands INTEGER,
  successful_commands INTEGER DEFAULT 0,
  failed_commands INTEGER DEFAULT 0,
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  error_message TEXT
);
```

### Integration Points

#### With FastAPI Server:
- **Lifespan Handler**: Launches device sync threads on startup
- **Router Mounting**: `/sync` endpoints route to `sync_router`
- **Database Sessions**: Shared work database access
- **Rollback Coordination**: Batch failures don't corrupt server state

#### With Main Database:
- **Change Capture**: Transaction post-hooks create sync commands
- **Atomic Operations**: Batch changes apply in database transactions with rollback protection
- **Constraint Validation**: Database foreign keys enforced during sync
- **Snapshot Isolation**: Snapshots in sync.db survive work.db rollbacks

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
