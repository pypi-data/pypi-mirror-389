from __future__ import annotations
from typing import Any

from nervels.document import NLSDocument
from nervels.nodes import ColorNode
from nervels.utils import build_color

from chromakitx import ColorType

class NLSCompiler:
    def __init__(self, document: NLSDocument) -> None:
        self.document: NLSDocument = document

    def compile(self) -> tuple[str, str, list[ColorType], ColorType, ColorType]:
        large_logo: str = "\n".join(self.document.get_section("large"))
        small_logo: str = "\n".join(self.document.get_section("small"))
        colors: list[str] = self.document.get_section("colors")

        title_color: str = self._get_property_value(key="title", default="AnsiColor.White")
        keys_color:  str = self._get_property_value(key="keys", default="AnsiColor.White")

        return large_logo, small_logo, build_color(colors), build_color(title_color), build_color(keys_color)

    def _get_property_value(self, key: str, default: str) -> str:
        value: Any = self.document.get_property(key)
        return value.value if isinstance(value, ColorNode) else (value or default)
