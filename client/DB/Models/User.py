"""
Этот модуль содержит определение класса TableUser, который представляет
таблицу "User" в базе данных. Класс предназначен для хранения информации
о пользователях системы, включая их роли, имена, фамилии и другие данные.
Обеспечивает связи с таблицами "Role" и "Identification" для организации
структуры данных.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, Index, PrimaryKeyConstraint
from sqlalchemy.orm import relationship
from DB.Data.base import Base
from DB.Models.BaseModel import Model


# print("User")


class User(Base, Model):
    __tablename__ = 'User'  # Имя таблицы User в базе данных
    __table_args__ = (
        # PrimaryKeyConstraint('id', 'barcode', 'code', 'role_id'),
        Index('id_user', 'id', unique=False),
        # Index('idx_user_code', 'code', unique=False),
        # Index('idx_user_barcode', 'barcode', unique=False),
        Index('fk_user_role_idx', 'role_id', unique=False),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)  #
    barcode = Column(Integer, nullable=False, unique=True)
    code = Column(Integer, nullable=False, unique=True)
    first_name = Column(String(50), nullable=True)
    password = Column(String(45), nullable=True)
    second_name = Column(String(50), nullable=True)
    family = Column(String(50), nullable=True)  # Исправлено название
    role_id = Column(Integer, ForeignKey('Role.id'), nullable=False)

    @property
    def roles(self):
        if 'Roles' not in Base.metadata.tables:
            from DB.Models.Role import Role
        else:
            Role = Base.metadata.tables['Roles'].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Role, back_populates='Users')

    @property
    def identifications(self):
        if 'Identifications' not in Base.metadata.tables:
            from DB.Models.Identification import Identification
        else:
            Identification = Base.metadata.tables['Identifications'].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Identification, back_populates='Users')

    @property
    def stories(self):
        if 'Stories' not in Base.metadata.tables:
            from DB.Models.History import History
        else:
            History = Base.metadata.tables['Stories'].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(History, back_populates='Users')

    def __repr__(self):
        """Представляет объект User в виде строки."""
        return (f"<User("
                f"id={self.id}, "
                f"barcode={self.barcode}, "
                f"code={self.code}, "
                f"first_name={self.first_name}, "
                f"password={self.password}, "
                f"second_name={self.second_name}, "
                f"family={self.family}, "
                f"role_id={self.role_id}"
                f">")

# # Связи
# roles = relationship('Role', back_populates='Users')  # Связь с таблицей Role
# identifications = relationship('Identification', back_populates='Users')  # Связь с таблицей Identification
# stories = relationship('History', back_populates='Users')  # Связь с таблицей History
