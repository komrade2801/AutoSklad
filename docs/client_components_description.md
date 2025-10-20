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
- **Port Configuration**: Default 8080 (configurable via `config.json`)
- **Router Mounting**: `/sync` endpoints for bidirectional data exchange
- **Threading Model**: Runs in separate thread to avoid blocking GUI
- **Shared Database Access**: Same SQLite databases as GUI thread

### Synchronization Endpoints (`dbSync/Transport/routers.py`):
- **`/push`**: Send commands to server (encrypted with AES)
- **`/pull`**: Receive pending commands from server
- **`/handshake`**: Initial synchronization handshake with schema validation

## 3. Synchronization Service (`dbSync/`)

Comprehensive bidirectional synchronization system between client and server.

### Core Components:
- **`Logic_v2/`**: Advanced sync logic with conflict resolution
  - **`CommandQueue.py`**: Background processing queues
  - **`ConflictManager.py`**: Sync conflict strategies
  - **`DataMapper.py`**: Database schema mapping
  - **`JSONSchemaValidator.py`**: Sync payload validation
  - **`SyncManager.py`**: Overall synchronization orchestration
  - **`TransportService.py`**: HTTP client for server communication

- **`Engines/`**: Data transformation engines per entity type
  - **`CRUD.py`**: Generic database operations
  - **`CommandEngine.py`**: Command processing
  - **`RecordEngine.py`**: Record synchronization

- **`Model/`**: Synchronization data models and schemas
- **`setup.py`, `sync_db.py`**: Initialization and bootstrap logic

### Key Features:
- **AES Encryption**: All client-server communication encrypted
- **Background Processing**: Non-blocking sync operations
- **Conflict Resolution**: Automatic merge strategies for data conflicts
- **Schema Validation**: JSON schema validation for sync payloads
- **Retry Logic**: Failed sync automatic retries

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
- **`Model/vending.db`**: Main application data
- **`Model/sync.db`**: Synchronization metadata and queue state
- **`command_queue.json`**: Sync command persistence

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
    "aes": "16byteslongkey!!",
    "sender_timeout": 30,
    "receiver_timeout": 60
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
