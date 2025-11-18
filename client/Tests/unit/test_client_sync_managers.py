import os
import sys
import pytest
from sqlalchemy import inspect
from datetime import datetime, timedelta

# Ensure 'client' package path so we can import client-side dbSync
_CURRENT_DIR = os.path.dirname(__file__)
# When invoked from project root or from client/, resolve client dir robustly
_PROJECT_OR_CLIENT = os.path.abspath(os.path.join(_CURRENT_DIR, "..", ".."))
if os.path.basename(_PROJECT_OR_CLIENT).lower() == "client":
    _CLIENT_DIR = _PROJECT_OR_CLIENT
else:
    _CLIENT_DIR = os.path.join(_PROJECT_OR_CLIENT, "client")
if _CLIENT_DIR not in sys.path:
    sys.path.insert(0, _CLIENT_DIR)

# Use client sync_db to create tables
from dbSync.sync_db import init_sync_db, get_sync_session
# Managers under test
from dbSync.Logic_v2.SnapshotManager import SnapshotManager
from dbSync.Logic_v2.IdempotencyManager import IdempotencyManager
# CRUDs
from dbSync.Engines.CommandSnapshotEngine import CommandSnapshotCRUD
from dbSync.Engines.IdempotencyTokenEngine import IdempotencyTokenCRUD


def fresh_engine_and_session():
    # Dispose previous engine to avoid Windows file locks
    try:
        import dbSync.sync_db as sync_db
        eng = sync_db._get_sync_engine()
        if eng:
            eng.dispose()
        sync_db._sync_engine = None
        sync_db._SessionLocal = None
    except Exception:
        pass

    init_sync_db(force_recreate=True)
    session = get_sync_session()
    engine = session.get_bind()
    return engine, session


def test_schema_has_required_columns_for_batch_and_token():
    engine, session = fresh_engine_and_session()
    insp = inspect(engine)

    # BatchExecution must include success/fail counters
    batch_cols = {c['name'] for c in insp.get_columns('BatchExecution')}
    assert 'successful_commands' in batch_cols, "BatchExecution missing 'successful_commands' column (client)"
    assert 'failed_commands' in batch_cols, "BatchExecution missing 'failed_commands' column (client)"

    # IdempotencyToken must include status, created_at, expires_at
    token_cols = {c['name'] for c in insp.get_columns('IdempotencyToken')}
    assert 'status' in token_cols, "IdempotencyToken missing 'status' column (client)"
    assert 'created_at' in token_cols, "IdempotencyToken missing 'created_at' column (client)"
    assert 'expires_at' in token_cols, "IdempotencyToken missing 'expires_at' column (client)"
    session.close()


def test_snapshot_manager_cleanup_calls_supported_crud_method():
    engine, session = fresh_engine_and_session()
    snapshot_crud = CommandSnapshotCRUD(session=session)
    mgr = SnapshotManager(snapshot_crud=snapshot_crud, work_session=session)

    # Should not raise AttributeError; should return int
    deleted = mgr.cleanup_old_snapshots(older_than_days=1)
    assert isinstance(deleted, int)
    session.close()


def test_idempotency_manager_cleanup_and_delete_alias():
    engine, session = fresh_engine_and_session()
    token_crud = IdempotencyTokenCRUD(session=session)
    mgr = IdempotencyManager(token_crud=token_crud)

    # cleanup should accept older_than_days and internally use datetime cutoff in CRUD (or CRUD should accept datetime)
    deleted = mgr.cleanup_old_tokens(older_than_days=0)
    assert isinstance(deleted, int)

    # Invalidate token via alias
    tkn = 'client-unit-test-token'
    token_crud.add_token(token=tkn, command_id=1, batch_id=None, execution_result=None)
    assert token_crud.get_by_token(tkn) is not None
    assert mgr.invalidate_token(tkn) is True
    assert token_crud.get_by_token(tkn) is None
    session.close()
