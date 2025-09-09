import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, Index
from DB.Data.base import Base
from DB.Models.BaseModel import Model


# if 'DropOperations' not in Base.metadata.tables:
#     from DB.Models.DropOperations import DropOperations
# if 'LoadOperations' not in Base.metadata.tables:
#     from DB.Models.LoadOperations import LoadOperations
# if 'OperationsConsumption' not in Base.metadata.tables:
#     from DB.Models.OperationsConsumption import OperationsConsumption
# if 'Cell' not in Base.metadata.tables:
#     from DB.Models.Cell import Cell

# print("Status")


class Status(Base, Model):
    """Модель для хранения статусов и их типов."""
    __tablename__ = 'Status'
    __table_kwargs__ = {"extend_existing": True}  # Указываем аргументы таблицы отдельно

    # Поля таблицы
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True, comment='Уникальный идентификатор статуса')
    stype = Column(String(100), nullable=False, unique=True, comment='Тип статуса (например, Active, Inactive, Pending и т.д.)')
    description = Column(String(255), nullable=True, comment='Описание статуса')
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False,
                        comment='Дата и время создания записи статуса')

    @property
    def drop_operations(self):
        if "DropOperations" not in Base.metadata.tables:
            from DB.Models.DropOperations import DropOperations
        else:
            DropOperations = Base.metadata.tables["DropOperations"].class_
            # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(DropOperations, back_populates='Status')

    @property
    def load_operations(self):
        if "LoadOperations" not in Base.metadata.tables:
            from DB.Models.LoadOperations import LoadOperations
        else:
            LoadOperations = Base.metadata.tables["LoadOperations"].class_
            # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(LoadOperations, back_populates='Status')

    @property
    def operations_consumptions(self):
        if 'OperationsConsumptions' not in Base.metadata.tables:
            from DB.Models.OperationsConsumption import OperationsConsumption
        else:
            OperationsConsumption = Base.metadata.tables['OperationsConsumptions'].class_
            # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(OperationsConsumption, back_populates='Status')

    @property
    def cells(self):
        if 'Cells' not in Base.metadata.tables:
            from DB.Models.Cell import Cell
        else:
            Cell = Base.metadata.tables['Cells'].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Cell, back_populates='Status')

    # Индексы
    __table_args__ = (
        Index('idx_type_status', 'stype', unique=False),
        Index('idx_created_at_status', 'created_at', unique=False),
    )

    def __repr__(self):
        """Представляет объект Status в виде строки для удобства отладки."""
        return (f"<Status("
                f"id={self.id}, "
                f"type={self.stype}, "
                f"description={self.description}, "
                f"created_at={self.created_at}"
                f")>")

# drop_operations = relationship('DropOperations', back_populates='Status')
# load_operations = relationship('LoadOperations', back_populates='Status')
# operations_consumption = relationship('OperationsConsumption', back_populates='Status')
# cells = relationship('Cell', back_populates='Status')
