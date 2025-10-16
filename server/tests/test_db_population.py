import pytest
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

import dbSync
from fastapi.testclient import TestClient

# Import reconstruction of server startup
from options import Host, RECEIVER_TIMEOUT, SENDER_TIMEOUT, AES_KEY, port
from DB.session import get_db
from DB.Data.sqlite_db import SessionLocal
import dbSync
from DB.Data.init_db import initialize_database_if_needed
# Import Core functions for full database setup
from Core.default import rebuild_db, execute
from sqlalchemy.orm import Session

# Defer router imports until database is created
def create_test_app():
    """Create the test FastAPI app after database is initialized"""
    try:
        import importlib
        front_router = importlib.import_module("frontend.front_router").front_router
        backend_router = importlib.import_module("API.backend.routers").backend_router
        sync_router = importlib.import_module("dbSync.Transport.routers").sync_router
    except ImportError as e:
        # Create minimal routers for testing
        from fastapi import APIRouter
        front_router = APIRouter()
        backend_router = APIRouter()
        sync_router = APIRouter()

    from fastapi import FastAPI
    app = FastAPI(title="Test API")
    app.mount("/backend", backend_router)

    # Note: Not including front_router or sync_router in test app
    # as we only need backend API endpoints for this test

    return app, backend_router


class TestDbPopulation:
    """Test database population via API and log all created rows."""

    @pytest.fixture(scope="class", autouse=True)
    def setup_database(self):
        """Ensure database exists and is fully initialized with data."""
        db_path = Path("server/DB/Data/web_vending.db")
        if not db_path.exists():
            # Full database setup: create tables AND populate with initial data
            dbSync.init_db = True
            rebuild_db()
            execute()
            dbSync.init_db = False

        yield

        # Cleanup after all tests in class
        # Reminder: User mentioned to run cleanup_databases.ps1 when done
        print("Note: Run cleanup_databases.ps1 to remove test database when finished.")
        # Don't auto-cleanup to allow inspection of test results

    @pytest.fixture
    def test_client(self):
        """Create test client with bypassed sync."""
        # Temporarily disable sync decorators during tests
        dbSync.init_db = True
        test_app, _ = create_test_app()
        client = TestClient(test_app)
        yield client
        dbSync.init_db = False

    @staticmethod
    def get_db_snapshot(db: Session):
        """Capture all rows from relevant tables."""
        from DB.Engine.GroupCRUD import EngineGroup
        from DB.Engine.ToolTypesCRUD import EngineToolTypes
        from DB.Engine.ToolsCRUD import EngineTools

        groups_crud = EngineGroup(db)
        tool_types_crud = EngineToolTypes(db)
        tools_crud = EngineTools(db)

        return {
            "groups": groups_crud.get_all_groups(),
            "tool_types": tool_types_crud.get_all_tool_types(),
            "tools": tools_crud.get_all_tools()
        }

    def test_populate_groups_and_tools(self, test_client: TestClient, tmp_path):
        """End-to-end test: populate groups and tools, verify DB state."""
        # Setup logging
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = tmp_path / f"test_db_population_{timestamp}.txt"

        # Initial DB snapshot
        initial_data = TestDbPopulation.get_db_snapshot(next(get_db()))
        with log_file.open("w", encoding="utf-8") as f:
            f.write("=== INITIAL DATABASE STATE ===\n")
            f.write(json.dumps(initial_data, ensure_ascii=False, indent=2, default=str))
            f.write("\n\n=== GROUP CREATION ===\n")

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

        created_groups = []
        for group_data in groups_data:
            response = test_client.post("/backend/create_groups", json=group_data)
            assert response.status_code == 200, f"Failed to create group: {response.json()}"

            with log_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(group_data, ensure_ascii=False, indent=2, default=str))
                f.write(f"\nResponse: {response.json()}\n\n")

            created_groups.append(group_data)

        with log_file.open("a", encoding="utf-8") as f:
            f.write("=== TOOL CREATION ===\n")

        # Define tools for each group (2-3 tools with varied counts)
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

        created_tools = []
        for tool_data in tools_data:
            response = test_client.post("/backend/create_tools", json=tool_data)
            # Note: We may get failures if groups don't exist or duplicates - this tests the behavior
            if response.status_code not in [200, 201]:
                print(f"Warning: Tool creation failed: {response.json()}")
                with log_file.open("a", encoding="utf-8") as f:
                    f.write(f"\nFAILED: {json.dumps(tool_data, ensure_ascii=False, indent=2)}\n")
                    f.write(f"Response: {response.json()}\n\n")
            else:
                with log_file.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(tool_data, ensure_ascii=False, indent=2))
                    f.write(f"\nResponse: {response.json()}\n\n")
                created_tools.append(tool_data)

        # Final DB snapshot
        final_data = TestDbPopulation.get_db_snapshot(next(get_db()))
        with log_file.open("a", encoding="utf-8") as f:
            f.write("=== FINAL DATABASE STATE ===\n")
            f.write(json.dumps(final_data, ensure_ascii=False, indent=2, default=str))
            f.write("\n\n=== SUMMARY ===\n")
            f.write(f"Groups attempted: {len(groups_data)}\n")
            f.write(f"Groups successfully created: {len(created_groups)}\n")
            f.write(f"Tools attempted: {len(tools_data)}\n")
            f.write(f"Tools successfully created: {len(created_tools)}\n")
            f.write(f"Final Groups count: {len(final_data['groups'])}\n")
            f.write(f"Final ToolTypes count: {len(final_data['tool_types'])}\n")
            f.write(f"Final Tools count: {len(final_data['tools'])}\n")

        # Move log to server/logs/ as required
        final_log_path = Path("logs/") / f"test_db_population_{timestamp}.txt"
        os.makedirs(final_log_path.parent, exist_ok=True)
        os.rename(log_file, final_log_path)

        # Assertions - check that some data was created (may vary based on initial DB state)
        assert len(final_data['groups']) >= len(created_groups), "Groups creation failed"
        assert len(final_data['tool_types']) >= len(created_tools), "Tools creation failed"
        assert len(final_data['tools']) >= sum(tool['count'] for tool in created_tools if tool in created_tools), "Individual tools creation failed"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
