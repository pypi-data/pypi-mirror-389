from __future__ import annotations

from chromakitx import (Color, ColorType, TextStyle, AnsiColor)

class AnsiRenderer:
    def __init__(self) -> None:
        self._default_color: ColorType = AnsiColor.White

    def render_segment(self, text: str, color: ColorType | None, bold: bool) -> str:
        prefix: str = ""

        if bold:
            prefix += Color(TextStyle.BOLD)

        prefix += Color(color if color else self._default_color)
        return prefix + text + Color(TextStyle.RESET)
