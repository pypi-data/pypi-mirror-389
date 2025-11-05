from __future__ import annotations
from dataclasses import dataclass
from re import (Match, match as _match)

@dataclass(slots=True)
class ColorNode:
    value: str
    module: str | None = None
    attribute: str | None = None

    @classmethod
    def parse(cls, value: str) -> ColorNode:
        match: Match[str] | None = _match(pattern=r"^(?!CustomColor)(\w+)\.(\w+)$", string=value.strip())
        return cls(value=value, module=match[1], attribute=match[2]) if match else cls(value=value)
