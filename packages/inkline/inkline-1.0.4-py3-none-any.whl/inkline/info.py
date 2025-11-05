from __future__ import annotations
from enum import IntEnum
from dataclasses import dataclass

class InfoPosition(IntEnum):
    TOP    = 0
    RIGHT  = 1
    LEFT   = 2
    BOTTOM = 3

@dataclass
class InfoConfig:
    lines: list[str]
    position: InfoPosition = InfoPosition.RIGHT
    margin: int = 4
