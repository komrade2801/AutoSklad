#!/usr/bin/env python3
"""
Database Debug Script
Inspects sync.db, web_vending.db, and vending.db to debug sync and delete operations.
"""

import sqlite3
import os
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

def inspect_database(db_path: str, db_name: str) -> Dict[str, Any]:
    """Inspect a SQLite database and return table information."""
    if not os.path.exists(db_path):
        return {"error": f"Database {db_path} does not exist"}

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        result = {
            "database": db_name,
            "path": db_path,
            "tables": {}
        }

        # Inspect key tables
        key_tables = ['Tools', 'ToolTypes', 'Group', 'Groups', 'Tools_has_Device', 'ToolTypes_has_Device',
                     'command_queue', 'command_status', 'sync_config']

        for table_name, in tables:
            if table_name in key_tables or 'sync' in table_name.lower():
                try:
                    # Get table info
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = cursor.fetchall()

                    # Get row count
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]

                    # Get sample data (first 5 rows)
                    try:
                        cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                        sample_data = cursor.fetchall()
                    except:
                        sample_data = []

                    result["tables"][table_name] = {
                        "columns": [{"name": col[1], "type": col[2]} for col in columns],
                        "row_count": count,
                        "sample_data": sample_data
                    }

                except Exception as e:
                    result["tables"][table_name] = {"error": str(e)}

        conn.close()
        return result

    except Exception as e:
        return {"error": f"Failed to inspect {db_name}: {str(e)}"}

def inspect_command_queue(queue_path: str) -> Dict[str, Any]:
    """Inspect the command queue JSON file."""
    if not os.path.exists(queue_path):
        return {"error": f"Command queue {queue_path} does not exist"}

    try:
        with open(queue_path, 'r', encoding='utf-8') as f:
            commands = json.load(f)

        # Analyze commands by status and operation
        stats = {
            "total": len(commands),
            "by_status": {},
            "by_operation": {},
            "by_table": {},
            "failed_commands": []
        }

        for cmd in commands:
            status = cmd.get('status', 'unknown')
            operation = cmd.get('operation', 'unknown')
            table = cmd.get('table', 'unknown')

            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            stats["by_operation"][operation] = stats["by_operation"].get(operation, 0) + 1
            stats["by_table"][table] = stats["by_table"].get(table, 0) + 1

            if status == 'failed':
                stats["failed_commands"].append({
                    "id": cmd.get('id'),
                    "table": table,
                    "operation": operation,
                    "timestamp": cmd.get('timestamp')
                })

        return {
            "command_queue": queue_path,
            "statistics": stats,
            "recent_commands": commands[-10:] if len(commands) > 10 else commands
        }

    except Exception as e:
        return {"error": f"Failed to inspect command queue: {str(e)}"}

def save_debug_report(report_data: Dict[str, Any], logs_dir: Path):
    """Save the debug report to a JSON file in the logs directory."""
    logs_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"debug_report_{timestamp}.json"
    filepath = logs_dir / filename

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
        print(f"📄 Debug report saved to: {filepath}")
    except Exception as e:
        print(f"❌ Failed to save debug report: {e}")

def main():
    """Main debug function."""
    print("=" * 80)
    print("DATABASE DEBUG INSPECTION")
    print("=" * 80)
    print(f"Timestamp: {datetime.now()}")
    print()

    # Define database paths
    base_dir = Path(__file__).parent.parent

    databases = {
        "web_vending.db": base_dir / "DB" / "Data" / "web_vending.db",
        "sync.db": base_dir / "dbSync" / "Model" / "sync.db",
        "vending.db": base_dir / ".." / "client" / "Model" / "sync.db"  # Client database
    }

    command_queue = base_dir / "command_queue.json"
    logs_dir = base_dir / "tests" / "logs"

    # Collect all debug data
    debug_report = {
        "timestamp": datetime.now().isoformat(),
        "command_queue": {},
        "databases": {}
    }

    # Inspect command queue first
    print("COMMAND QUEUE INSPECTION")
    print("-" * 40)
    queue_info = inspect_command_queue(str(command_queue))
    debug_report["command_queue"] = queue_info

    if "error" in queue_info:
        print(f"❌ {queue_info['error']}")
    else:
        stats = queue_info["statistics"]
        print(f"📊 Total commands: {stats['total']}")
        print(f"📈 By status: {stats['by_status']}")
        print(f"🔧 By operation: {stats['by_operation']}")
        print(f"📋 By table: {stats['by_table']}")

        if stats["by_status"].get("failed", 0) > 0:
            print(f"\n❌ FAILED COMMANDS ({len(stats['failed_commands'])}):")
            for cmd in stats["failed_commands"][-5:]:  # Show last 5 failed
                print(f"  - {cmd['table']} {cmd['operation']} (ID: {cmd['id'][:8]}...)")

    print("\n" + "=" * 80)

    # Inspect each database
    for db_name, db_path in databases.items():
        print(f"\nDATABASE: {db_name.upper()}")
        print("-" * 40)

        db_info = inspect_database(str(db_path), db_name)
        debug_report["databases"][db_name] = db_info

        if "error" in db_info:
            print(f"❌ {db_info['error']}")
            continue

        print(f"📁 Path: {db_info['path']}")

        # Show key table summaries
        key_tables = ['Tools', 'ToolTypes', 'Group', 'Groups']
        for table_name in key_tables:
            if table_name in db_info["tables"]:
                table_info = db_info["tables"][table_name]
                if "error" in table_info:
                    print(f"  ❌ {table_name}: Error - {table_info['error']}")
                else:
                    count = table_info["row_count"]
                    print(f"  📊 {table_name}: {count} records")

                    if count > 0 and table_info["sample_data"]:
                        print("    Sample data:")
                        for row in table_info["sample_data"][:2]:  # First 2 rows
                            print(f"      {row}")

        # Show sync-related tables
        sync_tables = [t for t in db_info["tables"].keys() if 'sync' in t.lower() or 'command' in t.lower()]
        if sync_tables:
            print("  🔄 Sync tables:")
            for table_name in sync_tables:
                table_info = db_info["tables"][table_name]
                if "error" in table_info:
                    print(f"    ❌ {table_name}: Error - {table_info['error']}")
                else:
                    count = table_info["row_count"]
                    print(f"    📋 {table_name}: {count} records")

    # Save debug report to logs folder
    save_debug_report(debug_report, logs_dir)

    print("\n" + "=" * 80)
    print("DEBUG COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
