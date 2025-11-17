"""
BatchProcessor Enhanced - Atomic batch processing with ALL_OR_NOTHING rollback

This enhanced version adds comprehensive rollback support using:
- IdempotencyManager: Prevents duplicate execution during retries
- SnapshotManager: Captures pre-execution state for compensation
- BatchExecutionCRUD: Tracks batch lifecycle and status
- Two-phase rollback: DB transaction rollback + compensation operations

Architecture:
- Phase 1: Check idempotency (skip duplicates)
- Phase 2: Capture snapshots (before execution)
- Phase 3: Execute operations (in transaction)
- Phase 4: Record results (for idempotency)
- Phase 5: On failure - Apply compensation (undo changes)

Integration:
- Called by SyncProcessor.process_push()
- Uses SnapshotManager and IdempotencyManager from Phase 2
- Tracks batches in BatchExecution table
"""

import threading
import traceback
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, TypedDict
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from dbSync.Logic_v2.SyncManager import SyncManager
from dbSync.Logic_v2.DiagnosticLogger import DiagnosticLogger
from dbSync.Logic_v2.SnapshotManager import SnapshotManager
from dbSync.Logic_v2.IdempotencyManager import IdempotencyManager
from dbSync.Engines.BatchExecutionEngine import BatchExecutionCRUD

import logging
logger = logging.getLogger(__name__)


class Operation(TypedDict, total=False):
    """Operation definition for sync commands."""
    command_id: int
    table: str
    operation: str  # "insert" | "update" | "delete"
    data: Dict[str, Any]
    id: Optional[int]
    timestamp: Optional[str]  # For idempotency token generation


class OperationResult(TypedDict, total=False):
    """Result of a single operation execution."""
    command_id: int
    success: bool
    new_id: Optional[int]
    error: Optional[str]
    was_duplicate: Optional[bool]  # True if skipped due to idempotency


