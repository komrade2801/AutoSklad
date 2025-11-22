# Server Settings Management and Backup Enhancement Plan

## Overview

This document outlines a comprehensive plan to address the identified issues with server configuration management, database backup functionality, and default settings handling. The plan focuses on making the AutoSklad server easier to administer through a web interface while ensuring safe live updates during runtime.

## IMPLEMENTATION STATUS (v1.0)

### ✅ COMPLETED COMPONENTS

1. **Database Schema** - Settings & DeviceDefaults tables created with proper indexing
2. **Settings CRUD Implementation** - EngineSettings with thread-safe caching, validation, and type conversion
3. **Admin Interface** - REST API endpoints + working settings management page with tabbed navigation
4. **Configuration Files** - JSON-based default settings and device templates with environment variable support
5. **Web Interface** - Fully functional settings page with real-time database access

### 🔄 PARTIALLY IMPLEMENTED

- **Migration Strategy** - Basic framework established, full migration not implemented
- **Settings Categories** - Network, security, database, sync visualized, frontend not fully categorized

### ❌ NOT YET IMPLEMENTED

- **Maintenance Mode** - Server shutdown-proof updates during runtime
- **Scheduler Integration** - Pause/resume for safe settings reloads
- **Enhanced Backup System** - JSON compression with integrity checks
- **Settings Validation** - Range/type validation on frontend
- **Audit Logging** - Settings change history and user tracking

## Table of Contents

