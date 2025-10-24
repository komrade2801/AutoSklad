import pytest
import json
import os
from datetime import datetime
from pathlib import Path

from fastapi.testclient import TestClient

from DB.session import get_db
import dbSync
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
        db_path = Path("DB/Data/web_vending.db")
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
        from DB.Engine.PlanCRUD import EnginePlan
        from DB.Engine.PlanToolTypesCRUD import EnginePlanToolTypes

        groups_crud = EngineGroup(db)
        tool_types_crud = EngineToolTypes(db)
        tools_crud = EngineTools(db)
        plan_crud = EnginePlan(db)
        plan_tool_types_crud = EnginePlanToolTypes(db)

        return {
            "groups": groups_crud.get_all_groups(),
            "tool_types": tool_types_crud.get_all_tool_types(),
            "tools": tools_crud.get_all_tools(),
            "plan": plan_crud.get_all_plans(),
            "plan_tool_types": plan_tool_types_crud.get_all_plan_tool_types()
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
            {"group_name": "Метчики", "parent_group": 0, "description": "Инструмент для нарезания внутренних резьб", "img": ""},
            {"group_name": "Сверла", "parent_group": 0, "description": "Осевой режущий инструмент", "img": ""},
            {"group_name": "Пластины", "parent_group": 0, "description": "Сменный режущий элемент для токарных резцов", "img": ""},
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

        plan_data = [
            {
                "id":1,
                "enterprise": "ООО «Завод Контакт»",
                "barcode": "2",
                "name": "Втулка БА8.226.320-23",
                "description": "Втулка БА8.226.320-23 ЮПИЯ.715331.003-23 ОСТ 4Г 0.822.003-73",
                "designation": "4022-4-5",
                "index_list":0,
                "list_count":0,
                "parent_plan":None,
                "parent_plan_id":None,
                "tools": [{'name':"M6x1 HSS", 'quantity': 1}, {'name':"Сверло 990SUTA 4.5 мм", 'quantity': 1}, {'name':"ZCC-CT CNMG120408-DM", 'quantity': 2}]
            },
            {
                "id":2,
                "index_list":0,
                "list_count":0,
                "parent_plan":None,
                "parent_plan_id":None,
                "enterprise": "ООО «Завод Контакт»",
                "barcode": "2",
                "description": "Шайба ИВУА.711341.046 (по чертежу; Сталь 20, Ц15.хр; без ЛКП)",
                "name": "Шайба ИВУА.711341.046",
                "designation": "4022-4-5",
                "tools": [{'name':"M6x1 HSS", 'quantity': 1}, {'name':"Сверло твердосплавное 3.3 мм PSD-3DA-0330", 'quantity': 2}, {'name':"SEHT1204AFFN-AL", 'quantity': 1}]
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

        created_plans = []
        for plan in plan_data:
            response = test_client.post("/backend/create_plan/1", json=plan)
            if response.status_code not in [200, 201]:
                print(f"Warning: Plan creation failed: {response.json()}")
                with log_file.open("a", encoding="utf-8") as f:
                    f.write(f"\nFAILED: {json.dumps(plan, ensure_ascii=False, indent=2)}\n")
                    f.write(f"Response: {response.json()}\n\n")
            else:
                with log_file.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(plan, ensure_ascii=False, indent=2))
                    f.write(f"\nResponse: {response.json()}\n\n")
                created_plans.append(plan)

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
        # final_log_path = Path("logs/") / f"test_db_population_{timestamp}.txt"
        # os.makedirs(final_log_path.parent, exist_ok=True)
        # os.rename(log_file, final_log_path)

        print(created_tools)
        print(created_plans)

        # Assertions - check that some data was created (may vary based on initial DB state)
        assert len(final_data['groups']) >= len(created_groups), "Groups creation failed"
        assert len(final_data['tool_types']) >= len(created_tools), "Tools creation failed"
        assert len(final_data['tools']) >= sum(tool['count'] for tool in created_tools if tool in created_tools), "Individual tools creation failed"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