class BatchProcessorEnhanced:
    """
    Enhanced atomic batch processor with ALL_OR_NOTHING rollback strategy.
    
    New Features (Phase 3):
    - Idempotency checking to prevent duplicate execution
    - Pre-execution snapshot capture for compensation
    - Batch tracking via BatchExecution table
    - Two-phase rollback: transaction rollback + compensation
    - Comprehensive logging and error handling
    
    Rollback Strategy:
    1. Database Transaction Rollback: Automatically handled by SQLAlchemy
    2. Compensation Operations: Applied for any successfully executed commands
       before the failure point (uses SnapshotManager)
    """
    
    def __init__(
        self,
        session: Session,
        sync_manager: SyncManager,
        snapshot_manager: Optional[SnapshotManager] = None,
        idempotency_manager: Optional[IdempotencyManager] = None,
        batch_crud: Optional[BatchExecutionCRUD] = None,
        device_number: Optional[int] = None,
        _logger: Optional[DiagnosticLogger] = None
    ):
        """
        Initialize enhanced batch processor.
        
        :param session: SQLAlchemy Session for work.db transactions
        :param sync_manager: Routes operations to appropriate CRUD classes
        :param snapshot_manager: Captures pre-execution state (optional)
        :param idempotency_manager: Prevents duplicate execution (optional)
        :param batch_crud: Tracks batch execution (optional)
        :param device_number: Device ID for batch tracking
        :param _logger: Diagnostic logger for centralized logging
        """
        self.session = session
        self.sync_manager = sync_manager
        self.snapshot_manager = snapshot_manager
        self.idempotency_manager = idempotency_manager
        self.batch_crud = batch_crud
        self.device_number = device_number
        self.logger = _logger
    
    def execute_batch(
        self,
        operations: List[Operation],
        enable_rollback: bool = True
    ) -> List[OperationResult]:
        """
        Execute batch with ALL_OR_NOTHING rollback strategy.
        
        Flow:
        1. Generate unique batch ID
        2. Create BatchExecution record (status: in_progress)
        3. For each operation:
           a. Check idempotency (skip if duplicate)
           b. Capture snapshot (for UPDATE/DELETE)
           c. Execute operation
           d. Record result for idempotency
           e. Link command to batch
        4. On success: Update batch status to 'committed'
        5. On failure:
           a. DB transaction rolls back automatically
           b. Apply compensation operations (if enabled)
           c. Update batch status to 'rolled_back'
        
        :param operations: List of operations to execute
        :param enable_rollback: Enable compensation rollback (default: True)
        :return: List of operation results
        """
        batch_id = str(uuid.uuid4())
        results: List[OperationResult] = []
        executed_command_ids: List[int] = []
        
        print(
            f'[ПОТОК][{threading.current_thread().name}]'
            f'[BatchProcessorEnhanced][execute_batch][INFO] - '
            f'Starting batch: batch_id={batch_id}, '
            f'operations={len(operations)}. [{datetime.now()}]'
        )
        
        # Create batch execution record
        if self.batch_crud and self.device_number:
            try:
                self.batch_crud.create_batch(
                    batch_id=batch_id,
                    device_number=self.device_number,
                    total_commands=len(operations),
                    status='in_progress'
                )
            except Exception as e:
                print(
                    f'[ПОТОК][{threading.current_thread().name}]'
                    f'[BatchProcessorEnhanced][execute_batch][WARNING] - '
                    f'Failed to create batch record: {e}. [{datetime.now()}]'
                )
        
        try:
            with self.session.begin_nested():
                for idx, op in enumerate(operations):
                    try:
                        # Phase 1: Idempotency check
                        if self.idempotency_manager:
                            token = self.idempotency_manager.generate_token(
                                command_id=op["command_id"],
                                timestamp=op.get("timestamp")
                            )
                            
                            if self.idempotency_manager.is_duplicate(token):
                                # Skip duplicate - return cached result
                                cached_result = self.idempotency_manager.get_cached_result(token)
                                if cached_result:
                                    results.append({
                                        "command_id": op["command_id"],
                                        "success": True,
                                        "new_id": cached_result.get("new_id"),
                                        "was_duplicate": True
                                    })
                                    print(
                                        f'[ПОТОК][{threading.current_thread().name}]'
                                        f'[BatchProcessorEnhanced][execute_batch][INFO] - '
                                        f'Skipped duplicate: command_id={op["command_id"]}. '
                                        f'[{datetime.now()}]'
                                    )
                                    continue
                        
                        # Phase 2: Snapshot capture (for UPDATE/DELETE)
                        if self.snapshot_manager:
                            operation_type = op["operation"].lower()
                            if operation_type in ['update', 'delete']:
                                self.snapshot_manager.capture_snapshot(
                                    command_id=op["command_id"],
                                    table=op["table"],
                                    record_id=op.get("id"),
                                    operation=operation_type
                                )
                        
                        # Phase 3: Execute operation
                        res = self._apply_single(op)
                        
                        # Extract new_id
                        new_id = None
                        if isinstance(res, dict):
                            new_id = res.get('id', None)
                        else:
                            new_id = getattr(res, 'id', None)
                        
                        # Phase 4: Record result for idempotency
                        if self.idempotency_manager:
                            result_data = {
                                "success": True,
                                "new_id": new_id
                            }
                            self.idempotency_manager.record_execution(
                                token=token,
                                command_id=op["command_id"],
                                batch_id=batch_id,
                                result=result_data
                            )
                        
                        # Track executed commands for potential rollback
                        executed_command_ids.append(op["command_id"])
                        
                        # Link command to batch
                        if self.batch_crud:
                            try:
                                self.batch_crud.add_command_link(
                                    batch_id=batch_id,
                                    command_id=op["command_id"],
                                    execution_order=idx,
                                    status='executed'
                                )
                            except Exception as e:
                                print(
                                    f'[ПОТОК][{threading.current_thread().name}]'
                                    f'[BatchProcessorEnhanced][execute_batch][WARNING] - '
                                    f'Failed to link command to batch: {e}. '
                                    f'[{datetime.now()}]'
                                )
                        
                        results.append({
                            "command_id": op["command_id"],
                            "success": True,
                            "new_id": new_id,
                            "was_duplicate": False
                        })
                        
                        print(
                            f'[ПОТОК][{threading.current_thread().name}]'
                            f'[BatchProcessorEnhanced][execute_batch][INFO] - '
                            f'command_id: {op["command_id"]} executed successfully. '
                            f'[{datetime.now()}]'
                        )
                        
                    except Exception as e:
                        print(
                            f'[ПОТОК][{threading.current_thread().name}]'
                            f'[BatchProcessorEnhanced][execute_batch][ERROR] - '
                            f'error: {e}, подробности: - {traceback.format_exc()}. '
                            f'[{datetime.now()}]'
                        )
                        
                        if self.logger:
                            self.logger.log_error(
                                f"BatchProcessor failed on command {op['command_id']}",
                                {"operation": op, "exception": str(e)}
                            )
                        
                        results.append({
                            "command_id": op["command_id"],
                            "success": False,
                            "error": str(e),
                            "was_duplicate": False
                        })
                        
                        # Raise to trigger transaction rollback
                        raise
            
            # Success - update batch status
            if self.batch_crud:
                try:
                    self.batch_crud.update_batch_status(
                        batch_id=batch_id,
                        status='committed'
                    )
                except Exception as e:
                    print(
                        f'[ПОТОК][{threading.current_thread().name}]'
                        f'[BatchProcessorEnhanced][execute_batch][WARNING] - '
                        f'Failed to update batch status: {e}. [{datetime.now()}]'
                    )
            
            print(
                f'[ПОТОК][{threading.current_thread().name}]'
                f'[BatchProcessorEnhanced][execute_batch][INFO] - '
                f'Batch committed successfully: batch_id={batch_id}. '
                f'[{datetime.now()}]'
            )
            
        except (SQLAlchemyError, Exception) as e:
            print(
                f'[ПОТОК][{threading.current_thread().name}]'
                f'[BatchProcessorEnhanced][execute_batch][ERROR] - '
                f'Batch failed, rolling back: batch_id={batch_id}, '
                f'error: {e}. [{datetime.now()}]'
            )
            
            # Phase 5: Apply compensation (if enabled)
            if enable_rollback and self.snapshot_manager and executed_command_ids:
                print(
                    f'[ПОТОК][{threading.current_thread().name}]'
                    f'[BatchProcessorEnhanced][execute_batch][INFO] - '
                    f'Applying compensation for {len(executed_command_ids)} commands. '
                    f'[{datetime.now()}]'
                )
                
                self._apply_compensation(executed_command_ids)
            
            # Update batch status to rolled_back
            if self.batch_crud:
                try:
                    self.batch_crud.update_batch_status(
                        batch_id=batch_id,
                        status='rolled_back',
                        error_message=str(e)
                    )
                except Exception as update_error:
                    print(
                        f'[ПОТОК][{threading.current_thread().name}]'
                        f'[BatchProcessorEnhanced][execute_batch][WARNING] - '
                        f'Failed to update batch status: {update_error}. '
                        f'[{datetime.now()}]'
                    )
        
        return results
    
    def _apply_single(self, op: Operation) -> Dict[str, Any]:
        """
        Execute a single operation via SyncManager.
        
        :param op: Operation to execute
        :return: Result dictionary
        """
        payload = {
            "table": op["table"],
            "operation": op["operation"].lower(),
            "data": op["data"]
        }
        if op.get("id") is not None:
            payload["id"] = op["id"]
        
        result = self.sync_manager.process_sync_command(payload, sync_context=True)
        
        print(
            f'[ПОТОК][{threading.current_thread().name}]'
            f'[BatchProcessorEnhanced][_apply_single][INFO] - '
            f'command_id: {op["command_id"]}. [{datetime.now()}]'
        )
        
        return result or {}
    
    def _apply_compensation(self, executed_command_ids: List[int]) -> None:
        """
        Apply compensation operations for executed commands.
        
        Compensation is applied in REVERSE order (LIFO) to undo
        changes in the opposite sequence of execution.
        
        :param executed_command_ids: List of command IDs that were executed
        """
        if not self.snapshot_manager:
            print(
                f'[ПОТОК][{threading.current_thread().name}]'
                f'[BatchProcessorEnhanced][_apply_compensation][WARNING] - '
                f'SnapshotManager not available, skipping compensation. '
                f'[{datetime.now()}]'
            )
            return
        
        # Reverse order for LIFO compensation
        for command_id in reversed(executed_command_ids):
            try:
                # Generate compensation operation
                compensation_op = self.snapshot_manager.generate_compensation_for_command(
                    command_id
                )
                
                if not compensation_op:
                    print(
                        f'[ПОТОК][{threading.current_thread().name}]'
                        f'[BatchProcessorEnhanced][_apply_compensation][WARNING] - '
                        f'No compensation generated for command_id={command_id}. '
                        f'[{datetime.now()}]'
                    )
                    continue
                
                # Apply compensation
                self.sync_manager.process_sync_command(
                    compensation_op,
                    sync_context=True
                )
                
                print(
                    f'[ПОТОК][{threading.current_thread().name}]'
                    f'[BatchProcessorEnhanced][_apply_compensation][INFO] - '
                    f'Compensation applied for command_id={command_id}. '
                    f'[{datetime.now()}]'
                )
                
                if self.logger:
                    self.logger.log_info(
                        f"Compensation applied for command {command_id}",
                        {"operation": compensation_op}
                    )
                
            except Exception as e:
                print(
                    f'[ПОТОК][{threading.current_thread().name}]'
                    f'[BatchProcessorEnhanced][_apply_compensation][ERROR] - '
                    f'Failed to apply compensation for command_id={command_id}: '
                    f'{e}. [{datetime.now()}]'
                )
                
                if self.logger:
                    self.logger.log_error(
                        f"Compensation failed for command {command_id}",
                        {"command_id": command_id, "exception": str(e)}
                    )
