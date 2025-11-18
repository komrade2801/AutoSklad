"""
BatchExecution CRUD Engine - Database operations for batch tracking

Handles creation, updates, and queries for batch execution tracking
and command linking within batches.
"""

from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from ..Model.BatchExecution import BatchExecution, BatchCommandLink
from dbSync.Engines.CRUD import BaseCRUD


class BatchExecutionCRUD(BaseCRUD):
    """
    CRUD operations for BatchExecution model.
    
    Primary Operations:
    - create_batch: Initialize new batch execution
    - update_status: Update batch status (committed, rolled_back)
    - get_by_batch_id: Retrieve batch by UUID
    - add_command_link: Link command to batch
    - get_batch_commands: Get all commands in batch
    
    Architecture Integration:
    - Called by BatchProcessor.execute_batch()
    - Used for rollback coordination
    - Provides audit trail
    """
    
    def __init__(self, session: Session):
        """
        Initialize BatchExecution CRUD engine.
        
        :param session: SQLAlchemy session for sync.db
        """
        super().__init__(model=BatchExecution, session=session)
    
    def create_batch(
        self,
        batch_id: str,
        device_number: int,
        total_commands: int,
        status: str = 'in_progress'
    ) -> int:
        """
        Create new batch execution record.
        
        :param batch_id: UUID for batch
        :param device_number: Device initiating batch
        :param total_commands: Total commands in batch
        :param status: Initial status (default: in_progress)
        :return: Created batch record ID
        """
        batch = BatchExecution(
            batch_id=batch_id,
            device_number=device_number,
            total_commands=total_commands,
            status=status
        )
        
        self.session.add(batch)
        self.session.flush()
        
        return batch.id
    
    def get_by_batch_id(self, batch_id: str) -> Optional[BatchExecution]:
        """
        Retrieve batch by UUID.
        
        :param batch_id: Batch UUID
        :return: BatchExecution instance or None
        """
        return self.session.query(BatchExecution).filter_by(
            batch_id=batch_id
        ).first()
    
    def update_status(
        self,
        batch_id: str,
        status: str,
        error_message: Optional[str] = None
    ) -> bool:
        """
        Update batch status and completion time.
        
        :param batch_id: Batch UUID
        :param status: New status (committed, rolled_back)
        :param error_message: Optional error message
        :return: True if updated, False if batch not found
        """
        batch = self.get_by_batch_id(batch_id)
        
        if batch:
            batch.status = status
            batch.completed_at = datetime.utcnow()
            
            if error_message:
                batch.error_message = error_message
            
            self.session.flush()
            return True
        
        return False
    
    def update_batch_status(
        self,
        batch_id: str,
        status: str,
        successful_commands: int = 0,
        failed_commands: int = 0,
        error_message: Optional[str] = None
    ) -> bool:
        """
        Update batch status with command counts (alias for update_status with extended parameters).
        
        :param batch_id: Batch UUID
        :param status: New status (committed, rolled_back, completed, failed)
        :param successful_commands: Count of successful commands
        :param failed_commands: Count of failed commands
        :param error_message: Optional error message
        :return: True if updated, False if batch not found
        """
        batch = self.get_by_batch_id(batch_id)
        
        if batch:
            batch.status = status
            batch.successful_commands = successful_commands
            batch.failed_commands = failed_commands
            batch.completed_at = datetime.utcnow()
            
            if error_message:
                batch.error_message = error_message
            
            self.session.flush()
            return True
        
        return False
    
    def get_by_device(
        self, 
        device_number: int, 
        limit: int = 50
    ) -> List[BatchExecution]:
        """
        Retrieve recent batches for device.
        
        :param device_number: Device number
        :param limit: Maximum number of batches
        :return: List of BatchExecution instances
        """
        return self.session.query(BatchExecution).filter_by(
            device_number=device_number
        ).order_by(BatchExecution.started_at.desc()).limit(limit).all()
    
    def get_by_status(
        self, 
        status: str, 
        limit: int = 100
    ) -> List[BatchExecution]:
        """
        Retrieve batches by status.
        
        :param status: Status filter (in_progress, committed, rolled_back)
        :param limit: Maximum number of batches
        :return: List of BatchExecution instances
        """
        return self.session.query(BatchExecution).filter_by(
            status=status
        ).order_by(BatchExecution.started_at.desc()).limit(limit).all()
    
    def add_command_link(
        self,
        batch_id: str,
        command_id: int,
        execution_order: int,
        status: str = 'pending'
    ) -> int:
        """
        Link command to batch execution.
        
        :param batch_id: Batch UUID
        :param command_id: Command ID
        :param execution_order: Order within batch (0-based)
        :param status: Initial status (default: pending)
        :return: Created link ID
        """
        link = BatchCommandLink(
            batch_id=batch_id,
            command_id=command_id,
            execution_order=execution_order,
            status=status
        )
        
        self.session.add(link)
        self.session.flush()
        
        return link.id
    
    def update_command_status(
        self,
        batch_id: str,
        command_id: int,
        status: str
    ) -> bool:
        """
        Update status of command within batch.
        
        :param batch_id: Batch UUID
        :param command_id: Command ID
        :param status: New status (executed, rolled_back)
        :return: True if updated, False if not found
        """
        link = self.session.query(BatchCommandLink).filter_by(
            batch_id=batch_id,
            command_id=command_id
        ).first()
        
        if link:
            link.status = status
            link.executed_at = datetime.utcnow()
            self.session.flush()
            return True
        
        return False
    
    def get_batch_commands(self, batch_id: str) -> List[BatchCommandLink]:
        """
        Retrieve all command links for batch.
        
        :param batch_id: Batch UUID
        :return: List of BatchCommandLink instances in execution order
        """
        return self.session.query(BatchCommandLink).filter_by(
            batch_id=batch_id
        ).order_by(BatchCommandLink.execution_order).all()
    
    def get_executed_command_ids(self, batch_id: str) -> List[int]:
        """
        Get list of command IDs that were executed in batch.
        
        Used for compensation on rollback.
        
        :param batch_id: Batch UUID
        :return: List of command IDs with status 'executed'
        """
        links = self.session.query(BatchCommandLink).filter_by(
            batch_id=batch_id,
            status='executed'
        ).order_by(BatchCommandLink.execution_order).all()
        
        return [link.command_id for link in links]
    
    def count_by_status_and_device(
        self, 
        device_number: int, 
        status: str
    ) -> int:
        """
        Count batches by device and status.
        
        :param device_number: Device number
        :param status: Status filter
        :return: Count of batches
        """
        return self.session.query(BatchExecution).filter_by(
            device_number=device_number,
            status=status
        ).count()
