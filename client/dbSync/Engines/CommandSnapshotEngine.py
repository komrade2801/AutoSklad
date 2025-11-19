"""
CommandSnapshot CRUD Engine - Database operations for snapshot management

Handles creation, retrieval, and cleanup of pre-execution snapshots
used for rollback compensation.
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from ..Model.CommandSnapshot import CommandSnapshot
from dbSync.Engines.CRUD import BaseCRUD


class CommandSnapshotCRUD(BaseCRUD):
    """
    CRUD operations for CommandSnapshot model.
    
    Primary Operations:
    - add_snapshot: Create snapshot before command execution
    - get_by_command: Retrieve snapshot for specific command
    - get_by_batch: Retrieve all snapshots for batch
    - delete_by_command: Clean up snapshot after successful commit
    - bulk_delete: Clean up snapshots for entire batch
    
    Architecture Integration:
    - Called by SnapshotManager.capture_snapshot()
    - Used by SnapshotManager.generate_compensation()
    - Cleanup after successful batch commit (optional)
    """
    
    def __init__(self, session: Session):
        """
        Initialize CommandSnapshot CRUD engine.
        
        :param session: SQLAlchemy session for sync.db
        """
        super().__init__(session, CommandSnapshot)
    
    def add_snapshot(
        self,
        command_id: int,
        table_name: str,
        record_id: Optional[int],
        snapshot_data: Optional[str],
        operation: str
    ) -> int:
        """
        Create snapshot record for command.
        
        :param command_id: ID of command being snapshotted
        :param table_name: Name of table being modified
        :param record_id: ID of record being modified (None for INSERT)
        :param snapshot_data: JSON string of record state (None for INSERT)
        :param operation: Operation type (insert, update, delete)
        :return: Created snapshot ID
        """
        snapshot = CommandSnapshot(
            command_id=command_id,
            table_name=table_name,
            record_id=record_id,
            snapshot_data=snapshot_data,
            operation=operation.lower()
        )
        
        self.session.add(snapshot)
        self.session.flush()  # Get ID without committing
        
        return snapshot.id
    
    def get_by_command(self, command_id: int) -> Optional[CommandSnapshot]:
        """
        Retrieve snapshot for specific command.
        
        :param command_id: Command ID
        :return: CommandSnapshot instance or None
        """
        return self.session.query(CommandSnapshot).filter_by(
            command_id=command_id
        ).first()
    
    def get_by_commands(self, command_ids: List[int]) -> List[CommandSnapshot]:
        """
        Retrieve snapshots for multiple commands.
        
        :param command_ids: List of command IDs
        :return: List of CommandSnapshot instances
        """
        return self.session.query(CommandSnapshot).filter(
            CommandSnapshot.command_id.in_(command_ids)
        ).order_by(CommandSnapshot.id).all()
    
    def get_by_table(
        self, 
        table_name: str, 
        record_id: Optional[int] = None
    ) -> List[CommandSnapshot]:
        """
        Retrieve snapshots for specific table/record.
        
        :param table_name: Table name
        :param record_id: Optional record ID filter
        :return: List of CommandSnapshot instances
        """
        query = self.session.query(CommandSnapshot).filter_by(
            table_name=table_name
        )
        
        if record_id is not None:
            query = query.filter_by(record_id=record_id)
        
        return query.order_by(CommandSnapshot.created_at.desc()).all()
    
    def delete_by_command(self, command_id: int) -> bool:
        """
        Delete snapshot for specific command.
        
        Used for cleanup after successful commit.
        
        :param command_id: Command ID
        :return: True if deleted, False if not found
        """
        snapshot = self.get_by_command(command_id)
        
        if snapshot:
            self.session.delete(snapshot)
            self.session.flush()
            return True
        
        return False
    
    def bulk_delete(self, command_ids: List[int]) -> int:
        """
        Delete snapshots for multiple commands.
        
        Used for batch cleanup after successful commit.
        
        :param command_ids: List of command IDs
        :return: Number of snapshots deleted
        """
        count = self.session.query(CommandSnapshot).filter(
            CommandSnapshot.command_id.in_(command_ids)
        ).delete(synchronize_session=False)
        
        self.session.flush()
        return count
    
    def count_by_table(self, table_name: str) -> int:
        """
        Count snapshots for specific table.
        
        Useful for monitoring and diagnostics.
        
        :param table_name: Table name
        :return: Count of snapshots
        """
        return self.session.query(CommandSnapshot).filter_by(
            table_name=table_name
        ).count()
    
    def get_all_snapshots(self, limit: int = 100) -> List[CommandSnapshot]:
        """
        Retrieve all snapshots (limited).
        
        For diagnostic and monitoring purposes.
        
        :param limit: Maximum number of snapshots to retrieve
        :return: List of CommandSnapshot instances
        """
        return self.session.query(CommandSnapshot).order_by(
            CommandSnapshot.created_at.desc()
        ).limit(limit).all()
