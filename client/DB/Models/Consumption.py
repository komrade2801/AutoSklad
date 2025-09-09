from sqlalchemy import Column, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship
from DB.Data.base import Base
from DB.Models.BaseModel import Model


# if 'Tools' not in Base.metadata.tables:
#     from DB.Models.Tools import Tools

# print("Consumption")


class Consumption(Base, Model):
    """Модель для хранения информации о расходе инструментов."""
    __tablename__ = 'Consumption'
    __table_kwargs__ = {"extend_existing": True}  # Указываем аргументы таблицы отдельно

    # Поля таблицы
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False, comment='Уникальный идентификатор записи расхода')
    cell_id = Column(Integer, ForeignKey('Cell.id'), nullable=False, comment='Идентификатор ячейки')
    tools_id = Column(Integer, ForeignKey('Tools.id'), nullable=False, comment='Идентификатор инструмента')

    @property
    def tools(self):
        if 'Tools' not in Base.metadata.tables:
            from DB.Models.Tools import Tools
        else:
            Tools = Base.metadata.tables['Tools'].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Tools, back_populates='Consumptions')

    @property
    def cells(self):
        if 'Cells' not in Base.metadata.tables:
            from DB.Models.Cell import Cell
        else:
            Cell = Base.metadata.tables['Cells'].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Cell, back_populates='Consumptions')

    @property
    def operations_consumptions(self):
        if 'OperationsConsumptions' not in Base.metadata.tables:
            from DB.Models.OperationsConsumption import OperationsConsumption
        else:
            OperationsConsumption = Base.metadata.tables['OperationsConsumptions'].class_
            # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(OperationsConsumption, back_populates='Consumptions')

    # Индексы
    __table_args__ = (
        Index('idx_tools_id', 'tools_id', unique=False),
        Index('idx_cell_id', 'cell_id', unique=False),
    )

    def __repr__(self):
        """Представляет объект Consumption в виде строки для удобства отладки."""
        return (f"<Consumption("
                f"id={self.id}, "
                f"tools_id={self.tools_id}, "
                f"cell_id={self.cell_id}"
                f")>")

# cells = relationship('Cell', back_populates='Consumptions')
# operations_consumptions = relationship('OperationsConsumption', back_populates='Consumptions')
# tools = relationship('Tools', back_populates='Consumptions')
