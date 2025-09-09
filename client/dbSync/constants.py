# dbSync/constants.py
from enum import Enum

class CommandStatusEnum(str, Enum):
    PENDING        = "PENDING"
    IN_PROGRESS    = "IN_PROGRESS"
    COMPLETED      = "COMPLETED"
    FAILED         = "FAILED"

    @classmethod
    def values(cls):
        return [e.value for e in cls]
