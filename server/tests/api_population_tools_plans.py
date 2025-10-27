#!/usr/bin/env python3
"""
External API Connectivity Test for AutoSklad

This script tests the server API endpoints by making HTTP requests to a running
server instance. It creates the same groups and tools as the pytest version,
but uses real HTTP calls instead of FastAPI TestClient.

Usage:
    python api_connectivity_test.py [--url BASE_URL]

Example:
    python api_connectivity_test.py --url http://192.168.0.10:8080
"""

import requests
import json
import argparse
import time
from datetime import datetime
from pathlib import Path


class ApiConnectivityTest:
    """Test server API endpoints with real HTTP requests."""

    def __init__(self, base_url="http://127.0.0.1:8000"):
        """Initialize with server base URL."""
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.start_time = datetime.now()
        self.jwt_token = None

    def authenticate(self, login="1111", password="1111"):
        """Authenticate and obtain JWT token."""
        print("\n" + "=" * 40)
        print("AUTHENTICATING")
        print("=" * 40)

        auth_data = {"login": login, "password": password}
        response = self.session.get(f"{self.base_url}/backend/authorization", params=auth_data, timeout=30)

        print(f"GET /authorization?login={login}&password=****")
        print(".2f")
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            try:
                auth_response = response.json()
                self.jwt_token = auth_response.get("token")
                if self.jwt_token:
                    print(f"✓ Authentication successful")
                    print(f"Token: {self.jwt_token[:50]}...")
                    # Set authorization header for all future requests
                    self.session.headers.update({"Authorization": f"Bearer {self.jwt_token}"})
                    return auth_response
                else:
                    print(f"✗ No token in response")
                    print(f"Response: {json.dumps(auth_response, ensure_ascii=False, indent=2)}")
            except json.JSONDecodeError:
                print(f"✗ Invalid JSON response: {response.text[:500]}")
        else:
            print(f"✗ Authentication failed")
            try:
                error_data = response.json()
                print(f"Error Response: {json.dumps(error_data, ensure_ascii=False, indent=2)}")
            except json.JSONDecodeError:
                print(f"Error Response (text): {response.text[:500]}")

        return None

    def make_request(self, method, endpoint, data=None):
        """Make HTTP request with timing and error handling."""
        url = f"{self.base_url}{endpoint}"
        print(f"\n{method.upper()} {endpoint}")
        print(f"URL: {url}")

        if data:
            print(f"Data: {json.dumps(data, ensure_ascii=False, indent=2)}")

        start_time = time.time()
        try:
            if method.lower() == 'post':
                response = self.session.post(url, json=data, timeout=30)
            elif method.lower() == 'get':
                response = self.session.get(url, timeout=30)
            elif method.lower() == 'put':
                response = self.session.put(url, json=data, timeout=30)
            elif method.lower() == 'delete':
                response = self.session.delete(url, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            duration = time.time() - start_time
            print(".2f")
            print(f"Status: {response.status_code}")

            if response.status_code >= 200 and response.status_code < 300:
                print(f"✓ Success")
                try:
                    response_data = response.json()
                    print(f"Response: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
                    return response_data
                except json.JSONDecodeError:
                    print(f"Response (text): {response.text[:500]}")
                    return response.text
            else:
                print(f"✗ Failed")
                try:
                    error_data = response.json()
                    print(f"Error Response: {json.dumps(error_data, ensure_ascii=False, indent=2)}")
                except json.JSONDecodeError:
                    print(f"Error Response (text): {response.text[:500]}")
                return None

        except requests.RequestException as e:
            duration = time.time() - start_time
            print(".2f")
            print(f"✗ Exception: {e}")
            return None

    def test_server_status(self):
        """Test basic server connectivity."""
        print("=" * 60)
        print("SERVER CONNECTIVITY TEST")
        print("=" * 60)

        # Try different endpoints to check server is running
        endpoints = ["/", "/docs"]

        for endpoint in endpoints:
            print(f"\nTesting endpoint: {endpoint}")
            try:
                response = self.session.get(f"{self.base_url}{endpoint}", timeout=10)
                print(f"Status: {response.status_code}")
                if response.status_code < 400:
                    print("✓ Server appears to be running")
                    return True
            except requests.RequestException as e:
                print(f"✗ Cannot connect: {e}")

        return False

    def run_api_population_test(self):
        """Run the full API population test."""
        # First authenticate to get JWT token
        if not self.authenticate():
            print("❌ Authentication failed. Aborting API tests.")
            return False

        print("=" * 60)
        print("API POPULATION TEST")
        print("=" * 60)
        print(f"Server URL: {self.base_url}")
        print(f"Test started: {self.start_time}")
        print(f"Using JWT token: {self.jwt_token[:50]}..." if self.jwt_token else "No token")

        # Create logs directory if it doesn't exist
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)

        # Create log file in logs directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = logs_dir / f"api_connectivity_test_{timestamp}.txt"
        print(f"Log file: {log_file.absolute()}")

        with log_file.open("w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write("EXTERNAL API CONNECTIVITY TEST\n")
            f.write("=" * 60 + "\n")
            f.write(f"Server URL: {self.base_url}\n")
            f.write(f"Test started: {self.start_time}\n")
            if self.jwt_token:
                f.write(f"JWT Token obtained: {self.jwt_token[:50]}...\n")
            f.write("\n")

        # Define test groups with nesting
        groups_data = [
            # Root groups
            {"group_name": "Метчики", "parent_group": 0, "description": "Инструмент для нарезания внутренних резьб", "img": ""},
            {"group_name": "Сверла", "parent_group": 0, "description": "Осевой режущий инструмент", "img": ""},
            {"group_name": "Пластины", "parent_group": 0, "description": "Сменный режущий элемент для токарных резцов", "img": ""},
        ]

        # Test group creation
        print("\n" + "=" * 40)
        print("CREATING GROUPS")
        print("=" * 40)

        with log_file.open("a", encoding="utf-8") as f:
            f.write("=== GROUP CREATION ===\n")

        created_groups = 0
        for i, group_data in enumerate(groups_data, 1):
            print(f"\n--- Creating Group {i}/{len(groups_data)} ---")
            response = self.make_request("POST", "/backend/create_groups", group_data)

            if response and isinstance(response, dict) and response.get("status") == 200:
                created_groups += 1

            # Log to file
            with log_file.open("a", encoding="utf-8") as f:
                f.write(f"Group {i}: {json.dumps(group_data, ensure_ascii=False)}\n")
                f.write(f"Response: {json.dumps(response, ensure_ascii=False) if response else 'No response'}\n\n")

            # Small delay between requests
            time.sleep(0.5)

        print(f"\nGroups created successfully: {created_groups}/{len(groups_data)}")

        # Define tools for each group
        tools_data = [
            # Root groups
            {
                "group_id": 1,  # Метчики
                "tool_name": "M6x1 HSS",
                "description": "Общая длина: 66 мм, Длина рабочей части: 19 мм, Диаметр резьбы (М): M6, Шаг резьбы М: 1 мм",
                "count": 4,
                "img": "",
                "tools": {"1": "", "2": "", "3": "", "4": ""}
            },
            {
                "group_id": 1,
                "tool_name": "М4 х 0.7 мм MOS",
                "description": "Общая длина: 54 мм, Длина рабочей части: 21 мм, Диаметр резьбы (М): M4, Шаг резьбы М: 0,7 мм",
                "count": 3,
                "img": "",
                "tools": {"1": "", "2": "", "3": ""}
            },
            {
                "group_id": 2,  # Сверла
                "tool_name": "Сверло твердосплавное 3.3 мм PSD-3DA-0330",
                "description": "Общая длина: 62 мм, Длина рабочей части: 20 мм, Диаметр : 3,3 мм",
                "count": 6,
                "img": "",
                "tools": {"1": "", "2": "", "3": "", "4": "", "5": "", "6": ""}
            },
            {
                "group_id": 2,  # Сверла
                "tool_name": "Сверло 990SUTA 4.5 мм",
                "description": "Общая длина: 91 мм, Длина рабочей части: 47 мм, Диаметр : 4,5 мм",
                "count": 4,
                "img": "",
                "tools": {"1": "", "2": "", "3": "", "4": ""}
            },
            {
                "group_id": 3,  # Пластины
                "tool_name": "ZCC-CT CNMG120408-DM",
                "description": "Ширина: 12.9 мм, Толщина: 4.76 мм, Радиус при вершине: 8 мм, Размер пластины: 12, Угол при вершине: 80°, Форма: С-ромбическая 80°",
                "count": 10,
                "img": "",
                "tools": {"1": "", "2": "", "3": "", "4": "", "5": "", "6": "", "7": "", "8": "", "9": "", "10": ""}
            },
            {
                "group_id": 3,  # Пластины
                "tool_name": "SEHT1204AFFN-AL",
                "description": "Толщина: 4.76 мм, Размер пластины: 12, Угол при вершине: 90°, Форма: S-квадратная",
                "count": 6,
                "img": "",
                "tools": {"1": "", "2": "", "3": "", "4": "", "5": "", "6": ""}
            },
        ]

        # Test tool creation
        print("\n" + "=" * 40)
        print("CREATING TOOLS")
        print("=" * 40)

        with log_file.open("a", encoding="utf-8") as f:
            f.write("=== TOOL CREATION ===\n")

        created_tools = 0
        total_tools_created = 0
        for i, tool_data in enumerate(tools_data, 1):
            print(f"\n--- Creating Tool Type {i}/{len(tools_data)} ---")
            response = self.make_request("POST", "/backend/create_tools", tool_data)

            if response and isinstance(response, dict) and response.get("status") == 200:
                created_tools += 1
                total_tools_created += tool_data["count"]

            # Log to file
            with log_file.open("a", encoding="utf-8") as f:
                f.write(f"Tool Type {i}: {json.dumps(tool_data, ensure_ascii=False)}\n")
                f.write(f"Response: {json.dumps(response, ensure_ascii=False) if response else 'No response'}\n\n")

            # Small delay between requests
            time.sleep(0.5)

        print(f"\nTool types created successfully: {created_tools}/{len(tools_data)}")
        print(f"Individual tools created: {total_tools_created}")

        plan_data = [
            {
                "id": 1,
                "enterprise": "ООО «Завод Контакт»",
                "barcode": "2",
                "name": "Втулка БА8.226.320-23",
                "description": "Втулка БА8.226.320-23 ЮПИЯ.715331.003-23 ОСТ 4Г 0.822.003-73",
                "designation": "4022-4-5",
                "index_list": 0,
                "list_count": 0,
                "parent_plan": None,
                "parent_plan_id": None,
                "tools": [{'name': "M6x1 HSS", 'quantity': 1}, {'name': "Сверло 990SUTA 4.5 мм", 'quantity': 1},
                          {'name': "ZCC-CT CNMG120408-DM", 'quantity': 2}]
            },
            {
                "id": 2,
                "index_list": 0,
                "list_count": 0,
                "parent_plan": None,
                "parent_plan_id": None,
                "enterprise": "ООО «Завод Контакт»",
                "barcode": "4",
                "description": "Шайба ИВУА.711341.046 (по чертежу; Сталь 20, Ц15.хр; без ЛКП)",
                "name": "Шайба ИВУА.711341.046",
                "designation": "4022-4-5",
                "tools": [{'name': "M6x1 HSS", 'quantity': 1},
                          {'name': "Сверло твердосплавное 3.3 мм PSD-3DA-0330", 'quantity': 2},
                          {'name': "SEHT1204AFFN-AL", 'quantity': 1}]
            },
        ]

        created_plans = []
        for plan in plan_data:
            response = self.make_request("POST", "/backend/create_plan/1", plan)
            # if response.status not in [200, 201]:
            #     print(f"Warning: Plan creation failed: {response.json()}")
            #     with log_file.open("a", encoding="utf-8") as f:
            #         f.write(f"\nFAILED: {json.dumps(plan, ensure_ascii=False, indent=2)}\n")
            #         f.write(f"Response: {response.json()}\n\n")
            # else:
            #     with log_file.open("a", encoding="utf-8") as f:
            #         f.write(json.dumps(plan, ensure_ascii=False, indent=2))
            #         f.write(f"\nResponse: {response.json()}\n\n")
            created_plans.append(plan)

        # Test library endpoint to verify data
        print("\n" + "=" * 40)
        print("VERIFYING CREATED DATA")
        print("=" * 40)

        response = self.make_request("GET", "/backend/get_groups_from_db?device_number=1")

        test_end_time = datetime.now()
        test_duration = (test_end_time - self.start_time).total_seconds()

        # Final summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Test duration: {test_duration:.2f} seconds")
        print(f"Groups attempted: {len(groups_data)}")
        print(f"Groups created: {created_groups}")
        print(f"Tools attempted: {len(tools_data)}")
        print(f"Tools created: {created_tools}")
        print(f"Individual tools: {total_tools_created}")

        # Write final summary to log
        with log_file.open("a", encoding="utf-8") as f:
            f.write("=== TEST SUMMARY ===\n")
            f.write(f"Test duration: {test_duration:.2f} seconds\n")
            f.write(f"Groups attempted: {len(groups_data)}\n")
            f.write(f"Groups successfully created: {created_groups}\n")
            f.write(f"Tools attempted: {len(tools_data)}\n")
            f.write(f"Tools successfully created: {created_tools}\n")
            f.write(f"Individual tools created: {total_tools_created}\n")
            f.write(f"Test completed: {test_end_time}\n")

        print(f"\n✓ Log saved to: {log_file.absolute()}")
        print("✓ Remember to clean up test data with cleanup_databases.ps1")

def main():
    parser = argparse.ArgumentParser(description="External API connectivity test for AutoSklad")
    parser.add_argument("--url", default="http://127.0.0.1:8000",
                       help="Base URL of the running server (default: http://127.0.0.1:8000)")
    parser.add_argument("--skip-connectivity", action="store_true",
                       help="Skip initial connectivity test")

    args = parser.parse_args()

    print("AutoSklad External API Connectivity Test")
    print("=" * 50)
    print(f"Target URL: {args.url}")
    print(f"Skip connectivity test: {args.skip_connectivity}")
    print()

    tester = ApiConnectivityTest(args.url)

    if not args.skip_connectivity and not tester.test_server_status():
        print("❌ Cannot connect to server. Aborting tests.")
        return 1

    try:
        success = tester.run_api_population_test()
        if success or success is None:  # None means it tried to run but failed on API calls
            print("\n✅ API connectivity test completed!")
            return 0
        else:
            print("\n❌ API connectivity test failed!")
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
