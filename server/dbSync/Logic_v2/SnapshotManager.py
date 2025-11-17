"""
SnapshotManager - Captures and manages database state snapshots for rollback compensation

This manager captures the state of database records BEFORE sync operations execute,
enabling precise rollback through compensation when batch operations fail.

Architecture:
- Captures snapshots synchronously before each UPDATE/DELETE operation
- Stores snapshots in sync.db (survives work.db transaction rollback)
- Generates compensation operations from snapshots on batch failure
- Provides automatic cleanup of old snapshots

Integration:
- Called by BatchProcessor before each command execution
- Used by SyncProcessor to rollback failed batches
- Works with CommandSnapshotCRUD for persistence
"""

import json
import threading
import traceback
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from dbSync.Engines.CommandSnapshotEngine import CommandSnapshotCRUD
from dbSync.Logic_v2.DiagnosticLogger import DiagnosticLogger


class SnapshotManager:
    """
    Manages pre-execution snapshots for compensation-based rollback.
    
    Responsibilities:
    - Capture current record state before UPDATE/DELETE operations
    - Generate inverse operations from snapshots
    - Apply compensation in reverse order on batch failure
    - Cleanup old snapshots to prevent database bloat
    """
    
    def __init__(
        self,
        snapshot_crud: CommandSnapshotCRUD,
        work_session: Session,
        sync_manager=None,
        _logger: Optional[DiagnosticLogger] = None
    ):
        """
        Initialize SnapshotManager.
        
        :param snapshot_crud: CommandSnapshotCRUD for snapshot persistence
        :param work_session: SQLAlchemy Session for querying work.db
        :param sync_manager: SyncManager for querying current record state
        :param _logger: Optional DiagnosticLogger for centralized logging
        """
        self.snapshot_crud = snapshot_crud
        self.work_session = work_session
        self.sync_manager = sync_manager
        self.logger = _logger
    
    def capture_snapshot(
        self,
        command_id: int,
        table: str,
        record_id: Optional[int],
        operation: str
    ) -> bool:
        """
        Synchronously capture current record state BEFORE execution.
        
        Flow:
        1. For INSERT: Store NULL snapshot (nothing existed before)
        2. For UPDATE/DELETE: Query current record from work.db
        3. Serialize record to JSON
        4. Store in CommandSnapshot table via snapshot_crud
        5. Log success/failure
        
        :param command_id: ID of command being executed
        :param table: Name of table being modified
        :param record_id: ID of record being modified (None for INSERT)
        :param operation: Operation type (insert/update/delete)
        :return: True if snapshot captured successfully
        """
        try:
            snapshot_data = None
            
            # For UPDATE/DELETE, capture current state
            if operation.lower() in ['update', 'delete'] and record_id is not None:
                snapshot_data = self._query_current_state(table, record_id)
                
                if snapshot_data is None:
                    print(
                        f'[ПОТОК][{threading.current_thread().name}]'
                        f'[SnapshotManager][capture_snapshot][WARNING] - '
                        f'Record not found for snapshot: table={table}, '
                        f'record_id={record_id}. [{datetime.now()}]'
                    )
                    # Not necessarily an error - record might not exist yet
                    # Continue with NULL snapshot
            
            # Store snapshot (NULL for INSERT, data for UPDATE/DELETE)
            self.snapshot_crud.add_snapshot(
                command_id=command_id,
                table_name=table,
                record_id=record_id,
                snapshot_data=json.dumps(snapshot_data) if snapshot_data else None,
                operation=operation.lower()
            )
            
            print(
                f'[ПОТОК][{threading.current_thread().name}]'
                f'[SnapshotManager][capture_snapshot][INFO] - '
                f'command_id: {command_id}, table: {table}, '
                f'operation: {operation}. [{datetime.now()}]'
            )
            
            if self.logger:
                self.logger.log_info(
                    f"Snapshot captured for command {command_id}",
                    {
                        "table": table,
                        "record_id": record_id,
                        "operation": operation,
                        "has_data": snapshot_data is not None
                    }
                )
            
            return True
            
        except Exception as e:
            print(
                f'[ПОТОК][{threading.current_thread().name}]'
                f'[SnapshotManager][capture_snapshot][ERROR] - '
                f'error: {e}, подробности: - {traceback.format_exc()}. '
                f'[{datetime.now()}]'
            )
            
            if self.logger:
                self.logger.log_error(
                    f"Failed to capture snapshot for command {command_id}",
                    {
                        "table": table,
                        "record_id": record_id,
                        "operation": operation,
                        "exception": str(e)
                    }
                )
            
            return False
    
    def _query_current_state(self, table: str, record_id: int) -> Optional[Dict[str, Any]]:
        """
        Query current record state from work.db.
        
        Uses SyncManager to access the appropriate CRUD engine.
        
        :param table: Table name
        :param record_id: Record ID
        :return: Record data as dictionary, or None if not found
        """
        try:
            if not self.sync_manager:
                print(
                    f'[ПОТОК][{threading.current_thread().name}]'
                    f'[SnapshotManager][_query_current_state][WARNING] - '
                    f'SyncManager not available, cannot query record state. '
                    f'[{datetime.now()}]'
                )
                return None
            
            # Get CRUD engine for table
            crud = self.sync_manager.get_crud(table)
            if not crud:
                return None
            
            # Query record by ID
            record = crud.get(record_id)
            if not record:
                return None
            
            # Convert to dictionary
            if hasattr(record, '__dict__'):
                data = {
                    key: value for key, value in record.__dict__.items()
                    if not key.startswith('_')
                }
                return data
            
            return None
            
        except Exception as e:
            print(
                f'[ПОТОК][{threading.current_thread().name}]'
                f'[SnapshotManager][_query_current_state][ERROR] - '
                f'error: {e}, table: {table}, record_id: {record_id}. '
                f'[{datetime.now()}]'
            )
            return None
    
    def generate_compensation_operations(self, batch_id: str) -> List[Dict[str, Any]]:
        """
        Generate inverse operations from snapshots for a failed batch.
        
        Compensation logic:
        - INSERT → DELETE the inserted record
        - UPDATE → UPDATE back to snapshot values
        - DELETE → INSERT the deleted record (restore from snapshot)
        
        Operations are returned in REVERSE order (LIFO) to undo in
        the opposite sequence of execution.
        
        :param batch_id: Batch ID to generate compensation for
        :return: List of compensation operations in reverse order
        """
        try:
            # Get all command IDs for this batch
            # This would come from BatchCommandLink table
            # For now, we'll need the command_ids passed separately
            # or retrieved via batch_crud
            
            compensation_ops = []
            
            print(
                f'[ПОТОК][{threading.current_thread().name}]'
                f'[SnapshotManager][generate_compensation_operations][INFO] - '
                f'Generating compensation for batch_id: {batch_id}. '
                f'[{datetime.now()}]'
            )
            
            # NOTE: This is a placeholder - actual implementation needs
            # BatchCommandLink to get command IDs for the batch
            # For now, return empty list
            
            if self.logger:
                self.logger.log_info(
                    f"Generated {len(compensation_ops)} compensation operations",
                    {"batch_id": batch_id}
                )
            
            return compensation_ops
            
        except Exception as e:
            print(
                f'[ПОТОК][{threading.current_thread().name}]'
                f'[SnapshotManager][generate_compensation_operations][ERROR] - '
                f'error: {e}, подробности: - {traceback.format_exc()}. '
                f'[{datetime.now()}]'
            )
            
            if self.logger:
                self.logger.log_error(
                    f"Failed to generate compensation operations",
                    {"batch_id": batch_id, "exception": str(e)}
                )
            
            return []
    
    def generate_compensation_for_command(
        self,
        command_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Generate compensation operation for a single command.
        
        :param command_id: Command ID to compensate
        :return: Compensation operation dict or None
        """
        try:
            snapshot = self.snapshot_crud.get_by_command(command_id)
            if not snapshot:
                return None
            
            operation = snapshot.operation.lower()
            table = snapshot.table_name
            record_id = snapshot.record_id
            
            # Parse snapshot data
            snapshot_data = None
            if snapshot.snapshot_data:
                snapshot_data = json.loads(snapshot.snapshot_data)
            
            # Generate inverse operation
            if operation == 'insert':
                # INSERT → DELETE
                return {
                    'table': table,
                    'operation': 'delete',
                    'id': record_id,
                    'data': {}
                }
            
            elif operation == 'update':
                # UPDATE → UPDATE back to original
                if snapshot_data:
                    return {
                        'table': table,
                        'operation': 'update',
                        'id': record_id,
                        'data': snapshot_data
                    }
            
            elif operation == 'delete':
                # DELETE → INSERT (restore)
                if snapshot_data:
                    return {
                        'table': table,
                        'operation': 'insert',
                        'data': snapshot_data
                    }
            
            return None
            
        except Exception as e:
            print(
                f'[ПОТОК][{threading.current_thread().name}]'
                f'[SnapshotManager][generate_compensation_for_command][ERROR] - '
                f'error: {e}, command_id: {command_id}. [{datetime.now()}]'
            )
            return None
    
    def cleanup_old_snapshots(self, older_than_days: int = 30) -> int:
        """
        Automatic cleanup of old snapshots to prevent database bloat.
        
        Called periodically by APScheduler (typically daily at 3 AM).
        Deletes snapshots older than the specified retention period.
        
        :param older_than_days: Delete snapshots older than this many days
        :return: Number of snapshots deleted
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=older_than_days)
            
            print(
                f'[ПОТОК][{threading.current_thread().name}]'
                f'[SnapshotManager][cleanup_old_snapshots][INFO] - '
                f'Starting cleanup: older_than_days={older_than_days}, '
                f'cutoff_date={cutoff_date}. [{datetime.now()}]'
            )
            
            # Get count before deletion
            deleted_count = self.snapshot_crud.bulk_delete_older_than(cutoff_date)
            
            print(
                f'[ПОТОК][{threading.current_thread().name}]'
                f'[SnapshotManager][cleanup_old_snapshots][INFO] - '
                f'Cleanup complete: deleted {deleted_count} snapshots. '
                f'[{datetime.now()}]'
            )
            
            if self.logger:
                self.logger.log_info(
                    f"Snapshot cleanup completed",
                    {
                        "older_than_days": older_than_days,
                        "deleted_count": deleted_count,
                        "cutoff_date": cutoff_date.isoformat()
                    }
                )
            
            return deleted_count
            
        except Exception as e:
            print(
                f'[ПОТОК][{threading.current_thread().name}]'
                f'[SnapshotManager][cleanup_old_snapshots][ERROR] - '
                f'error: {e}, подробности: - {traceback.format_exc()}. '
                f'[{datetime.now()}]'
            )
            
            if self.logger:
                self.logger.log_error(
                    f"Snapshot cleanup failed",
                    {
                        "older_than_days": older_than_days,
                        "exception": str(e)
                    }
                )
            
            return 0
    
    def get_snapshot(self, command_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve snapshot for a specific command.
        
        :param command_id: Command ID
        :return: Snapshot data dictionary or None
        """
        try:
            snapshot = self.snapshot_crud.get_by_command(command_id)
            if not snapshot:
                return None
            
            return {
                'command_id': command_id,
                'table': snapshot.table_name,
                'record_id': snapshot.record_id,
                'operation': snapshot.operation,
                'snapshot_data': json.loads(snapshot.snapshot_data) if snapshot.snapshot_data else None,
                'created_at': snapshot.created_at.isoformat() if snapshot.created_at else None
            }
            
        except Exception as e:
            print(
                f'[ПОТОК][{threading.current_thread().name}]'
                f'[SnapshotManager][get_snapshot][ERROR] - '
                f'error: {e}, command_id: {command_id}. [{datetime.now()}]'
            )
            return None
