import datetime
from sqlalchemy import Column, Integer, String, DateTime, Index
from sqlalchemy.orm import relationship
from DB.Data.base import Base
from DB.Models.BaseModel import Model


# print("MassDrop")


class MassDrop(Base, Model):
    """Модель для управления массовым удалением данных из системы."""
    __tablename__ = 'MassDrop'
    __table_kwargs__ = {"extend_existing": True}  # Указываем аргументы таблицы отдельно

    # Поля таблицы
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True, comment='Уникальный идентификатор задачи массового удаления')
    description = Column(String(255), nullable=True, comment='Описание задачи массового удаления')
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, comment='Дата и время создания задачи массового удаления')

    @property
    def drops(self):
        if "Drops" not in Base.metadata.tables:
            from DB.Models.Drop import Drop
        else:
            Drop = Base.metadata.tables["Drops"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Drop, back_populates='MassDrops')

    # Индексы
    __table_args__ = (
        Index('idx_created_at', 'created_at', unique=False),
    )

    def __repr__(self):
        """Представляет объект MassDrop в виде строки для удобства отладки."""
        return (f"<MassDrop("
                f"id={self.id}, "
                f"description={self.description},"
                f"created_at={self.created_at}"
                f")>")
