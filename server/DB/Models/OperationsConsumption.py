import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from DB.Data.base import Base
from DB.Models.BaseModel import Model


# if "Consumption" not in Base.metadata.tables:
#     from DB.Models.Consumption import Consumption
# if "Status" not in Base.metadata.tables:
#     from DB.Models.Status import Status
# if "History" not in Base.metadata.tables:
#     from DB.Models.History import History
# if "Tools" not in Base.metadata.tables:
#     from DB.Models.Tools import Tools

#  print("OperationsConsumption")


class OperationsConsumption(Base, Model):
    """Модель для учета операций с расходом инструментов."""
    __tablename__ = "OperationsConsumption"
    __table_kwargs__ = {"extend_existing": True}  # Указываем аргументы таблицы отдельно

    # Поля таблицы
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True, comment="Уникальный идентификатор записи операции")
    date = Column(DateTime, default=datetime.datetime.utcnow, nullable=False,comment="Дата и время операции")
    description = Column(String(255), nullable=True, comment="Описание операции или дополнительные детали")
    consumption_id = Column(Integer, ForeignKey("Consumption.id"), nullable=False, comment="Идентификатор расхода из таблицы Consumption")
    history_id = Column(Integer, ForeignKey("History.id"), nullable=False, comment="Идентификатор записи из таблицы History")
    consumption_tools_id = Column(Integer, ForeignKey("Tools.id"), nullable=False, comment="Идентификатор инструмента из таблицы Tools")
    status_id = Column(Integer, ForeignKey("Status.id"), nullable=False, comment="Идентификатор статуса операции из таблицы Status")

    @property
    def status(self):
        if "Status" not in Base.metadata.tables:
            from DB.Models.Status import Status
        else:
            Status = Base.metadata.tables["Status"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Status, back_populates="OperationsConsumptions")
    
    @property
    def stories(self):
        if "Stories" not in Base.metadata.tables:
            from DB.Models.History import History
        else:
            History = Base.metadata.tables["Stories"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(History, back_populates="OperationsConsumptions")
    @property
    def consumptions(self):
        if "Consumptions" not in Base.metadata.tables:
            from DB.Models.Consumption import Consumption
        else:
            Consumption = Base.metadata.tables["Consumptions"].class_
            # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Consumption, back_populates="OperationsConsumptions")
    @property
    def tools(self):
        if "Tools" not in Base.metadata.tables:
            from DB.Models.Tools import Tools
        else:
            Tools = Base.metadata.tables["Tools"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Tools, back_populates="OperationsConsumptions")

    # Индексы
    __table_args__ = (
        Index("idx_consumption_id_tools_id", "consumption_id", "consumption_tools_id", unique=False),
        Index("idx_status_operations_consumption_id", "status_id", unique=False),
    )

    def __repr__(self):
        """Представляет объект OperationsConsumption в виде строки для удобства отладки."""
        return (f"<{self.__tablename__}("
                f"id={self.id}, "
                f"date={self.date}, "
                f"description={self.description}"
                f"consumption_id={self.consumption_id}, "
                f"history_id={self.history_id}, "
                f"consumption_tools_id={self.consumption_tools_id}, "
                f"status_id={self.status_id}, "
                f")>")
