"""
IdempotencyManager - Ensures exactly-once command execution during retries

This manager generates and validates idempotency tokens to prevent duplicate
command execution when batches are retried after failures or network issues.

Architecture:
- Generates stable SHA256 tokens from command metadata
- Checks for duplicate executions before processing
- Caches execution results for replay on retry
- Provides automatic cleanup of old tokens

Integration:
- Called by BatchProcessor at start of each command execution
- Prevents re-execution after batch rollback + retry
- Works with IdempotencyTokenCRUD for persistence
"""

import hashlib
import json
import threading
import traceback
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.exc import SQLAlchemyError

from dbSync.Engines.IdempotencyTokenEngine import IdempotencyTokenCRUD
from dbSync.Logic_v2.DiagnosticLogger import DiagnosticLogger


class IdempotencyManager:
    """
    Manages idempotency tokens for exactly-once command execution.
    
    Responsibilities:
    - Generate stable tokens for commands (SHA256 hash)
    - Check for duplicates before execution
    - Store execution results for replay
    - Enable safe retries after batch rollback
    - Cleanup old tokens to prevent database bloat
    """
    
    def __init__(
        self,
        token_crud: IdempotencyTokenCRUD,
        _logger: Optional[DiagnosticLogger] = None
    ):
        """
        Initialize IdempotencyManager.
        
        :param token_crud: IdempotencyTokenCRUD for token persistence
        :param _logger: Optional DiagnosticLogger for centralized logging
        """
        self.token_crud = token_crud
        self.logger = _logger
    
    def generate_token(
        self,
        command_id: int,
        timestamp: Optional[str] = None
    ) -> str:
        """
        Generate stable SHA256 token for a command.
        
        Token is deterministic - same command_id and timestamp
        always produce the same token. This enables retry detection.
        
        Formula: SHA256(f"{command_id}|{timestamp}")
        
        :param command_id: ID of command
        :param timestamp: Optional timestamp (uses current time if None)
        :return: Hex string token (64 characters)
        """
        try:
            # Use provided timestamp or current time
            if timestamp is None:
                timestamp = datetime.now().isoformat()
            
            # Generate stable token
            token_input = f"{command_id}|{timestamp}"
            token_bytes = token_input.encode('utf-8')
            token_hash = hashlib.sha256(token_bytes).hexdigest()
            
            print(
                f'[ПОТОК][{threading.current_thread().name}]'
                f'[IdempotencyManager][generate_token][INFO] - '
                f'command_id: {command_id}, token: {token_hash[:16]}... '
                f'[{datetime.now()}]'
            )
            
            return token_hash
            
        except Exception as e:
            print(
                f'[ПОТОК][{threading.current_thread().name}]'
                f'[IdempotencyManager][generate_token][ERROR] - '
                f'error: {e}, command_id: {command_id}. [{datetime.now()}]'
            )
            # Fallback to simple hash on error
            return hashlib.sha256(str(command_id).encode()).hexdigest()
    
    def is_duplicate(self, token: str) -> bool:
        """
        Synchronously check if token exists (command already executed).
        
        :param token: Idempotency token to check
        :return: True if command was already executed
        """
        try:
            existing_token = self.token_crud.get_by_token(token)
            
            is_dup = existing_token is not None
            
            if is_dup:
                print(
                    f'[ПОТОК][{threading.current_thread().name}]'
                    f'[IdempotencyManager][is_duplicate][INFO] - '
                    f'Duplicate detected: token={token[:16]}... '
                    f'[{datetime.now()}]'
                )
                
                if self.logger:
                    self.logger.log_info(
                        f"Duplicate command detected",
                        {"token": token[:16]}
                    )
            
            return is_dup
            
        except Exception as e:
            print(
                f'[ПОТОК][{threading.current_thread().name}]'
                f'[IdempotencyManager][is_duplicate][ERROR] - '
                f'error: {e}, token: {token[:16]}... [{datetime.now()}]'
            )
            
            if self.logger:
                self.logger.log_error(
                    f"Error checking duplicate",
                    {"token": token[:16], "exception": str(e)}
                )
            
            # On error, assume not duplicate to avoid blocking operations
            return False
    
    def record_execution(
        self,
        token: str,
        command_id: int,
        batch_id: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Store execution result for replay on retry.
        
        :param token: Idempotency token
        :param command_id: Command ID
        :param batch_id: Optional batch ID
        :param result: Execution result to cache
        :return: True if stored successfully
        """
        try:
            # Serialize result
            result_json = None
            if result:
                result_json = json.dumps(result)
            
            # Store token
            self.token_crud.add_token(
                token=token,
                command_id=command_id,
                batch_id=batch_id,
                execution_result=result_json
            )
            
            print(
                f'[ПОТОК][{threading.current_thread().name}]'
                f'[IdempotencyManager][record_execution][INFO] - '
                f'command_id: {command_id}, token: {token[:16]}... '
                f'[{datetime.now()}]'
            )
            
            if self.logger:
                self.logger.log_info(
                    f"Execution recorded for command {command_id}",
                    {
                        "token": token[:16],
                        "batch_id": batch_id,
                        "has_result": result is not None
                    }
                )
            
            return True
            
        except Exception as e:
            print(
                f'[ПОТОК][{threading.current_thread().name}]'
                f'[IdempotencyManager][record_execution][ERROR] - '
                f'error: {e}, подробности: - {traceback.format_exc()}. '
                f'[{datetime.now()}]'
            )
            
            if self.logger:
                self.logger.log_error(
                    f"Failed to record execution for command {command_id}",
                    {
                        "token": token[:16],
                        "exception": str(e)
                    }
                )
            
            return False
    
    def get_cached_result(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve stored result for duplicate command (for replay).
        
        :param token: Idempotency token
        :return: Cached result or None
        """
        try:
            token_record = self.token_crud.get_by_token(token)
            
            if not token_record:
                return None
            
            # Deserialize result
            if token_record.execution_result:
                result = json.loads(token_record.execution_result)
                
                print(
                    f'[ПОТОК][{threading.current_thread().name}]'
                    f'[IdempotencyManager][get_cached_result][INFO] - '
                    f'Cache hit: token={token[:16]}... [{datetime.now()}]'
                )
                
                if self.logger:
                    self.logger.log_info(
                        f"Cached result retrieved",
                        {"token": token[:16]}
                    )
                
                return result
            
            return None
            
        except Exception as e:
            print(
                f'[ПОТОК][{threading.current_thread().name}]'
                f'[IdempotencyManager][get_cached_result][ERROR] - '
                f'error: {e}, token: {token[:16]}... [{datetime.now()}]'
            )
            
            if self.logger:
                self.logger.log_error(
                    f"Error retrieving cached result",
                    {"token": token[:16], "exception": str(e)}
                )
            
            return None
    
    def cleanup_old_tokens(self, older_than_days: int = 7) -> int:
        """
        Automatic cleanup of old tokens to prevent database bloat.
        
        Called periodically by APScheduler (typically daily).
        Deletes tokens older than the specified retention period.
        
        Note: Retention should be shorter than snapshot retention
        since tokens are only needed during the retry window.
        
        :param older_than_days: Delete tokens older than this many days
        :return: Number of tokens deleted
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=older_than_days)
            
            print(
                f'[ПОТОК][{threading.current_thread().name}]'
                f'[IdempotencyManager][cleanup_old_tokens][INFO] - '
                f'Starting cleanup: older_than_days={older_than_days}, '
                f'cutoff_date={cutoff_date}. [{datetime.now()}]'
            )
            
            # Delete old tokens
            deleted_count = self.token_crud.cleanup_old_tokens(cutoff_date)
            
            print(
                f'[ПОТОК][{threading.current_thread().name}]'
                f'[IdempotencyManager][cleanup_old_tokens][INFO] - '
                f'Cleanup complete: deleted {deleted_count} tokens. '
                f'[{datetime.now()}]'
            )
            
            if self.logger:
                self.logger.log_info(
                    f"Token cleanup completed",
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
                f'[IdempotencyManager][cleanup_old_tokens][ERROR] - '
                f'error: {e}, подробности: - {traceback.format_exc()}. '
                f'[{datetime.now()}]'
            )
            
            if self.logger:
                self.logger.log_error(
                    f"Token cleanup failed",
                    {
                        "older_than_days": older_than_days,
                        "exception": str(e)
                    }
                )
            
            return 0
    
    def get_token_info(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve full token information.
        
        :param token: Idempotency token
        :return: Token info dictionary or None
        """
        try:
            token_record = self.token_crud.get_by_token(token)
            
            if not token_record:
                return None
            
            return {
                'token': token,
                'command_id': token_record.command_id,
                'batch_id': token_record.batch_id,
                'execution_result': json.loads(token_record.execution_result) if token_record.execution_result else None,
                'executed_at': token_record.executed_at.isoformat() if token_record.executed_at else None
            }
            
        except Exception as e:
            print(
                f'[ПОТОК][{threading.current_thread().name}]'
                f'[IdempotencyManager][get_token_info][ERROR] - '
                f'error: {e}, token: {token[:16]}... [{datetime.now()}]'
            )
            return None
    
    def invalidate_token(self, token: str) -> bool:
        """
        Invalidate (delete) a token.
        
        Useful for manual cleanup or testing.
        
        :param token: Token to invalidate
        :return: True if invalidated successfully
        """
        try:
            success = self.token_crud.delete_token(token)
            
            if success:
                print(
                    f'[ПОТОК][{threading.current_thread().name}]'
                    f'[IdempotencyManager][invalidate_token][INFO] - '
                    f'Token invalidated: {token[:16]}... [{datetime.now()}]'
                )
                
                if self.logger:
                    self.logger.log_info(
                        f"Token invalidated",
                        {"token": token[:16]}
                    )
            
            return success
            
        except Exception as e:
            print(
                f'[ПОТОК][{threading.current_thread().name}]'
                f'[IdempotencyManager][invalidate_token][ERROR] - '
                f'error: {e}, token: {token[:16]}... [{datetime.now()}]'
            )
            
            if self.logger:
                self.logger.log_error(
                    f"Failed to invalidate token",
                    {"token": token[:16], "exception": str(e)}
                )
            
            return False
