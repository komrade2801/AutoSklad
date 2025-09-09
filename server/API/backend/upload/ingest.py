# ingest.py
from sqlalchemy.exc import SQLAlchemyError

from API.backend.upload.mappers import normalize_record
from DB.Engine.GroupCRUD import EngineGroup
from DB.Engine.ToolTypesCRUD import EngineToolTypes
from DB.Engine.ToolsCRUD import EngineTools


def process_records(records: list[dict], db_session, required: list[str]):
    """
    Для каждого rec:
      1. normalize_record(rec)
      2. upsert группы
      3. upsert типов
      4. upsert инструментов
    Всё в рамках одной сессии, но по‑записи — чтобы не потерять данные при ошибке в одной из.
    """

    grp_engine  = EngineGroup()
    tp_engine   = EngineToolTypes()
    t_engine    = EngineTools()

    results = {"success": 0, "failed": []}

    for idx, rec in enumerate(records, start=1):
        try:
            norm = normalize_record(rec, required)
            # 1) группа
            grp = None
            grp_name = norm["group_code"]
            if grp_name is not None:
                grp_list = grp_engine.filter_by(name=str(grp_name))
                if grp_list:
                    grp = grp_list[0]
                else:
                    grp_engine.add(name=str(grp_name))
                    grp = grp_engine.filter_by(name=str(grp_name))[0]
            # 2) тип
            tt_list = tp_engine.filter_by(name=norm["short_name"])
            if tt_list:
                tt = tt_list[0]
            else:
                tp_engine.add(
                  name=norm["short_name"],
                  description=norm.get("description") or "",
                  groups_id=grp.id if grp else None
                )
                tt = tp_engine.filter_by(name=norm["short_name"])[0]
            # 3) инструмент
            inv = norm["code"]
            ex = t_engine.filter_by(inventory_number=inv)
            if ex:
                t_engine.update(ex[0].id, tool_type_id=tt.id)
            else:
                t_engine.add(
                  inventory_number=inv,
                  tool_type_id=tt.id,
                  plan_id=None
                )
            results["success"] += 1

        except (ValueError, SQLAlchemyError) as e:
            results["failed"].append({"row": idx, "error": str(e)})

    return results
