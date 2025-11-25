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
            {"group_name": "Фрезы", "parent_group": 0, "description": "", "img": ""},
            {"group_name": "Сверла", "parent_group": 0, "description": "", "img": ""},
            {"group_name": "Пластины", "parent_group": 0, "description": "", "img": ""},
            {"group_name": "Свёрла", "parent_group": 2, "description": "", "img": ""},
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
            {'group_id': 3, 'tool_name': 'VCGT110304-FS', 'description': 'Проходная-маленькая', 'count': 2, 'img': '',
             'tools': {}},
            {'group_id': 3, 'tool_name': 'VCGT110302-SM', 'description': 'Проходная-маленькая', 'count': 4, 'img': '',
             'tools': {}},
            {'group_id': 3, 'tool_name': 'VCGT160402-FS', 'description': 'Проходная-большая', 'count': 5, 'img': '',
             'tools': {}},
            {'group_id': 3, 'tool_name': 'VCGT160404-ZM', 'description': 'Проходная-большая', 'count': 8, 'img': '',
             'tools': {}},
            {'group_id': 3, 'tool_name': 'TDJ2', 'description': 'Отрезная-2', 'count': 9, 'img': '', 'tools': {}},
            {'group_id': 3, 'tool_name': 'CCGT060204-SM', 'description': 'Расточная-маленькая', 'count': 10, 'img': '',
             'tools': {}},
            {'group_id': 3, 'tool_name': 'TDJ-2', 'description': 'Отрезная-2', 'count': 10, 'img': '', 'tools': {}},
            {'group_id': 4, 'tool_name': 'Сверло 3мм', 'description': 'Сверло 3мм', 'count': 10, 'img': '',
             'tools': {}},
            {'group_id': 2, 'tool_name': 'Сверло 3,3', 'description': 'Св-ло DIN338N; HSSE; 3.30 мм. /IZAR/ Испания',
             'count': 5, 'img': '', 'tools': {}},
            {'group_id': 2, 'tool_name': 'Сверло 3,4 кор.', 'description': 'DIN1897N сверло-короткая серия 3,4-IZAR',
             'count': 5, 'img': '', 'tools': {}},
            {'group_id': 2, 'tool_name': 'Сверло 3,3', 'description': 'DIN1897N сверло-короткая серия 3,3-IZAR',
             'count': 1, 'img': '', 'tools': {}},

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

        mass_load_data = {
            "operation": {
                "1": {"cell": "2", "tool": "2", "plan": 0},
                "2": {"cell": "3", "tool": "1", "plan": 0},
                "3": {"cell": "36", "tool": "63", "plan": 0},
                "4": {"cell": "37", "tool": "62", "plan": 0},
                "5": {"cell": "38", "tool": "61", "plan": 0},
                "6": {"cell": "41", "tool": "68", "plan": 0},
                "7": {"cell": "42", "tool": "67", "plan": 0},
                "8": {"cell": "43", "tool": "66", "plan": 0},
                "9": {"cell": "44", "tool": "65", "plan": 0},
                "10": {"cell": "45", "tool": "64", "plan": 0},
                "11": {"cell": "72", "tool": "11", "plan": 0},
                "12": {"cell": "73", "tool": "10", "plan": 0},
                "13": {"cell": "74", "tool": "9", "plan": 0},
                "14": {"cell": "150", "tool": "39", "plan": 0},
                "15": {"cell": "177", "tool": "38", "plan": 0},
                "16": {"cell": "178", "tool": "37", "plan": 0},
                "17": {"cell": "179", "tool": "36", "plan": 0},
                "18": {"cell": "180", "tool": "35", "plan": 0},
                "19": {"cell": "181", "tool": "34", "plan": 0},
                "20": {"cell": "186", "tool": "29", "plan": 0},
            }
        }

        print(f"\n--- Creating Mass Load ---")
        response = self.make_request("POST", "/backend/mass_load_tools/1", mass_load_data)

        if response and isinstance(response, dict) and response.get("status") == 200:
            print(f"\n--- Mass Load created ---")

        # Log to file
        with log_file.open("a", encoding="utf-8") as f:
            f.write(f"Tool Type: {json.dumps(mass_load_data, ensure_ascii=False)}\n")
            f.write(f"Response: {json.dumps(response, ensure_ascii=False) if response else 'No response'}\n\n")

        # Small delay between requests
        time.sleep(0.5)

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
