"""
IdempotencyToken CRUD Engine - Database operations for idempotency management

Handles creation, retrieval, and updates for idempotency tokens
used to prevent duplicate command execution.
"""

from typing import Optional, List
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
        super().__init__(session, IdempotencyToken)
    
    def add_token(
        self,
        token: str,
        command_id: int,
        batch_id: Optional[str] = None
    ) -> int:
        """
        Create idempotency token record.
        
        :param token: SHA256 hash token
        :param command_id: Command ID
        :param batch_id: Optional batch UUID
        :return: Created token record ID
        """
        token_record = IdempotencyToken(
            token=token,
            command_id=command_id,
            batch_id=batch_id
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
    
    def cleanup_old_tokens(self, days_old: int = 30) -> int:
        """
        Delete tokens older than specified days.
        
        Optional maintenance operation to prevent table growth.
        
        :param days_old: Age threshold in days
        :return: Number of tokens deleted
        """
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        count = self.session.query(IdempotencyToken).filter(
            IdempotencyToken.executed_at < cutoff_date
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