1. [Current State Assessment](#current-state-assessment)
2. [Proposed Settings Management System](#proposed-settings-management-system)
3. [Configuration Database Schema](#configuration-database-schema)
4. [Settings CRUD Implementation](#settings-crud-implementation)
5. [Admin Interface Development](#admin-interface-development)
6. [Server Maintenance Mode](#server-maintenance-mode)
7. [Scheduler Integration for Safe Reloads](#scheduler-integration-for-safe-reloads)
8. [Backup System Improvements](#backup-system-improvements)
9. [Default Configuration Files](#default-configuration-files)
10. [Migration Strategy](#migration-strategy)
11. [Testing and Validation](#testing-and-validation)

## Current State Assessment

### Settings Management Issues

- **Hardcoded Constants**: Server settings are mostly hardcoded in `server/options.py`
- **No Hot-Reload**: Settings changes require server restart
- **No Admin Interface**: No way to modify settings through the web UI
- **Limited Safety**: Concurrent modifications could cause issues
- **Poor Separation**: Network, timing, and security settings mixed with code

### Backup System Issues

- **Pickle Security**: Uses pickle for data serialization (not secure for distributed systems)
- **No Cleanup**: Backup directory accumulates without cleanup
- **No Backup Validation**: Missing integrity checks
- **Process Termination**: Kills processes instead of graceful handling
- **No Compression**: Wasteful disk usage

### Default Configuration Issues

- **Hardcoded Defaults**: Database seeding data is hardcoded in `server/Core/default.py`
- **No Flexibility**: Cannot customize per-deployment without code changes
- **Maintenance Burden**: Changing test users or hardware configurations requires code edits

## Proposed Settings Management System

### Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Admin UI  │───▶│ Settings CRUD   │───▶│   Settings DB   │
│                 │    │   Layer         │    │   Table         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                        │
                              ▼                        ▼
                   ┌─────────────────┐      ┌─────────────────┐
                   │   In-Memory     │      │   Persistence    │
                   │    Cache        │◀─────│   Layer          │
                   │                 │      │                 │
                   └─────────────────┘      └─────────────────┘
                              ▲                        │
                              │                        ▼
                   ┌─────────────────┐      ┌─────────────────┐
                   │ Server Startup │      │ Change Tracking │
                   │   Loading       │      │   & Audit       │
                   └─────────────────┘      └─────────────────┘
```

### Benefits

- **Shutdown-Proof**: Persists across server restarts
- **Multi-User Safe**: Concurrent access protected with locks
- **Versioned**: Tracks changes with timestamps
- **Auditable**: Maintains history of settings modifications
- **Type-Safe**: Validates setting values before storage
- **Admin-Friendly**: Web interface for management
- **Hot-Reload**: Apply changes without restart

## Configuration Database Schema

### Settings Table

```sql
CREATE TABLE Settings (
    id INTEGER PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT NOT NULL,
    value_type VARCHAR(20) DEFAULT 'str',
    category VARCHAR(50) DEFAULT 'general',
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER REFERENCES User(id),
    is_sensitive BOOLEAN DEFAULT FALSE,
    requires_restart BOOLEAN DEFAULT TRUE,
    validation_rules TEXT
);
```

### System Settings Categories

1. **Network Settings**: Host, port, URLs
2. **Database Settings**: Connection strings, timeouts
3. **Security Settings**: AES keys, JWT secrets
4. **Sync Settings**: Sender/Receiver timeouts, device configs
5. **Frontend Settings**: UI customizations, pagination limits
6. **Hardware Settings**: Serial ports, baud rates, network interfaces

### Initial Settings Population

```sql
INSERT INTO Settings (key, value, value_type, category, description, requires_restart) VALUES
-- Network
('Host', '127.0.0.1', 'str', 'network', 'Server bind address', true),
('port', '8000', 'int', 'network', 'Server port', true),
-- Sync
('SENDER_TIMEOUT', '30', 'int', 'sync', 'Sync push interval (seconds)', false),
('RECEIVER_TIMEOUT', '60', 'int', 'sync', 'Sync pull interval (seconds)', false),
-- Security
('AES_KEY', '16byteslongkey!!', 'str', 'security', 'Encryption key for sync', true),
('SECRET_KEY', 'random-secret', 'str', 'security', 'JWT signing key', true);
```

## Settings CRUD Implementation

### BaseSettingsCRUD Class

```python
from DB.Engine.CRUD import BaseCRUD
from DB.Models.Settings import Settings
from threading import Lock
from typing import Dict, Any, Optional
import json
from datetime import datetime

class SettingsCRUD(BaseCRUD):
    def __init__(self, session=None):
        super().__init__(session=session, model=Settings)
        self._cache: Dict[str, Any] = {}
        self._cache_lock = Lock()
        self._type_casts = {
            'str': str,
            'int': int,
            'float': float,
            'bool': lambda x: bool(int(x)),  # Store as 0/1
            'json': json.loads
        }

    def load_all_settings(self) -> Dict[str, Any]:
        """Load all settings into cache"""
        with self._cache_lock:
            settings = self.get_all()
            for setting in settings:
                value = self._cast_value(setting.value, setting.value_type)
                self._cache[setting.key] = value
            return self._cache.copy()

    def get_setting(self, key: str) -> Optional[Any]:
        """Get cached setting value"""
        with self._cache_lock:
            return self._cache.get(key)

    def set_setting(self, key: str, value: Any, user_id: int = None) -> bool:
        """Set setting with validation and cache update"""
        with self._cache_lock:
            # Validate setting exists
            existing = self.find_by_key(key)
            if not existing:
                return False

            # Type validation
            string_value = self._stringify_value(value, existing.value_type)

            # Update database
            if not self.update(existing.id, value=string_value, updated_at=datetime.now(), updated_by=user_id):
                return False

            # Update cache
            self._cache[key] = value
            return True

    def reload_cache(self) -> Dict[str, Any]:
        """Reload cache from database (for hot-reload)"""
        with self._cache_lock:
            self._cache.clear()
            return self.load_all_settings()
```

### Setting Types and Validation

```python
class SettingValidator:
    @staticmethod
    def validate_network_setting(key: str, value: str) -> bool:
        if key == 'Host':
            # IPv4 validation
            pass
        elif key == 'port':
            # Port range 1-65535
            port = int(value)
            return 1 <= port <= 65535
        return True

    @staticmethod
    def validate_timeout_setting(key: str, value: int) -> bool:
        return isinstance(value, int) and value > 0 and value <= 3600  # Max 1 hour
```

## Admin Interface Development

### API Endpoints

```python
# server/API/backend/endpoints/settings.py

from fastapi import APIRouter, Depends, HTTPException
from DB.Engine.SettingsCRUD import SettingsCRUD
from DB.Data.sqlite_db import get_db
from sqlalchemy.orm import Session
from typing import Dict, List, Any
from pydantic import BaseModel

router = APIRouter()

class SettingUpdate(BaseModel):
    value: Any
    user_id: Optional[int] = None

class SettingResponse(BaseModel):
    id: int
    key: str
    value: Any
    value_type: str
    category: str
    description: str
    requires_restart: bool
    updated_at: datetime

@router.get("/settings", response_model=List[SettingResponse])
def get_all_settings(db: Session = Depends(get_db)):
    crud = SettingsCRUD(db)
    settings = crud.get_all()
    return [SettingResponse(**s.__dict__) for s in settings]

@router.put("/settings/{key}")
def update_setting(key: str, update: SettingUpdate, db: Session = Depends(get_db)):
    crud = SettingsCRUD(db)
    if not crud.set_setting(key, update.value, update.user_id):
        raise HTTPException(status_code=400, detail="Invalid setting or update failed")
    return {"message": "Setting updated successfully"}

@router.post("/settings/reload")
def reload_settings(maintenance_mode: bool = False):
    global maintenance_mode
    if maintenance_mode:
        maintenance_mode = True  # Block new requests during reload
        # Perform scheduler pause/resume logic
        pass
    # reload cache logic
    return {"message": "Settings reloaded"}
```

### Frontend Integration

Add "Settings" to admin navigation with permissions check:

```javascript
// frontend/scripts/settings.js

async function loadSettings() {
    const response = await fetch('/backend/settings');
    const settings = await response.json();

    // Group by category
    const grouped = settings.reduce((acc, setting) => {
        if (!acc[setting.category]) acc[setting.category] = [];
        acc[setting.category].push(setting);
        return acc;
    }, {});

    renderSettingsTable(grouped);
}

async function updateSetting(key, value) {
    const response = await fetch(`/backend/settings/${key}`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({value: value})
    });

    if (!response.ok) {
        showError('Failed to update setting');
        return;
    }
    showSuccess('Setting updated');
    // Check if restart required
    if (setting.requires_restart) showRestartNotice();
}
```

## Server Maintenance Mode

### Middleware Implementation

```python
# server/main.py
from fastapi import Request, HTTPException
from starlette.responses import JSONResponse
import asyncio
from contextlib import asynccontextmanager

maintenance_mode = False

@app.middleware("http")
async def maintenance_middleware(request: Request, call_next):
    if maintenance_mode and request.url.path.startswith("/backend"):
        return JSONResponse(
            status_code=503,
            content={
                "detail": "Server is in maintenance mode. Please try again later.",
                "retry_after": 30
            }
        )
    return await call_next(request)
```

### Advanced Maintenance Modes

```python
class MaintenanceManager:
    def __init__(self):
        self._mode = False
        self._lock = asyncio.Lock()
        self._waiting_requests = 0

    @asynccontextmanager
    async def maintenance_context(self, timeout: int = 300):
        """Context manager for maintenance windows"""
        async with self._lock:
            # Wait for active requests to complete
            start_time = asyncio.get_event_loop().time()
            while self._waiting_requests > 0:
                await asyncio.sleep(0.1)
                if asyncio.get_event_loop().time() - start_time > timeout:
                    break

            self._mode = True
            try:
                yield
            finally:
                self._mode = False
```

## Scheduler Integration for Safe Reloads

### Scheduler Lifecycle Management

```python
# server/dbSync/Runner.py

class SynchronizedScheduler(BackgroundScheduler):
    """Enhanced scheduler with pause/resume coordination"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pause_event = asyncio.Event()
        self._pause_event.set()  # Initially running

    async def pause_for_maintenance(self, timeout: int = 60):
        """Pause all jobs waiting for current executions to complete"""
        # Signal pause
        self._pause_event.clear()

        # Wait for jobs to acknowledge pause
        await asyncio.wait_for(self._all_jobs_paused.wait(), timeout=timeout)

    async def resume_after_maintenance(self):
        """Resume job execution"""
        self._pause_event.set()
        self._all_jobs_paused.clear()

    def _job_wrapper(self, func):
        """Wrap jobs to check pause status"""
        async def wrapped(*args, **kwargs):
            await self._pause_event.wait()  # Wait if paused
            return await func(*args, **kwargs)
        return wrapped
```

### Integration with Settings Reload

```python
# server/main.py

active_schedulers: List[SynchronizedScheduler] = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ... existing device startup ...

    schedulers = []
    for dev in devices:
        scheduler = start_sync(...)  # Returns our scheduler
        schedulers.append(scheduler)

    global active_schedulers
    active_schedulers = schedulers

    yield

    # Shutdown
    for scheduler in schedulers:
        await scheduler.pause_for_maintenance()
        stop_sync(device_id)

@router.post("/settings/reload-safe")
async def safe_reload_settings():
    """Pause-sync-update-resume cycle"""
    global maintenance_mode, active_schedulers

    maintenance_mode = True

    try:
        # Pause all schedulers
        pause_tasks = [sched.pause_for_maintenance() for sched in active_schedulers]
        await asyncio.gather(*pause_tasks, return_exceptions=True)

        # Perform settings update
        settings_crud = SettingsCRUD()
        settings_crud.reload_cache()

        # Apply time-sensitive changes (reschedule jobs)
        for scheduler in active_schedulers:
            scheduler.reschedule_jobs_based_on_new_settings()

        # Resume schedulers
        resume_tasks = [sched.resume_after_maintenance() for sched in active_schedulers]
        await asyncio.gather(*resume_tasks, return_exceptions=True)

        return {"message": "Settings reloaded successfully"}

    except Exception as e:
        return {"error": f"Reload failed: {str(e)}"}
    finally:
        maintenance_mode = False
```

## Backup System Improvements

### Enhanced Backup Manager

```python
# server/Core/backup_advanced.py

import os
import hashlib
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import gzip

class AdvancedBackupManager:
    def __init__(self, backup_dir: str = "db_backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        self.max_backups = 10  # Limit backup history

    def create_backup(self, db_path: str) -> str:
        """Create verified, compressed backup"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}.json.gz"

        backup_path = self.backup_dir / backup_name
        table_data = {}

        # Extract and validate data
        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.cursor()

            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]

            for table in tables:
                cursor.execute(f"SELECT * FROM {table}")
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()

                # Validate data integrity
                table_data[table] = {
                    'columns': columns,
                    'rows': rows,
                    'count': len(rows),
                    'hash': hashlib.sha256(json.dumps(rows).encode()).hexdigest()
                }

            # Compress and save
            with gzip.open(backup_path, 'wt', encoding='utf-8') as f:
                json.dump(table_data, f, default=self._json_serializer, indent=2)

        finally:
            conn.close()

        # Maintain backup limit
        self._cleanup_old_backups()

        return str(backup_path)

    def restore_backup(self, backup_path: str, db_path: str) -> bool:
        """Restore with integrity verification"""
        if not Path(backup_path).exists():
            return False

        with gzip.open(backup_path, 'rt', encoding='utf-8') as f:
            backup_data = json.load(f)

        conn = sqlite3.connect(db_path)
        try:
            conn.execute("PRAGMA foreign_keys = OFF")

            for table_name, table_info in backup_data.items():
                # Verify integrity
                expected_hash = table_info['hash']
                current_hash = hashlib.sha256(
                    json.dumps(table_info['rows'], default=self._json_serializer).encode()
                ).hexdigest()

                if current_hash != expected_hash:
                    raise ValueError(f"Integrity check failed for table {table_name}")

                # Restore table
                self._restore_table(conn, table_name, table_info)

            conn.commit()
            return True

        except Exception:
            conn.rollback()
            raise
        finally:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.close()

    def _restore_table(self, conn, table_name: str, table_info: Dict):
        """Restore single table with schema compatibility"""
        columns = table_info['columns']
        rows = table_info['rows']

        # Check current schema
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        current_columns = [row[1] for row in cursor.fetchall()]

        # Find compatible columns
        compatible_cols = [col for col in columns if col in current_columns]

        if not compatible_cols:
            return  # Skip incompatible table

        # Insert compatible data
        placeholders = ','.join(['?'] * len(compatible_cols))
        query = f"INSERT OR REPLACE INTO {table_name} ({','.join(compatible_cols)}) VALUES ({placeholders})"

        for row in rows:
            row_dict = dict(zip(columns, row))
            compatible_values = [row_dict[col] for col in compatible_cols]
            cursor.execute(query, compatible_values)

    def _cleanup_old_backups(self):
        """Remove old backups beyond limit"""
        backups = sorted(
            self.backup_dir.glob("backup_*.json.gz"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )

        for old_backup in backups[self.max_backups:]:
            old_backup.unlink()

    @staticmethod
    def _json_serializer(obj):
        """Handle non-JSON-serializable objects"""
        if isinstance(obj, bytes):
            return obj.hex()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
```

### Integration with Setup Process

```python
# server/Core/default.py

def run_setup_process_advanced():
    backup_manager = AdvancedBackupManager()

    backup_file = None
    try:
        update_progress("Creating backup", "backup", 0)
        backup_file = backup_manager.create_backup(db_path)

        update_progress("Running database rebuild", "rebuild", 20)
        rebuild_db()

        update_progress("Seeding database", "seed", 60)
        execute()

        update_progress("Verifying backup", "verify", 90)
        # Optional: verify some rows

    except Exception as e:
        if backup_file:
            update_progress("Restoring from backup", "restore", 0)
            backup_manager.restore_backup(backup_file, db_path)
        raise
```

## Default Configuration Files

### External Configuration Structure

```
server/
├── config/
│   ├── default_db.json      # Database seeding templates
│   ├── settings_defaults.json  # Initial settings population
│   └── environment.json     # Environment-specific overrides
```

### Database Defaults Configuration

```json
// config/default_db.json
{
  "devices": [{
    "number": 1,
    "name": "Основной вендинг",
    "signature": {
      "serial_number": 1,
      "cells": {
        "length": ${CELL_COUNT:-210},
        "columns": ${CELL_COLUMNS:-35},
        "rows": ${CELL_ROWS:-6}
      }
    },
    "server": {
      "ip": "${SERVER_IP:-127.0.0.1}",
      "port": ${SERVER_PORT:-8000},
      "aes": "${AES_KEY:-16byteslongkey!!}",
      "sender_timeout": ${SENDER_TIMEOUT:-30},
      "receiver_timeout": ${RECEIVER_TIMEOUT:-60}
    },
    "network": {
      "ip": "${CLIENT_IP:-127.0.0.1}",
      "port": ${CLIENT_PORT:-8080}
    }
  }],
  "test_users": [
    {
      "barcode": "${USER1_BARCODE:-4850357853783}",
      "code": "${USER1_CODE:-1111}",
      "first_name": "${USER1_FIRST:-Максим}",
      "second_name": "${USER1_SECOND:-Кудрявцев}",
      "family": "${USER1_FAMILY:-Иванов}",
      "role_id": "${USER1_ROLE:-1 }"
    }
  ],
  "statuses": [
    {"name": "start_system", "description": "System startup"},
    {"name": "mass_drop_ready", "description": "Mass drop prepared"}
  ],
  "roles_and_pages": {
    "Разработчик": ["screen_1", "screen_2"],
    "Администратор": ["screen_admin", "screen_settings"]
  }
}
```

### Configuration Loading Logic

```python
# server/Core/default.py

import os
import json
from string import Template

class ConfigManager:
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(__file__).parent.parent / config_dir

    def load_default_config(self) -> Dict[str, Any]:
        """Load and interpolate configuration"""
        config_file = self.config_dir / "default_db.json"
        if not config_file.exists():
            return self._get_hardcoded_defaults()

        with open(config_file, 'r', encoding='utf-8') as f:
            template_content = f.read()

        # Environment variable substitution
        template = Template(template_content)
        interpolated = template.safe_substitute(os.environ)

        return json.loads(interpolated)

    def get_device_config(self) -> Dict[str, Any]:
        """Extract device configuration with environment overrides"""
        config = self.load_default_config()
        device_config = config['devices'][0].copy()

        # Apply environment-level overrides
        env_file = self.config_dir / "environment.json"
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                env_overrides = json.load(f)
                self._merge_configs(device_config, env_overrides)

        return device_config
```

## Migration Strategy

### Phase 1: Infrastructure Setup

1. **Create Settings Table**
   - Run migration to create `Settings` table
   - Populate with current `options.py` values

2. **Install Backup Enhancements**
   - Replace `server/Core/backup.py` imports with advanced backup manager
   - Add configuration file handling to `default.py`

### Phase 2: Gradual Migration

1. **Refactor Settings Loading**
   - Modify `server/main.py` to load from Settings table
   - Keep `options.py` as fallback with deprecation warnings

2. **Add Admin Interface**
   - Implement settings endpoints
   - Update frontend with settings management UI

3. **Enhance Backup System**
   - Deploy advanced backup manager
   - Test backup/restore cycles

### Phase 3: Full Adoption

1. **Settings Migration**
   - Move all server settings to database
   - Remove `options.py` dependencies

2. **Configuration Externalization**
   - Replace hardcoded values in `default.py`
   - Document configuration file format

## Testing and Validation

### Unit Tests

```python
# tests/test_settings.py

def test_settings_crud():
    crud = SettingsCRUD()
    crud.load_all_settings()
    assert crud.get_setting('Host') == '127.0.0.1'

    # Test update with callback
    assert crud.set_setting('Host', '192.168.1.1')
    assert crud.get_setting('Host') == '192.168.1.1'

def test_backup_restore():
    manager = AdvancedBackupManager()
    backup_path = manager.create_backup('test.db')

    # Modify database
    # ... make changes ...

    success = manager.restore_backup(backup_path, 'test.db')
    assert success

    # Verify data integrity
    # ... assertions ...
```

### Integration Tests

```python
# tests/test_settings_integration.py

def test_settings_admin_api(client):
    # Test full admin workflow
    response = client.get('/backend/settings')
    assert response.status_code == 200

    # Update setting
    update_resp = client.put('/backend/settings/Host',
                           json={'value': '10.0.0.1'})
    assert update_resp.status_code == 200

    # Verify cache updated
    crud = SettingsCRUD()
    assert crud.get_setting('Host') == '10.0.0.1'

def test_maintenance_mode(client):
    # Enable maintenance mode
    # ... mock global maintenance_mode = True

    response = client.get('/backend/tools')
    assert response.status_code == 503

    # Test maintenance endpoints still work
    response = client.post('/backend/settings/reload')
    assert response.status_code == 200
```

### Load Testing

- **Concurrency Test**: Multiple admin users updating settings simultaneously
- **Performance Test**: Settings cache performance under high load
- **Reliability Test**: Backup/restore operations with large databases
- **Stress Test**: Network timeouts and connection failures during reloads
