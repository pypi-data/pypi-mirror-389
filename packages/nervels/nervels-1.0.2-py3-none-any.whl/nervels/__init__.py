from __future__ import annotations
from os.path import exists

from nervels.parser import NLSParser
from nervels.compiler import NLSCompiler
from nervels.parser import NLSDocument

from chromakitx import ColorType

def compile_nls(path: str) -> tuple[str, str, list[ColorType], ColorType, ColorType]:
    path: str = path + '.nls'

    if not exists(path):
        raise FileNotFoundError("File " + path + " does not exist")

    with open(file=path, encoding="utf-8") as file:
        content: str = file.read()

    nls_parser: NLSParser = NLSParser(content)
    document: NLSDocument = nls_parser.parse()
    nls_compiler: NLSCompiler = NLSCompiler(document)

    return nls_compiler.compile()

__all__: list[str] = ['compile_nls']
