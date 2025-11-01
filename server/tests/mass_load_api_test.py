#!/usr/bin/env python3
"""
Mass Load API Test for AutoSklad

This script tests the mass loading functionality by:
1. Creating 5 tool types with total 40 individual tools
2. Performing mass load operation distributing all 40 tools randomly across free cells
3. Saving the mass load

Usage:
    python mass_load_api_test.py [--url BASE_URL]

Example:
    python mass_load_api_test.py --url http://127.0.0.1:8000
"""

import requests
import json
import argparse
import time
import random
from datetime import datetime
from pathlib import Path
from api_connectivity_test import ApiConnectivityTest


class MassLoadApiTest(ApiConnectivityTest):
    """Test mass loading functionality with real HTTP requests."""

    def run_mass_load_test(self):
        """Run the full mass load test."""
        print("=" * 60)
        print("MASS LOAD API TEST")
        print("=" * 60)
        print(f"Server URL: {self.base_url}")
        print(f"Test started: {self.start_time}")

        # Create logs directory if it doesn't exist
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)

        # Create log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = logs_dir / f"mass_load_api_test_{timestamp}.txt"

        with log_file.open("w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write("MASS LOAD API TEST\n")
            f.write("=" * 60 + "\n")
            f.write(f"Server URL: {self.base_url}\n")
            f.write(f"Test started: {self.start_time}\n")
            f.write("\n")

        # Step 1: Create test groups and tools
        print("\n" + "=" * 40)
        print("STEP 1: CREATING TEST DATA")
        print("=" * 40)

        # Create a test group
        group_data = {
            "group_name": "Тестовые инструменты",
            "parent_group": 0,
            "description": "Группа для тестирования массовой загрузки",
            "img": ""
        }

        print("\n--- Creating Test Group ---")
        group_response = self.make_request("POST", "/backend/create_groups", group_data)

        if not group_response or not isinstance(group_response, dict) or group_response.get("status") != 200:
            print("❌ Failed to create test group. Aborting.")
            return False

        # Create 5 tool types with total 40 tools
        tools_data = [
            {
                "group_id": 1,  # Assuming group ID 1 (adjust if needed)
                "tool_name": "Молоток тестовый",
                "description": "Тестовый молоток для массовой загрузки",
                "count": 8,
                "img": "",
                "tools": {str(i+1): f"M{i+1:03d}" for i in range(8)}
            },
            {
                "group_id": 1,
                "tool_name": "Отвёртка тестовая",
                "description": "Тестовая отвёртка для массовой загрузки",
                "count": 6,
                "img": "",
                "tools": {str(i+1): f"S{i+1:03d}" for i in range(6)}
            },
            {
                "group_id": 1,
                "tool_name": "Дрель тестовая",
                "description": "Тестовая дрель для массовой загрузки",
                "count": 10,
                "img": "",
                "tools": {str(i+1): f"D{i+1:03d}" for i in range(10)}
            },
            {
                "group_id": 1,
                "tool_name": "Пила тестовая",
                "description": "Тестовая пила для массовой загрузки",
                "count": 8,
                "img": "",
                "tools": {str(i+1): f"P{i+1:03d}" for i in range(8)}
            },
            {
                "group_id": 1,
                "tool_name": "Ключ тестовый",
                "description": "Тестовый ключ для массовой загрузки",
                "count": 8,
                "img": "",
                "tools": {str(i+1): f"K{i+1:03d}" for i in range(8)}
            }
        ]

        created_tools = 0
        total_individual_tools = 0

        for i, tool_data in enumerate(tools_data, 1):
            print(f"\n--- Creating Tool Type {i}/5: {tool_data['tool_name']} ---")
            response = self.make_request("POST", "/backend/create_tools", tool_data)

            if response and isinstance(response, dict) and response.get("status") == 200:
                created_tools += 1
                total_individual_tools += tool_data["count"]
                print(f"✓ Created {tool_data['count']} {tool_data['tool_name']} tools")
            else:
                print(f"✗ Failed to create {tool_data['tool_name']}")

            time.sleep(0.5)

        print(f"\nTool types created: {created_tools}/5")
        print(f"Individual tools created: {total_individual_tools}")

        if created_tools != 5:
            print("❌ Not all tools created. Aborting mass load test.")
            return False

        # Step 2: Get available tools for mass loading
        print("\n" + "=" * 40)
        print("STEP 2: GETTING AVAILABLE TOOLS")
        print("=" * 40)

        tools_response = self.make_request("GET", "/backend/mass_load_tools?device_number=1")

        if not tools_response or not isinstance(tools_response, dict) or "plans" not in tools_response:
            print("❌ Failed to get available tools")
            return False

        print("✓ Retrieved available tools for mass loading")

        # Step 3: Get free cells
        print("\n" + "=" * 40)
        print("STEP 3: GETTING FREE CELLS")
        print("=" * 40)

        cells_response = self.make_request("GET", "/backend/cells_map/1")

        if not cells_response or not isinstance(cells_response, dict) or "rows" not in cells_response:
            print("❌ Failed to get cells map")
            return False

        # Find free cells (block: false)
        free_cells = []
        for row_key, row_data in cells_response["rows"].items():
            for cell_key, cell_data in row_data["cells"].items():
                if not cell_data.get("block", True):
                    free_cells.append(cell_data["id"])

        free_cells.sort()
        print(f"✓ Found {len(free_cells)} free cells: {free_cells[:10]}{'...' if len(free_cells) > 10 else ''}")

        if len(free_cells) < 40:
            print(f"❌ Not enough free cells. Need 40, have {len(free_cells)}. Aborting.")
            return False

        # Step 4: Create mass load operations
        print("\n" + "=" * 40)
        print("STEP 4: CREATING MASS LOAD OPERATIONS")
        print("=" * 40)

        # Collect all available tools
        available_tools = []
        for plan_key, plan_data in tools_response["plans"].items():
            for group_key, group_data in plan_data["groups"].items():
                for value_key, tool_data in group_data["value"].items():
                    if int(tool_data["sum"]) > 0:
                        available_tools.append({
                            "plan": plan_data["name"],
                            "group": group_data["name"],
                            "tool": f"{group_data['name']} {tool_data['name']}",
                            "available": int(tool_data["sum"])
                        })

        print(f"✓ Found {len(available_tools)} tool types with available items")

        # Create operations for all 40 tools
        operations = {}
        used_cells = set()
        op_index = 1

        # Shuffle free cells for random distribution
        random.shuffle(free_cells)

        for tool_info in available_tools:
            tools_to_load = min(tool_info["available"], 40 - (op_index - 1))
            if tools_to_load <= 0:
                continue

            for i in range(tools_to_load):
                if op_index > 40:
                    break

                # Find a free cell
                cell_id = None
                for cell in free_cells:
                    if cell not in used_cells:
                        cell_id = cell
                        used_cells.add(cell)
                        break

                if not cell_id:
                    print("❌ Ran out of free cells")
                    return False

                operations[str(op_index)] = {
                    "cell": str(cell_id),
                    "tool": tool_info["tool"],
                    "plan": tool_info["plan"]
                }

                print(f"  Operation {op_index}: {tool_info['tool']} → Cell {cell_id}")
                op_index += 1

                if op_index > 40:
                    break

            if op_index > 40:
                break

        print(f"✓ Created {len(operations)} mass load operations")

        # Step 5: Save mass load
        print("\n" + "=" * 40)
        print("STEP 5: SAVING MASS LOAD")
        print("=" * 40)

        mass_load_payload = {
            "operation": operations
        }

        print(f"Sending mass load with {len(operations)} operations...")
        save_response = self.make_request("POST", "/backend/mass_load_tools/1", mass_load_payload)

        if save_response and isinstance(save_response, dict) and "status" in save_response:
            if save_response["status"] == "ok":
                print("✓ Mass load saved successfully!")
                print(f"Message: {save_response.get('message', 'N/A')}")
                success = True
            else:
                print(f"✗ Mass load failed: {save_response}")
                success = False
        else:
            print("✗ Mass load request failed")
            success = False

        # Log results
        test_end_time = datetime.now()
        test_duration = (test_end_time - self.start_time).total_seconds()

        print("\n" + "=" * 60)
        print("MASS LOAD TEST SUMMARY")
        print("=" * 60)
        print(f"Test duration: {test_duration:.2f} seconds")
        print(f"Tool types created: {created_tools}/5")
        print(f"Individual tools created: {total_individual_tools}")
        print(f"Free cells available: {len(free_cells)}")
        print(f"Mass load operations: {len(operations)}")
        print(f"Mass load success: {success}")

        # Write to log file
        with log_file.open("a", encoding="utf-8") as f:
            f.write("=== MASS LOAD TEST SUMMARY ===\n")
            f.write(f"Test duration: {test_duration:.2f} seconds\n")
            f.write(f"Tool types created: {created_tools}/5\n")
            f.write(f"Individual tools created: {total_individual_tools}\n")
            f.write(f"Free cells available: {len(free_cells)}\n")
            f.write(f"Mass load operations created: {len(operations)}\n")
            f.write(f"Mass load success: {success}\n")
            f.write(f"Test completed: {test_end_time}\n")

        print(f"\n✓ Log saved to: {log_file.absolute()}")

        return success


def main():
    parser = argparse.ArgumentParser(description="Mass Load API test for AutoSklad")
    parser.add_argument("--url", default="http://127.0.0.1:8000",
                       help="Base URL of the running server (default: http://127.0.0.1:8000)")

    args = parser.parse_args()

    print("AutoSklad Mass Load API Test")
    print("=" * 50)
    print(f"Target URL: {args.url}")
    print()

    tester = MassLoadApiTest(args.url)

    # Authenticate first
    if not tester.authenticate():
        print("❌ Authentication failed. Aborting tests.")
        return 1

    try:
        success = tester.run_mass_load_test()
        if success:
            print("\n✅ Mass load API test completed successfully!")
            return 0
        else:
            print("\n❌ Mass load API test failed!")
            return 1
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
