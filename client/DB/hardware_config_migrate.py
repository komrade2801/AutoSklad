"""Миграция HardwareConfig: park_x/park_z → park_m1..park_m5."""

from sqlalchemy import inspect, text

from Core.app_logging import get_logger

logger = get_logger(__name__)

_LEGACY_PARK_MAP = (
    ("park_m1_default", "park_x_default"),
    ("park_m3_default", "park_z_default"),
    ("park_m5_default", "push_up_default"),
)


def migrate_hardware_config_park_motors(bind) -> None:
    """
    Добавляет park_m1_default..park_m5_default в существующую SQLite-БД
    и переносит значения из park_x_default / park_z_default при наличии.
    """
    insp = inspect(bind)
    if "HardwareConfig" not in insp.get_table_names():
        return

    existing = {c["name"] for c in insp.get_columns("HardwareConfig")}
    with bind.begin() as conn:
        for i in range(1, 6):
            col = f"park_m{i}_default"
            if col not in existing:
                conn.execute(
                    text(
                        f"ALTER TABLE HardwareConfig "
                        f"ADD COLUMN {col} INTEGER NOT NULL DEFAULT 0"
                    )
                )
                existing.add(col)
                logger.info("migrate HardwareConfig: added %s", col)

        for new_col, old_col in _LEGACY_PARK_MAP:
            if old_col in existing and new_col in existing:
                conn.execute(
                    text(
                        f"UPDATE HardwareConfig "
                        f"SET {new_col} = {old_col} "
                        f"WHERE {new_col} = 0 AND {old_col} != 0"
                    )
                )
