from __future__ import annotations
from re import (Match, match as _match, search, findall)

from chromakitx import (ColorType, AnsiColor, XtermColor, CssColor, CustomColor, HSL, RGB, HEX, HSV)

def is_color(value: str) -> bool:
    return bool(_match(pattern=r"^(AnsiColor|XTermColor|CssColor)\.\w+|CustomColor\(.+\)$", string=value.strip()))

def build_color(colors: list[str] | str) -> list[ColorType] | ColorType:
    return _build_color_object(colors.strip()) if isinstance(colors, str) else [_build_color_object(color.strip()) for color in colors]

def _build_color_object(text: str) -> ColorType:
    match text:
        case s if s.startswith("AnsiColor."):
            code: str = s.split(sep=".", maxsplit=1)[1]
            return getattr(AnsiColor, code, AnsiColor.White)

        case s if s.startswith("XtermColor."):
            code: str = s.split(sep=".", maxsplit=1)[1]
            return getattr(XtermColor, code, AnsiColor.White)

        case s if s.startswith("CssColor."):
            code: str = s.split(sep=".", maxsplit=1)[1]
            return getattr(CssColor, code, AnsiColor.White)

        case s if s.startswith("CustomColor("):
            match: Match[str] | None = search(pattern=r"CustomColor\((.+)\)", string=s)

            if not match:
                return AnsiColor.White

            inner: str = match[1].strip()

            if inner.startswith("HSL("):
                values: list[float | int] = _extract_numbers(inner)
                return CustomColor(HSL(*values)) if len(values) == 3 else AnsiColor.White

            if inner.startswith("RGB("):
                values: list[float | int] = _extract_numbers(inner)
                return CustomColor(RGB(*values)) if len(values) == 3 else AnsiColor.White

            if inner.startswith("HSV("):
                values: list[float | int] = _extract_numbers(inner)
                return CustomColor(HSV(*values)) if len(values) == 3 else AnsiColor.White

            if inner.startswith("HEX("):
                hex_match: Match[str] | None = search(pattern=r"HEX\((['\"]?)(#[0-9A-Fa-f]{6})\1\)", string=inner)
                return CustomColor(HEX(hex_match[2])) if hex_match else AnsiColor.White

            return AnsiColor.White

        case _:
            return AnsiColor.White

def _extract_numbers(expr: str) -> list[float | int]:
    return [float(x) if "." in x else int(x) for x in findall(pattern=r"[-+]?\d*\.?\d+", string=expr)]
