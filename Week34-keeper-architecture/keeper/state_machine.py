from enum import Enum, auto

class KeeperState(Enum):
    IDLE = auto()
    SCANNING = auto()
    OPPORTUNITY_FOUND = auto()
    EXECUTING = auto()
    CONFIRMING = auto()
    FAILED = auto()
    COOLDOWN = auto()       # after a failed tx, wait before retrying
    SHUTTING_DOWN = auto()
