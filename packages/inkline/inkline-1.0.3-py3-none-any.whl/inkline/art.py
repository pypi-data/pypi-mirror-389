from __future__ import annotations
from typing import Iterator
from shutil import get_terminal_size
from re import (Pattern, Match, compile)

from chromakitx import ColorType

from inkline.token import TokenType
from inkline.tokenizer import Tokenizer
from inkline.renderer import AnsiRenderer
from inkline.info import (InfoConfig, InfoPosition)

class AsciiArt:
    def __init__(self, text: str | None = None, colors: list[ColorType] | None = None, bold: bool = False, info: InfoConfig | None = None) -> None:
        self._colors: list[ColorType] = colors if colors else []
        self._bold: bool = bold
        self._info: InfoConfig | None = info
        self._renderer: AnsiRenderer = AnsiRenderer()
        self._current_color: ColorType | None = None

        self._lines: list[str] = self._preprocess_lines(text) if text else []
        self._start: int
        self._end: int
        (self._start, self._end) = self._calculate_boundaries(self._lines)

    @staticmethod
    def _preprocess_lines(text: str) -> list[str]:
        lines: list[str] = [line for line in text.splitlines() if line.strip()]

        while lines and Tokenizer(lines[-1]).has_no_solid_tokens():
            lines.pop()

        return lines

    @staticmethod
    def _calculate_boundaries(lines: list[str]) -> tuple[int, int]:
        if not lines:
            return 0, 0

        start: float = float("inf")
        end: int = 0

        for line in lines:
            tokenizer: Tokenizer = Tokenizer(line)

            line_start: int = tokenizer.leading_spaces()
            line_end:   int = tokenizer.true_length()

            start: int = min(start, line_start)
            end:   int = max(end, line_end)

        if start == float("inf"):
            return 0, 0

        return int(start), int(end)

    def render_line(self, line: str) -> str:
        tokenizer: Tokenizer = Tokenizer(line)
        output: list[str] = []

        default_color: ColorType | None = self._colors[0] if self._colors else None
        current_color: ColorType | None = self._current_color if self._current_color is not None else default_color
        current_segment: list[str] = []

        for tok in tokenizer.truncate(self._start, self._end):
            if tok.type == TokenType.COLOR:
                if current_segment:
                    segment_text: str = "".join(current_segment)
                    styled:       str = self._renderer.render_segment(segment_text, current_color, self._bold)

                    output.append(styled)
                    current_segment.clear()

                color_idx: int = int(tok.value or 0)

                if color_idx < len(self._colors):
                    current_color = self._colors[color_idx]
                    self._current_color = current_color

            elif tok.type in (TokenType.CHAR, TokenType.SPACE):
                current_segment.append(tok.value or ' ')

        if current_segment:
            segment_text: str = "".join(current_segment)
            styled:       str = self._renderer.render_segment(segment_text, current_color, self._bold)

            output.append(styled)

        return "".join(output)

    def __iter__(self) -> Iterator[str]:
        if not self._info:
            for line in self._lines:
                yield self.render_line(line)

            return

        yield from self._render_with_info()

    def render(self) -> str:
        return "\n".join(self)

    @property
    def width(self) -> int:
        return self._end - self._start

    @property
    def height(self) -> int:
        return len(self._lines)

    @property
    def lines(self) -> list[str]:
        return self._lines.copy()

    @property
    def colors(self) -> list[ColorType]:
        return self._colors.copy()

    @property
    def bold(self) -> bool:
        return self._bold

    def set_colors(self, colors: list[ColorType]) -> None:
        self._colors = colors

    def set_bold(self, bold: bool) -> None:
        self._bold = bold

    def _render_with_info(self) -> Iterator[str]:
        info_lines: list[str] = self._info.lines if self._info else []
        art_lines:  list[str] = [self.render_line(line) for line in self._lines]

        if not self._info:
            yield from art_lines
            return

        term_width: int = get_terminal_size().columns
        position: InfoPosition = self._info.position

        match position:
            case InfoPosition.TOP:
                yield from info_lines
                yield from art_lines

            case InfoPosition.BOTTOM:
                yield from art_lines
                yield from info_lines

            case InfoPosition.RIGHT:
                max_art_width: int = max((len(self._strip_ansi(line)) for line in art_lines), default=0)
                has_art: bool = bool(art_lines)

                margin_spaces: str = (" " * self._info.margin) if has_art else ""
                max_len: int = max(len(art_lines), len(info_lines))

                for i in range(max_len):
                    art_line:  str = art_lines[i] if i < len(art_lines) else ""
                    info_line: str = info_lines[i] if i < len(info_lines) else ""

                    art_visible_len: int = len(self._strip_ansi(art_line))
                    margin_needed:  int = max_art_width - art_visible_len

                    combined: str = art_line + (" " * margin_needed) + margin_spaces + info_line

                    if len(self._strip_ansi(combined)) > term_width:
                        combined = self._truncate_line(combined, term_width)

                    yield combined

            case InfoPosition.LEFT:
                max_info_width: int = max((len(self._strip_ansi(line)) for line in info_lines), default=0)
                margin_spaces: str = " " * self._info.margin

                max_len: int = max(len(art_lines), len(info_lines))

                for i in range(max_len):
                    info_line: str = info_lines[i] if i < len(info_lines) else ""
                    art_line:  str = art_lines[i] if i < len(art_lines) else ""

                    info_visible_len: int = len(self._strip_ansi(info_line))
                    margin_needed:   int = max_info_width - info_visible_len

                    combined: str = info_line + (" " * margin_needed) + margin_spaces + art_line

                    if len(self._strip_ansi(combined)) > term_width:
                        combined = self._truncate_line(combined, term_width)

                    yield combined

    @staticmethod
    def _strip_ansi(text: str) -> str:
        ansi_escape: Pattern[str] = compile(pattern=r'\x1b\[[0-9;]*m')
        return ansi_escape.sub(repl='', string=text)

    @staticmethod
    def _truncate_line(line: str, max_width: int) -> str:
        ansi_escape: Pattern[str] = compile(pattern=r'\x1b\[[0-9;]*m')

        visible_len: int = 0
        result: list[str] = []
        pos: int = 0

        while (pos < len(line)) and (visible_len < max_width):
            match: Match[str] | None = ansi_escape.match(line, pos)

            if match:
                result.append(match.group(0))
                pos = match.end()

                continue

            result.append(line[pos])
            visible_len += 1
            pos += 1

        return ''.join(result)
