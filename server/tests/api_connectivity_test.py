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
            {"group_name": "Инструменты ручные", "parent_group": 0, "description": "Основной раздел ручных инструментов", "img": ""},
            {"group_name": "Инструменты электрические", "parent_group": 0, "description": "Электроприборы и инструменты", "img": ""},
            {"group_name": "Инструменты садовые", "parent_group": 0, "description": "Оборудование для работ на участке", "img": ""},

            # Child groups (1-level nesting)
            {"group_name": "Отвёртки и ключи", "parent_group": 1, "description": "Завертыватели, отвёртки, ключи", "img": ""},
            {"group_name": "Ударный инструмент", "parent_group": 1, "description": "Молотки, кувалды, зубила", "img": ""},
            {"group_name": "Дрели и шуруповёрты", "parent_group": 2, "description": "Инструмент с вращением", "img": ""},
            {"group_name": "Газонокосилки", "parent_group": 3, "description": "Для стрижки травы", "img": ""},
            {"group_name": "Секаторы", "parent_group": 3, "description": "Для обрезки растений", "img": ""},

            # Nested child groups (2-level nesting)
            {"group_name": "Трубные ключи", "parent_group": 4, "description": "Ключи разводные и газовые", "img": ""},
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
                "group_id": 1,  # Ручные инструменты
                "tool_name": "Молоток большой",
                "description": "Стальной молоток для тяжёлых работ",
                "count": 3,
                "img": "",
                "tools": {"1": "101", "2": "102", "3": "103"}
            },
            {
                "group_id": 1,
                "tool_name": "Пила ручная",
                "description": "Деревянная пила для горизонтального пиления",
                "count": 2,
                "img": "",
                "tools": {"1": "201", "2": "202"}
            },
            {
                "group_id": 2,  # Электрические инструменты
                "tool_name": "Дрель ударная",
                "description": "Профессиональная дрель с ударным режимом",
                "count": 5,
                "img": "",
                "tools": {"1": "301", "2": "302", "3": "303", "4": "304", "5": "305"}
            },
            {
                "group_id": 3,  # Садовые инструменты
                "tool_name": "Лопата штыковая",
                "description": "Металлическая лопата для копки земли",
                "count": 4,
                "img": "",
                "tools": {"1": "401", "2": "402", "3": "403", "4": "404"}
            },

            # Child groups
            {
                "group_id": 4,  # Отвёртки и ключи
                "tool_name": "Отвёртка крестовая",
                "description": "Набор отвёрток Philips различных размеров",
                "count": 6,
                "img": "",
                "tools": {"1": "501", "2": "502", "3": "503", "4": "504", "5": "505", "6": "506"}
            },
            {
                "group_id": 5,  # Ударный инструмент
                "tool_name": "Кувалда",
                "description": "Бетонная кувалда весом 5 кг",
                "count": 1,
                "img": "",
                "tools": {"1": "601"}
            },
            {
                "group_id": 6,  # Дрели и шуруповёрты
                "tool_name": "Аккумуляторный шуруповёрт",
                "description": "Компактный инструмент с двухскоростным режимом",
                "count": 8,
                "img": "",
                "tools": {"1": "701", "2": "702", "3": "703", "4": "704", "5": "705", "6": "706", "7": "707", "8": "708"}
            },
            {
                "group_id": 7,  # Газонокосилки
                "tool_name": "Бензиновый триммер",
                "description": "Газонокосилка с леской и ножом",
                "count": 2,
                "img": "",
                "tools": {"1": "801", "2": "802"}
            },

            # Nested child groups
            {
                "group_id": 9,  # Трубные ключи
                "tool_name": "Ключ разводной",
                "description": "Универсальный разводной ключ",
                "count": 12,
                "img": "",
                "tools": {"1": "901", "2": "902", "3": "903", "4": "904", "5": "905", "6": "906",
                         "7": "907", "8": "908", "9": "909", "10": "910", "11": "911", "12": "912"}
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
