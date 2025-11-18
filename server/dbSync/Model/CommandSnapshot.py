"""
CommandSnapshot Model - Stores pre-execution snapshots for rollback/compensation

This model captures the database state BEFORE each sync command executes,
enabling precise rollback via compensation when batch operations fail.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.sql import func
from .base import sync_base


class CommandSnapshot(sync_base):
    """
    Stores pre-execution state snapshots for sync command rollback.
    
    Used by SnapshotManager to:
    1. Capture current record state before UPDATE/DELETE operations
    2. Store NULL for INSERT operations (nothing existed before)
    3. Generate compensation operations from snapshots on batch failure
    
    Architecture:
    - Created BEFORE command execution in BatchProcessor
    - Stored in sync.db (survives work.db transaction rollback)
    - Used for compensation when ALL_OR_NOTHING batch fails
    """
    
    __tablename__ = 'CommandSnapshot'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Link to the command being snapshotted
    command_id = Column(
        Integer, 
        ForeignKey('Command.id', ondelete='CASCADE'),
        nullable=False,
        unique=True,  # One snapshot per command
        comment='Foreign key to Command table'
    )
    
    # Target table and record information
    table_name = Column(
        String(100), 
        nullable=False,
        comment='Name of table being modified'
    )
    
    record_id = Column(
        Integer,
        nullable=True,  # NULL for INSERT operations
        comment='ID of record being modified (NULL for inserts)'
    )
    
    # Snapshot data (JSON serialized)
    snapshot_data = Column(
        Text,
        nullable=True,  # NULL for INSERT operations
        comment='JSON snapshot of record state BEFORE operation'
    )
    
    # Operation type for compensation logic
    operation = Column(
        String(20),
        nullable=False,
        comment='Operation type: insert, update, delete'
    )
    
    # Timestamp
    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        comment='When snapshot was created'
    )
    
    def __repr__(self):
        return (
            f"<CommandSnapshot(id={self.id}, "
            f"command_id={self.command_id}, "
            f"table={self.table_name}, "
            f"operation={self.operation})>"
        )
    
    def to_dict(self):
        """Convert snapshot to dictionary for serialization"""
        return {
            'id': self.id,
            'command_id': self.command_id,
            'table_name': self.table_name,
            'record_id': self.record_id,
            'snapshot_data': self.snapshot_data,
            'operation': self.operation,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
