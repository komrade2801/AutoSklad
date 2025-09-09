import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from DB.Data.base import Base
from DB.Models.BaseModel import Model


class LoadOperations(Base, Model):
    """Модель для учета операций загрузки инструментов."""
    __tablename__ = "LoadOperations"
    __table_kwargs__ = {"extend_existing": True}  # Указываем аргументы таблицы отдельно

    # Поля таблицы
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True, comment="Уникальный идентификатор операции загрузки")
    date = Column(DateTime, default=datetime.datetime.utcnow, nullable=False,comment="Дата и время выполнения операции загрузки")
    description = Column(String(255), nullable=True, comment="Описание операции или дополнительные детали")
    load_id = Column(Integer, ForeignKey("Load.id"), nullable=False,comment="Идентификатор записи загрузки из таблицы Load")
    load_tools_id = Column(Integer, ForeignKey("Tools.id"), nullable=False,comment="Идентификатор инструмента из таблицы Tools")
    status_id = Column(Integer, ForeignKey("Status.id"), nullable=False,comment="Идентификатор статуса операции из таблицы Status")
    history_id = Column(Integer, ForeignKey("History.id"), nullable=True,comment="Идентификатор записи истории из таблицы History")

    @property
    def status(self):
        if "Status" not in Base.metadata.tables:
            from DB.Models.Status import Status
        else:
            Status = Base.metadata.tables["Status"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Status, back_populates="LoadOperations")

    @property
    def tools(self):
        if "Tools" not in Base.metadata.tables:
            from DB.Models.Tools import Tools
        else:
            Tools = Base.metadata.tables["Tools"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Tools, back_populates="LoadOperations")

    @property
    def stories(self):
        if "Stories" not in Base.metadata.tables:
            from DB.Models.History import History
        else:
            History = Base.metadata.tables["Stories"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(History, back_populates="LoadOperations")

    @property
    def loads(self):
        if "Loads" not in Base.metadata.tables:
            from DB.Models.Load import Load
        else:
            Load = Base.metadata.tables["Loads"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Load, back_populates="LoadOperations")

    # Индексы
    __table_args__ = (
        Index("idx_load_id_tools_id", "load_id", "load_tools_id", unique=False),
        Index("idx_status_id", "status_id", unique=False),
        Index("idx_history_id", "history_id", unique=False),
    )

    def __repr__(self):
        """Представляет объект LoadOperations в виде строки для удобства отладки."""
        return (f"<{self.__tablename__}("
                f"id={self.id}, "
                f"date={self.date}, "
                f"description={self.description}, "
                f"load_id={self.load_id}, "
                f"load_tools_id={self.load_tools_id}, "
                f"status_id={self.status_id}, "
                f"history_id={self.history_id}"
                f")>")
