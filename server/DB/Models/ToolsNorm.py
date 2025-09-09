from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from DB.Data.base import Base
from DB.Models.BaseModel import Model


class ToolsNorm(Base, Model):
    __tablename__ = "ToolsNorm"
    __table_kwargs__ = {"extend_existing": True}
    __table_args__ = (
        Index("fk_ToolsNorm_Tools1_idx", "tools_id"),
        Index("fk_ToolsNorm_ActualNorm1_idx", "actual_norm_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    summa = Column(Integer, nullable=True)
    summa_of_periods = Column(Integer, nullable=True)
    description = Column(String(450), nullable=True)
    type_periods = Column(String(45), nullable=True)
    summa_of_use = Column(String(45), nullable=True)
    start_date = Column(DateTime, nullable=True)
    tools_id = Column(Integer, ForeignKey("Tools.id"), nullable=False)
    actual_norm_id = Column(Integer, ForeignKey("ActualNorm.id"), nullable=False)  # ранее ActualNorm_id, теперь Quota_id

    @property
    def ActualNorm(self):
        # Отложенный импорт модели ActualNorm
        from DB.Models.ActualNorm import ActualNorm
        return relationship(ActualNorm, back_populates="ToolsNorm")

    @property
    def Tools(self):
        # Отложенный импорт модели Tools
        from DB.Models.Tools import Tools
        return relationship(Tools, back_populates="ToolsNorm")

    def __repr__(self):
        return (f"<{self.__tablename__}("
                f"id={self.id}, "
                f"summa={self.summa}, "
                f"summa_of_periods={self.summa_of_periods}, "
                f"description={self.description}"
                f"type_periods={self.type_periods}, "
                f"summa_of_use={self.summa_of_use}, "
                f"start_date={self.start_date}, "
                f"tools_id={self.tools_id}, "
                f"actual_norm_id={self.actual_norm_id}, "
                f")>")
