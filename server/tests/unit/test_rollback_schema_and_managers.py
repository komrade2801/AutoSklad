import os
import sys
import pytest
from sqlalchemy import inspect
from datetime import datetime, timedelta

# Ensure 'server' package is importable as top-level for dbSync imports used by code
_CURRENT_DIR = os.path.dirname(__file__)
_PROJECT_ROOT = os.path.abspath(os.path.join(_CURRENT_DIR, "..", "..", ".."))
_SERVER_DIR = os.path.join(_PROJECT_ROOT, "server")
if _SERVER_DIR not in sys.path:
    sys.path.insert(0, _SERVER_DIR)

# Use server sync_db to create tables
from dbSync.sync_db import init_sync_db, get_sync_session

# Managers under test
from dbSync.Logic_v2.SnapshotManager import SnapshotManager
from dbSync.Logic_v2.IdempotencyManager import IdempotencyManager

# CRUDs (real implementations)
from dbSync.Engines.CommandSnapshotEngine import CommandSnapshotCRUD
from dbSync.Engines.IdempotencyTokenEngine import IdempotencyTokenCRUD


def fresh_engine_and_session():
    # Ensure previous engine is disposed to avoid Windows file lock
    try:
        import dbSync.sync_db as sync_db
        eng = sync_db._get_sync_engine()
        if eng:
            eng.dispose()
        # reset globals so new engine/session will be created
        sync_db._sync_engine = None
        sync_db._SessionLocal = None
    except Exception:
        pass

    # Recreate sync.db to ensure fresh schema
    init_sync_db(force_recreate=True)
    session = get_sync_session()
    engine = session.get_bind()
    return engine, session


def test_schema_has_required_columns_for_batch_and_token():
    engine, session = fresh_engine_and_session()
    insp = inspect(engine)

    # BatchExecution must include success/fail counters
    batch_cols = {c['name'] for c in insp.get_columns('BatchExecution')}
    assert 'successful_commands' in batch_cols, "BatchExecution missing 'successful_commands' column"
    assert 'failed_commands' in batch_cols, "BatchExecution missing 'failed_commands' column"

    # IdempotencyToken must include status, created_at, expires_at
    token_cols = {c['name'] for c in insp.get_columns('IdempotencyToken')}
    assert 'status' in token_cols, "IdempotencyToken missing 'status' column"
    assert 'created_at' in token_cols, "IdempotencyToken missing 'created_at' column"
    assert 'expires_at' in token_cols, "IdempotencyToken missing 'expires_at' column"
    session.close()


def test_snapshot_manager_cleanup_calls_supported_crud_method():
    engine, session = fresh_engine_and_session()
    snapshot_crud = CommandSnapshotCRUD(session=session)

    # Manager should call CRUD method that exists: bulk_delete_older_than
    mgr = SnapshotManager(snapshot_crud=snapshot_crud, work_session=session)

    # Should not raise AttributeError
    deleted = mgr.cleanup_old_snapshots(older_than_days=1)
    assert isinstance(deleted, int)
    session.close()


def test_idempotency_manager_cleanup_uses_datetime_cutoff_and_delete_alias():
    engine, session = fresh_engine_and_session()
    token_crud = IdempotencyTokenCRUD(session=session)
    mgr = IdempotencyManager(token_crud=token_crud)

    # Ensure cleanup accepts older_than_days and internally converts to datetime for CRUD
    deleted = mgr.cleanup_old_tokens(older_than_days=0)  # cutoff = now
    assert isinstance(deleted, int)

    # Ensure invalidate_token delegates to CRUD correctly (alias exists)
    # Create a token, then invalidate
    tkn = 'unit-test-token'
    token_crud.add_token(token=tkn, command_id=1, batch_id=None, execution_result=None)
    assert token_crud.get_by_token(tkn) is not None
    assert mgr.invalidate_token(tkn) is True
    assert token_crud.get_by_token(tkn) is None
    session.close()
