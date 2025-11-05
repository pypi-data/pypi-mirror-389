from __future__ import annotations
from typing import Iterator
from re import (Pattern, Match, compile)

from inkline.token import (Token, TokenType)

class Tokenizer:
    COLOR_PATTERN: Pattern[str] = compile(pattern=r'\{(\d)}')

    def __init__(self, line: str) -> None:
        self._line: str = line
        self._pos: int = 0

    def __iter__(self) -> Iterator[Token]:
        return self

    def __next__(self) -> Token:
        if self._pos >= len(self._line):
            raise StopIteration

        match: Match[str] | None = self.COLOR_PATTERN.match(self._line, self._pos)

        if match:
            self._pos = match.end()
            return Token(TokenType.COLOR, match.group(1))

        char: str = self._line[self._pos]
        self._pos += 1

        match char:
            case ' ':
                return Token(TokenType.SPACE)

            case '\n':
                return Token(TokenType.NEWLINE)

            case _:
                return Token(TokenType.CHAR, char)

    def clone(self) -> Tokenizer:
        new_tokenizer: Tokenizer = Tokenizer(self._line)
        new_tokenizer._pos = self._pos

        return new_tokenizer

    def has_no_solid_tokens(self) -> bool:
        return not any(tok.is_solid() for tok in self.clone())

    def true_length(self) -> int:
        last_non_space: int = 0
        total:          int = 0

        for tok in self.clone():
            if tok.has_zero_width():
                continue

            total += 1

            if not tok.is_space():
                last_non_space = total

        return last_non_space

    def leading_spaces(self) -> int:
        count: int = 0

        for tok in self.clone():
            if tok.is_solid():
                break

            if tok.is_space():
                count += 1

        return count

    def truncate(self, start: int, end: int) -> Iterator[Token]:
        assert start <= end, "Start position must be <= end position"

        width:           int = end - start
        remaining_start: int = start

        for tok in self.clone():
            if tok.has_zero_width():
                yield tok
                continue

            if remaining_start > 0:
                remaining_start -= 1
                continue

            if width == 0:
                break

            width -= 1
            yield tok

    @property
    def line(self) -> str:
        return self._line

    @property
    def position(self) -> int:
        return self._pos

    def reset(self) -> None:
        self._pos = 0

    def seek(self, position: int) -> None:
        if position < 0 or position > len(self._line):
            raise ValueError("Invalid position: " + str(position))

        self._pos = position
