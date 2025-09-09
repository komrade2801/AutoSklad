

from pathlib import Path

folder_path = Path("../DB/Engine")

# Все файлы в папке (без подпапок)
files = [file.name for file in folder_path.iterdir() if file.is_file()]

# Рекурсивный поиск всех файлов
all_files = [str(file) for file in folder_path.rglob("*") if file.is_file()]
print(all_files)


# Cell
# Cell_has_Device
# Command
# Consumption
# Device
# Drop
# DropOperations
# dropOperations_has_Device
# Error
# Error_has_Device
# Group
# Help
# History
# Identification
# Load
# LoadOperations
# loadOperations_has_Device
# MassDrop
# MassLoad
# mass_drop_has_Device
# mass_load_has_Device
# OperationsConsumption
# OperationsConsumption_has_Device
# Plan
# Quota
# Quota_has_Device
# Rights
# Role
# Status
# ToolLocation
# Tools
# Tools_has_Device
# ToolType
# Type
# User

