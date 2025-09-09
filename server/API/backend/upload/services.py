# from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from DB.Engine.CRUD import BaseCRUD
from DB.Models.Group import Group
from DB.Models.ToolTypes import ToolTypes
from DB.Models.Tools import Tools


class EngineGroup(BaseCRUD[Group]):
    def __init__(self, db: Session):
        super().__init__(db, Group)

    def upsert(self, code: str, name: str, description: str) -> int:
        q = self.filter_by(id=code) if code else []
        if q:
            return q[0].id
        self.add(index=code, name=name, description=description)
        return self.filter_by(id=code)[0].id

class EngineToolTypes(BaseCRUD[ToolTypes]):
    def __init__(self, db: Session):
        super().__init__(db, ToolTypes)

    def upsert(self, name: str, description: str, img: str, groups_id: int) -> int:
        q = self.filter_by(name=name, groups_id=groups_id)
        if q:
            return q[0].id
        self.add(name=name, description=description, img=img, groups_id=groups_id, count=0)
        return self.filter_by(name=name, groups_id=groups_id)[0].id

class EngineTools(BaseCRUD[Tools]):
    def __init__(self, db: Session):
        super().__init__(db, Tools)

    def upsert(self, inv: str, tool_type_id: int):
        q = self.filter_by(inventory_number=inv)
        if q:
            self.update(q[0].id, tool_type_id=tool_type_id)
        else:
            self.add(inventory_number=inv, tool_type_id=tool_type_id)
