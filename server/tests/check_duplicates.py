#!/usr/bin/env python3
"""
Script to check for duplicate records in Tools and ToolTypes tables
on both client and server databases.
"""

import sqlite3
import os
from pathlib import Path
from collections import defaultdict

def check_client_database():
    """Check client's database for duplicates."""
    print("=" * 60)
    print("CHECKING CLIENT DATABASE")
    print("=" * 60)

    client_db_path = Path("client/DB/Data/vending.db")
    if not client_db_path.exists():
        print(f"Client database not found at {client_db_path}")
        return

    conn = sqlite3.connect(client_db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Check Tools table
        print("\n--- TOOLS TABLE ---")
        cursor.execute("SELECT id, name, count, inventory_number, barcode, plan_id, tool_type_id, groups_id FROM Tools WHERE name LIKE '%Молоток большой%' OR name LIKE '%Пила ручная%' ORDER BY name, inventory_number")
        tools = cursor.fetchall()

        print(f"Total tools records: {len(tools)}")

        # Group by name and inventory_number to find duplicates
        tools_by_spec = defaultdict(list)
        for tool in tools:
            key = f"{tool['name']} - {tool['inventory_number']}"
            tools_by_spec[key].append(dict(tool))

        print("\nDuplicate analysis:")
        for spec, records in tools_by_spec.items():
            if len(records) > 1:
                print(f"\n🔴 DUPLICATE: {spec} (count: {len(records)})")
                for i, record in enumerate(records, 1):
                    print(f"  {i}. ID: {record['id']}, Count: {record['count']}")
            else:
                print(f"✅ UNIQUE: {spec} (count: {len(records)}) - ID: {records[0]['id']}, Count: {records[0]['count']}")

        # Check ToolTypes table
        print("\n--- TOOL TYPES TABLE ---")
        cursor.execute("SELECT id, name, count, groups_id FROM ToolTypes ORDER BY name, id")
        tool_types = cursor.fetchall()

        print(f"Total tool types records: {len(tool_types)}")

        # Group by name to find duplicates
        types_by_name = defaultdict(list)
        for tt in tool_types:
            types_by_name[tt['name']].append(dict(tt))

        print("\nDuplicate analysis:")
        for name, records in types_by_name.items():
            if len(records) > 1:
                print(f"\n🔴 DUPLICATE: {name} (count: {len(records)})")
                for i, record in enumerate(records, 1):
                    print(f"  {i}. ID: {record['id']}, Count: {record['count']}")
            else:
                print(f"✅ UNIQUE: {name} (count: {len(records)}) - ID: {records[0]['id']}, Count: {records[0]['count']}")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()

def check_server_database():
    """Check server's database for duplicates."""
    print("=" * 60)
    print("CHECKING SERVER DATABASE")
    print("=" * 60)

    server_db_path = Path("server/DB/Data/web_vending.db")
    if not server_db_path.exists():
        print(f"Server database not found at {server_db_path}")
        return

    conn = sqlite3.connect(server_db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Get table list first
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row['name'] for row in cursor.fetchall()]
        print(f"Available tables: {', '.join(tables)}")

        # Check if we have Tools and ToolTypes tables
        if 'Tools' not in tables:
            print("⚠️  Tools table not found in server database")
            return

        # Check Tools table
        print("\n--- SERVER TOOLS TABLE ---")
        cursor.execute("SELECT id, name, count, inventory_number, barcode, plan_id, tool_type_id, groups_id FROM Tools WHERE name LIKE '%Молоток большой%' OR name LIKE '%Пила ручная%' ORDER BY name, inventory_number")
        tools = cursor.fetchall()

        print(f"Total tools records: {len(tools)}")

        if tools:
            # Group by name and inventory_number
            tools_by_spec = defaultdict(list)
            for tool in tools:
                key = f"{tool['name']} - {tool['inventory_number']}"
                tools_by_spec[key].append(dict(tool))

            print("\nDuplicate analysis:")
            for spec, records in tools_by_spec.items():
                if len(records) > 1:
                    print(f"\n🔴 DUPLICATE: {spec} (count: {len(records)})")
                    for i, record in enumerate(records, 1):
                        print(f"  {i}. ID: {record['id']}, Count: {record['count']}")
                else:
                    print(f"✅ UNIQUE: {spec} (count: {len(records)}) - ID: {records[0]['id']}, Count: {records[0]['count']}")

        # Check ToolTypes table if it exists
        if 'ToolTypes' in tables:
            print("\n--- SERVER TOOL TYPES TABLE ---")
            cursor.execute("SELECT id, name, count, groups_id FROM ToolTypes ORDER BY name, id")
            tool_types = cursor.fetchall()

            print(f"Total tool types records: {len(tool_types)}")

            if tool_types:
                # Group by name
                types_by_name = defaultdict(list)
                for tt in tool_types:
                    types_by_name[tt['name']].append(dict(tt))

                print("\nDuplicate analysis:")
                for name, records in types_by_name.items():
                    if len(records) > 1:
                        print(f"\n🔴 DUPLICATE: {name} (count: {len(records)})")
                        for i, record in enumerate(records, 1):
                            print(f"  {i}. ID: {record['id']}, Count: {record['count']}")
                    else:
                        print(f"✅ UNIQUE: {name} (count: {len(records)}) - ID: {records[0]['id']}, Count: {records[0]['count']}")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()

def get_database_info():
    """Get basic database information."""
    print("=" * 60)
    print("DATABASE INFORMATION")
    print("=" * 60)

    client_db_path = Path("client/DB/Data/vending.db")
    server_db_path = Path("server/DB/Data/web_vending.db")

    print(f"Current directory: {os.getcwd()}")
    print(f"Client DB exists: {client_db_path.exists()} ({client_db_path.absolute()})")
    print(f"Server DB exists: {server_db_path.exists()} ({server_db_path.absolute()})")

    if client_db_path.exists():
        client_size = client_db_path.stat().st_size
        print(f"Client DB size: {client_size} bytes ({client_size/1024:.1f} KB)")

    if server_db_path.exists():
        server_size = server_db_path.stat().st_size
        print(f"Server DB size: {server_size} bytes ({server_size/1024:.1f} KB)")

def main():
    print("AUTO SKLAD DATABASE DUPLICATE ANALYSIS")
    print("======================================\n")

    get_database_info()
    check_client_database()
    check_server_database()

    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)
    print("Look for 🔴 DUPLICATE entries above - these indicate data duplication issues")

if __name__ == "__main__":
    main()
