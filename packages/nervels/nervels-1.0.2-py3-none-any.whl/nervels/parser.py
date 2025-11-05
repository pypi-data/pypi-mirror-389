from __future__ import annotations
from re import (Match, match as _match)

from nervels.nodes import ColorNode
from nervels.document import NLSDocument
from nervels.utils import is_color

class NLSParser:
    def __init__(self, content: str) -> None:
        self.lines: list[str] = content.splitlines()
        self.position: int = 0

    def parse(self) -> NLSDocument:
        properties: dict[str, str | ColorNode] = {}
        sections: dict[str, list[str]] = {}

        while self.position < len(self.lines):
            raw: str = self.lines[self.position].strip()
            self.position += 1

            if not raw or raw.startswith("#"):
                continue

            section_match: Match[str] | None = _match(pattern=r"^\[(.+?)]$", string=raw)

            if section_match:
                name: str = section_match[1]
                sections[name] = self._collect_section()

                continue

            prop_match: Match[str] | None = _match(pattern=r"^([\w\-]+)\s*:\s*(.+)$", string=raw)

            if prop_match:
                (key, value) = prop_match[1], prop_match[2]
                properties[key] = ColorNode.parse(value) if is_color(value) else value

        return NLSDocument(properties=properties, sections=sections)

    def _collect_section(self) -> list[str]:
        content: list[str] = []

        while self.position < len(self.lines):
            current: str = self.lines[self.position].rstrip()

            if _match(pattern=r"^\[.+?]$", string=current):
                break

            content.append(current)
            self.position += 1

        start_idx: int = 0
        end_idx:   int = len(content)

        for (i, line) in enumerate(content):
            if line.strip():
                start_idx = i
                break

        for i in range((len(content) - 1), -1, -1):
            if content[i].strip():
                end_idx = i + 1
                break

        return content[start_idx:end_idx]
