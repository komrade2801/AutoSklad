"""
IdempotencyToken Model - Prevents duplicate command execution during retries

This model stores idempotency tokens to ensure commands are executed
exactly once, even if they are retried multiple times due to network
failures or batch rollbacks.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.sql import func
from .base import sync_base


class IdempotencyToken(sync_base):
    """
    Stores idempotency tokens to prevent duplicate command execution.
    
    Used by IdempotencyManager to:
    1. Detect duplicate command submissions during retry
    2. Store execution results for replay
    3. Ensure exactly-once semantics
    
    Token Generation:
    - SHA256(command_id + timestamp)
    - Stable across retries (same command = same token)
    
    Architecture:
    - Created BEFORE command execution
    - Checked on every batch execution
    - Prevents re-execution after rollback + retry
    """
    
    __tablename__ = 'IdempotencyToken'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Unique token (SHA256 hash)
    token = Column(
        String(200),
        unique=True,
        nullable=False,
        comment='SHA256 hash of command_id + timestamp'
    )
    
    # Link to command
    command_id = Column(
        Integer,
        ForeignKey('Command.id', ondelete='CASCADE'),
        nullable=False,
        comment='Foreign key to Command table'
    )
    
    # Link to batch (optional)
    batch_id = Column(
        String(100),
        nullable=True,
        comment='UUID of batch execution (if part of batch)'
    )
    
    # Execution result (JSON serialized)
    execution_result = Column(
        Text,
        nullable=True,
        comment='JSON serialized result of command execution'
    )
    
    # Timestamp
    executed_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        comment='When command was first executed'
    )
    
    def __repr__(self):
        return (
            f"<IdempotencyToken(id={self.id}, "
            f"token={self.token[:16]}..., "
            f"command_id={self.command_id})>"
        )
    
    def to_dict(self):
        """Convert token to dictionary"""
        return {
            'id': self.id,
            'token': self.token,
            'command_id': self.command_id,
            'batch_id': self.batch_id,
            'execution_result': self.execution_result,
            'executed_at': self.executed_at.isoformat() if self.executed_at else None
        }
