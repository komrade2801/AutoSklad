import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from DB.Data.base import Base
from DB.Models.BaseModel import Model


class DropOperations(Base, Model):
    """Модель для учета операций по выдаче инструментов (Drop Operations)."""
    __tablename__ = "DropOperations"
    __table_kwargs__ = {"extend_existing": True}  # Указываем аргументы таблицы отдельно

    # Поля таблицы
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True, comment="Уникальный идентификатор записи операции Drop")
    date = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, comment="Дата и время выполнения операции")
    description = Column(String(255), nullable=True, comment="Описание операции или дополнительные детали")
    history_id = Column(Integer, ForeignKey("History.id"), nullable=True, comment="Внешний ключ на таблицу History")
    status_id = Column(Integer, ForeignKey("Status.id"), nullable=False, comment="Внешний ключ на таблицу Status")
    tools_id = Column(Integer, ForeignKey("ToolTypes.id"), nullable=False, comment="Внешний ключ на таблицу ToolTypes")
    drop_id = Column(Integer, ForeignKey("Drop.id"), nullable=False, comment="Внешний ключ на таблицу Drop")

    @property
    def drops(self):
        if "Drops" not in Base.metadata.tables:
            from DB.Models.Drop import Drop
        else:
            Drop = Base.metadata.tables["Drops"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Drop, back_populates="DropOperations")

    @property
    def tools(self):
        if "ToolTypes" not in Base.metadata.tables:
            from DB.Models.ToolTypes import ToolTypes
        else:
            ToolTypes = Base.metadata.tables["ToolTypes"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(ToolTypes, back_populates="DropOperations")

    @property
    def status(self):
        if "Status" not in Base.metadata.tables:
            from DB.Models.Status import Status
        else:
            Status = Base.metadata.tables["Status"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Status, back_populates="DropOperations")

    @property
    def stories(self):
        if "Stories" not in Base.metadata.tables:
            from DB.Models.History import History
        else:
            History = Base.metadata.tables["Stories"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(History, back_populates="DropOperations")

    # Индексы
    __table_args__ = (
        Index("idx_drop_operations_drop_id_tools_id", "drop_id", "tools_id", unique=False),
        Index("idx_drop_operations_status_id", "status_id", unique=False),
        Index("idx_drop_operations_history_id", "history_id", unique=False),
    )

    def __repr__(self):
        """Представляет объект DropOperations в виде строки для удобства отладки."""
        return (f"<DropOperations("
                f"id={self.id}, "
                f"date={self.date}, "
                f"description={self.description}, "
                f"history_id={self.history_id}, "
                f"status_id={self.status_id}, "
                f"tools_id={self.tools_id}, "
                f"drop_id={self.drop_id}"
                f")>")
