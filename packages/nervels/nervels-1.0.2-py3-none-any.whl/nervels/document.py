from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(slots=True)
class NLSDocument:
    properties: dict[str, Any]
    sections: dict[str, list[str]]

    def get_property(self, key: str) -> Any:
        return self.properties.get(key)

    def get_section(self, name: str) -> list[str]:
        return self.sections.get(name, [])
