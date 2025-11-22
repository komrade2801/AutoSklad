#!/usr/bin/env python3
"""
Database Dump Utility

Standalone script to dump schema and data from AutoSklad databases.
Supports multiple database files and shows last 10 rows per table for debugging.

Usage:
    python scripts/db_dump.py --list-databases
    python scripts/db_dump.py --database client/Model/sync.db --tables Command History --last10
    python scripts/db_dump.py --databases client/Model/sync.db server/dbSync/Model/sync.db --schema
    python scripts/db_dump.py --database client/DB/Data/vending.db --all
"""

import os
import sys
import argparse
import json
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class DatabaseDumper:
    """Handles database connections and data extraction"""

    # Known database file paths
    KNOWN_DBS = {
        'client_sync': 'client/Model/sync.db',
        'client_vending': 'client/DB/Data/vending.db',
        'server_sync': 'server/dbSync/Model/sync.db',
        'server_web': 'server/DB/Data/web_vending.db'
    }

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.db_name = Path(db_path).name
        self.connection = None

    def connect(self) -> bool:
        """Connect to SQLite database"""
        try:
            import sqlite3
            print(f"[{self.db_name}] Connecting to: {self.db_path}")
            if not Path(self.db_path).exists():
                print(f"[{self.db_name}] Database file not found: {self.db_path}")
                return False

            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            print(f"[{self.db_name}] Connected successfully")
            return True

        except Exception as e:
            print(f"[{self.db_name}] Connection failed: {e}")
            return False

    def get_tables(self) -> List[str]:
        """Get list of all tables in database"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            return [row[0] for row in cursor.fetchall() if not row[0].startswith('sqlite_')]
        except Exception as e:
            print(f"[{self.db_name}] Failed to get tables: {e}")
            return []

    def get_schema(self, table: str) -> Dict[str, Any]:
        """Get table schema information"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"PRAGMA table_info({table})")
            columns = []
            for row in cursor.fetchall():
                columns.append({
                    'name': row[1],
                    'type': row[2],
                    'notnull': bool(row[3]),  # 0 or 1
                    'default': row[4],
                    'pk': bool(row[5])  # 0 or 1
                })
            return {'columns': columns}
        except Exception as e:
            print(f"[{self.db_name}] Failed to get schema for {table}: {e}")
            return {}

    def get_table_data(self, table: str, limit: int = 50, last_rows: bool = False) -> List[Dict[str, Any]]:
        """Get data from table"""
        try:
            if last_rows:
                # Get last N rows using ORDER BY rowid DESC
                query = f"SELECT * FROM {table} ORDER BY rowid DESC LIMIT {limit}"
            else:
                query = f"SELECT * FROM {table} LIMIT {limit}"

            cursor = self.connection.cursor()
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            data = [dict(zip(columns, row)) for row in cursor.fetchall()]

            # If we got last rows but user expects chronological order, reverse back
            if last_rows:
                print(f"[{self.db_name}] Showing LAST {len(data)} rows from {table}")
            else:
                print(f"[{self.db_name}] Showing FIRST {len(data)} rows from {table}")

            return data

        except Exception as e:
            print(f"[{self.db_name}] Failed to get data from {table}: {e}")
            return []

    def dump_table(self, table: str, show_data: bool = True, last_rows: bool = False):
        """Dump schema and data for a specific table"""
        print(f"\n=== {self.db_name} - TABLE: {table} ===")

        # Schema
        schema = self.get_schema(table)
        if schema:
            print(f"Schema: {len(schema.get('columns', []))} columns")
            for col in schema.get('columns', []):
                pk_marker = " [PK]" if col.get('pk') else ""
                nn_marker = " [NOT NULL]" if col.get('notnull') else ""
                default_marker = f" [DEFAULT: {col.get('default')}]" if col.get('default') else ""
                print(f"  {col['name']} ({col['type']}){pk_marker}{nn_marker}{default_marker}")

        # Data
        if show_data:
            data = self.get_table_data(table, limit=10, last_rows=last_rows)
            print(f"Data: {len(data)} rows (showing last 10)" if last_rows else f"Data: {len(data)} rows (showing first 10)")
            if data:
                for i, row in enumerate(data, 1):
                    print(f"  Row {i}: {row}")
            else:
                print("  [No data]")

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            print(f"[{self.db_name}] Connection closed")

def list_known_databases():
    """List all known database files and their status"""
    print("AutoSklad Known Database Files:")
    print("=" * 50)

    root = Path(__file__).parent.parent
    found_count = 0

    for alias, rel_path in DatabaseDumper.KNOWN_DBS.items():
        full_path = root / rel_path
        status = "EXISTS" if full_path.exists() else "NOT FOUND"
        size = f"({full_path.stat().st_size} bytes)" if full_path.exists() else ""
        print(f"  {alias:15} {full_path} {status} {size}")
        if full_path.exists():
            found_count += 1

    print(f"\nSummary: {found_count}/{len(DatabaseDumper.KNOWN_DBS)} database files found")

def main():
    parser = argparse.ArgumentParser(description="Database Dump Utility for AutoSklad")
    parser.add_argument('--list-databases', action='store_true', help='List all known database files and their status')
    parser.add_argument('--database', help='Specific SQLite database file to dump')
    parser.add_argument('--databases', nargs='*', help='Multiple database files to dump')
    parser.add_argument('--tables', nargs='*', help='Specific tables to dump (default: all)')
    parser.add_argument('--all', action='store_true', help='Dump all tables in each database')
    parser.add_argument('--schema-only', action='store_true', help='Show schema only, no data')
    parser.add_argument('--last10', action='store_true', help='Show last 10 rows instead of first 10')

    args = parser.parse_args()

    # List known databases
    if args.list_databases:
        list_known_databases()
        return 0

    # Determine which databases to dump
    databases = []
    if args.database:
        databases = [args.database]
    elif args.databases:
        databases = args.databases
    else:
        print("ERROR: Specify --database <path> or --databases <path1> <path2> or --list-databases")
        return 1

    show_data = not args.schema_only
    last_rows = args.last10

    for db_path in databases:
        # Resolve known aliases
        if db_path in DatabaseDumper.KNOWN_DBS:
            rel_path = DatabaseDumper.KNOWN_DBS[db_path]
            db_path = str(Path(__file__).parent.parent / rel_path)

        print(f"\n{'='*80}")
        print(f"DUMPING: {db_path}")
        print(f"{'='*80}")

        dumper = DatabaseDumper(db_path)
        if not dumper.connect():
            continue

        tables = dumper.get_tables()
        print(f"Found {len(tables)} tables: {', '.join(tables[:10])}{'...' if len(tables) > 10 else ''}")

        # Filter tables if specific ones requested
        if args.tables and not args.all:
            tables = [t for t in tables if t.lower() in [at.lower() for at in args.tables]]
            if not tables:
                print(f"No matching tables found for: {args.tables}")
                dumper.close()
                continue

        # Dump each table
        for table in sorted(tables):
            show_table_data = show_data and (args.all or len(args.tables or []) <= 5)
            dumper.dump_table(table, show_data=show_table_data, last_rows=last_rows)

        dumper.close()

    return 0

if __name__ == "__main__":
    sys.exit(main())
