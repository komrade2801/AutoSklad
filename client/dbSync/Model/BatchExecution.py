"""
BatchExecution Model - Tracks batch sync operations for coordinated rollback

This model tracks the lifecycle of batch command executions, enabling
recovery and rollback coordination in ALL_OR_NOTHING strategy.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from .base import sync_base


class BatchExecution(sync_base):
    """
    Tracks batch execution state for rollback coordination.
    
    Used by BatchProcessor to:
    1. Track overall batch status (in_progress, committed, rolled_back)
    2. Coordinate rollback across multiple commands
    3. Enable retry of entire batch on failure
    4. Provide audit trail of batch operations
    
    Architecture:
    - Created at start of BatchProcessor.execute_batch()
    - Updated as batch progresses
    - Final status set on commit or rollback
    """
    
    __tablename__ = 'batch_execution'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Unique batch identifier (UUID)
    batch_id = Column(
        String(100),
        unique=True,
        nullable=False,
        comment='UUID for this batch execution'
    )
    
    # Device information
    device_number = Column(
        Integer,
        nullable=False,
        comment='Device that initiated this batch'
    )
    
    # Batch size
    total_commands = Column(
        Integer,
        nullable=False,
        comment='Total number of commands in batch'
    )
    
    # Execution status
    status = Column(
        String(20),
        nullable=False,
        default='in_progress',
        comment='Batch status: in_progress, committed, rolled_back'
    )
    
    # Timestamps
    started_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        comment='When batch execution started'
    )
    
    completed_at = Column(
        DateTime,
        nullable=True,
        comment='When batch completed (committed or rolled back)'
    )
    
    # Error information
    error_message = Column(
        Text,
        nullable=True,
        comment='Error message if batch failed'
    )
    
    def __repr__(self):
        return (
            f"<BatchExecution(id={self.id}, "
            f"batch_id={self.batch_id}, "
            f"status={self.status}, "
            f"total={self.total_commands})>"
        )
    
    def to_dict(self):
        """Convert batch execution to dictionary"""
        return {
            'id': self.id,
            'batch_id': self.batch_id,
            'device_number': self.device_number,
            'total_commands': self.total_commands,
            'status': self.status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message
        }


class BatchCommandLink(sync_base):
    """
    Links commands to batch executions for coordinated rollback.
    
    Tracks execution order and status of each command within a batch,
    enabling precise rollback and resume operations.
    """
    
    __tablename__ = 'batch_command_link'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Link to batch
    batch_id = Column(
        String(100),
        nullable=False,
        comment='UUID of batch execution'
    )
    
    # Link to command
    command_id = Column(
        Integer,
        nullable=False,
        comment='ID of command in this batch'
    )
    
    # Execution metadata
    execution_order = Column(
        Integer,
        nullable=False,
        comment='Order of command within batch (0-based)'
    )
    
    status = Column(
        String(20),
        nullable=False,
        default='pending',
        comment='Command status: pending, executed, rolled_back'
    )
    
    executed_at = Column(
        DateTime,
        nullable=True,
        comment='When command was executed'
    )
    
    def __repr__(self):
        return (
            f"<BatchCommandLink(batch_id={self.batch_id}, "
            f"command_id={self.command_id}, "
            f"order={self.execution_order}, "
            f"status={self.status})>"
        )
    
    def to_dict(self):
        """Convert link to dictionary"""
        return {
            'id': self.id,
            'batch_id': self.batch_id,
            'command_id': self.command_id,
            'execution_order': self.execution_order,
            'status': self.status,
            'executed_at': self.executed_at.isoformat() if self.executed_at else None
        }
