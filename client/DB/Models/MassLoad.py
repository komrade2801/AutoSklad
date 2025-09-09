from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Index
from sqlalchemy.orm import relationship
from DB.Data.base import Base
from DB.Models.BaseModel import Model


# print("MassLoad")


class MassLoad(Base, Model):
    """Модель для управления массовой загрузкой данных в систему."""
    __tablename__ = 'MassLoad'
    __table_kwargs__ = {"extend_existing": True}  # Указываем аргументы таблицы отдельно

    # Поля таблицы
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True, comment='Уникальный идентификатор загрузки (первичный ключ)')
    description = Column(String(255), nullable=True, comment='Описание задачи массовой загрузки')
    created_at = Column(DateTime, default=datetime.utcnow, nullable=True,
                        comment='Дата и время создания задачи массовой загрузки')

    @property
    def loads(self):
        if 'Loads' not in Base.metadata.tables:
            from DB.Models.Load import Load
        else:
            Load = Base.metadata.tables['Loads'].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Load, back_populates='MassLoads')

    # Индексы
    __table_args__ = (
        Index('idx_created_at_MassLoad', 'created_at', unique=False),
    )

    def __repr__(self):
        """Представляет объект MassLoad в виде строки для удобства отладки."""
        return (f"<MassLoad("
                f"id={self.id}, "
                f"description={self.description}, "
                f"created_at={self.created_at}"
                f")>")

# Help                            Help
# Error                           Error
# Role                            Role
# Plan                            Plan
# Group                           Group
# Rights                          Rights
# mass_drop                       MassDrop
# mass_load                       MassLoad
# Status                          Status
# User                            User
# Identification                  Identification
# Tools                           Tools
# Cell                            Cell
# Load                            load
# Drop                            Drop
# Consumption                     Consumption
# History                         History
# dropOperations                  DropOperations
# OperationsConsumption           OperationsConsumption
# loadOperations                  loadOperations
