from __future__ import annotations

from dataclasses import dataclass
from enum import (StrEnum, auto)

class TokenType(StrEnum):
    CHAR    = auto()
    SPACE   = auto()
    COLOR   = auto()
    NEWLINE = auto()

@dataclass(frozen=True)
class Token:
    type: TokenType
    value: str | None = None

    def is_solid(self) -> bool:
        return self.type == TokenType.CHAR

    def is_space(self) -> bool:
        return self.type == TokenType.SPACE

    def is_newline(self) -> bool:
        return self.type == TokenType.NEWLINE

    def has_zero_width(self) -> bool:
        return self.type == TokenType.COLOR
