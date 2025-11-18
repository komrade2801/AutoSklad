"""
IdempotencyToken CRUD Engine - Database operations for idempotency management

Handles creation, retrieval, and updates for idempotency tokens
used to prevent duplicate command execution.
"""

from typing import Optional, List, Union
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..Model.IdempotencyToken import IdempotencyToken
from dbSync.Engines.CRUD import BaseCRUD


class IdempotencyTokenCRUD(BaseCRUD):
    """
    CRUD operations for IdempotencyToken model.
    
    Primary Operations:
    - add_token: Create token before command execution
    - get_by_token: Check if token already exists
    - update_result: Store execution result
    - cleanup_old_tokens: Remove old tokens (optional)
    
    Architecture Integration:
    - Called by IdempotencyManager.check_and_store()
    - Used to prevent duplicate execution on retry
    - Enables exactly-once semantics
    """
    
    def __init__(self, session: Session):
        """
        Initialize IdempotencyToken CRUD engine.
        
        :param session: SQLAlchemy session for sync.db
        """
        super().__init__(model=IdempotencyToken, session=session)
    
    def add_token(
        self,
        token: str,
        command_id: int,
        batch_id: Optional[str] = None,
        execution_result: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        status: str = 'COMPLETED'
    ) -> int:
        """
        Create idempotency token record.
        
        :param token: SHA256 hash token
        :param command_id: Command ID
        :param batch_id: Optional batch UUID
        :param execution_result: Optional JSON string of execution result
        :param expires_at: Optional expiration datetime (defaults to now + 24h)
        :param status: Lifecycle status (PENDING|COMPLETED|FAILED)
        :return: Created token record ID
        """
        if expires_at is None:
            expires_at = datetime.utcnow() + timedelta(hours=24)
        token_record = IdempotencyToken(
            token=token,
            command_id=command_id,
            batch_id=batch_id,
            execution_result=execution_result,
            status=status,
            expires_at=expires_at
        )
        
        self.session.add(token_record)
        self.session.flush()
        
        return token_record.id
    
    def get_by_token(self, token: str) -> Optional[IdempotencyToken]:
        """
        Retrieve token record by hash.
        
        :param token: SHA256 hash token
        :return: IdempotencyToken instance or None
        """
        return self.session.query(IdempotencyToken).filter_by(
            token=token
        ).first()
    
    def get_by_command(self, command_id: int) -> Optional[IdempotencyToken]:
        """
        Retrieve token record by command ID.
        
        :param command_id: Command ID
        :return: IdempotencyToken instance or None
        """
        return self.session.query(IdempotencyToken).filter_by(
            command_id=command_id
        ).first()
    
    def update_result(
        self,
        token: str,
        result: str
    ) -> bool:
        """
        Update execution result for token.
        
        :param token: SHA256 hash token
        :param result: JSON string of execution result
        :return: True if updated, False if token not found
        """
        token_record = self.get_by_token(token)
        
        if token_record:
            token_record.execution_result = result
            self.session.flush()
            return True
        
        return False
    
    def get_by_batch(self, batch_id: str) -> List[IdempotencyToken]:
        """
        Retrieve all tokens for batch.
        
        :param batch_id: Batch UUID
        :return: List of IdempotencyToken instances
        """
        return self.session.query(IdempotencyToken).filter_by(
            batch_id=batch_id
        ).all()
    
    def delete_by_token(self, token: str) -> bool:
        """
        Delete token record.
        
        :param token: SHA256 hash token
        :return: True if deleted, False if not found
        """
        token_record = self.get_by_token(token)
        
        if token_record:
            self.session.delete(token_record)
            self.session.flush()
            return True
        
        return False

    # Backwards-compatible alias used by IdempotencyManager
    def delete_token(self, token: str) -> bool:
        return self.delete_by_token(token)
    
    def cleanup_old_tokens(self, cutoff_or_days: Union[datetime, int] = 30) -> int:
        """
        Delete tokens older than cutoff date (by expires_at).
        Accepts either datetime cutoff or days (int).
        """
        if isinstance(cutoff_or_days, int):
            cutoff_date = datetime.utcnow() - timedelta(days=cutoff_or_days)
        else:
            cutoff_date = cutoff_or_days
        count = self.session.query(IdempotencyToken).filter(
            (IdempotencyToken.expires_at != None) & (IdempotencyToken.expires_at < cutoff_date)
        ).delete(synchronize_session=False)
        self.session.flush()
        return count
    
    def count_tokens(self) -> int:
        """
        Count total idempotency tokens.
        
        For monitoring purposes.
        
        :return: Total count of tokens
        """
        return self.session.query(IdempotencyToken).count()
    
    def get_recent_tokens(self, limit: int = 100) -> List[IdempotencyToken]:
        """
        Retrieve recent tokens.
        
        For diagnostic purposes.
        
        :param limit: Maximum number of tokens
        :return: List of IdempotencyToken instances
        """
        return self.session.query(IdempotencyToken).order_by(
            IdempotencyToken.executed_at.desc()
        ).limit(limit).all()
