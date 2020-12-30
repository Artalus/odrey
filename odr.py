#!/usr/bin/env python3
import argparse
import hashlib
import re
import subprocess

from sys import platform
from collections import namedtuple
from typing import *


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument('inputfiles', nargs='+')
    p.add_argument('-Werror', action='store_true')
    p.add_argument('--ignore', action='append', default=[],
        nargs=2, metavar=('symbol', 'file'),
        help='specify pair of <symbol> <file> regexes to ignore when calculating collisions,'
        'example:\n' r'  --ignore boost::.* /usr/lib(32)?/.*\.so')
    a = p.parse_args()
    a.ignore = [IgnorePair(p, *i) for i in a.ignore]
    return a


class IgnorePair:
    symbol: re.Pattern
    file: re.Pattern
    def __init__(self, parser: argparse.ArgumentParser, symbol_re: str, file_re: str):
        try:
            self.symbol = re.compile(symbol_re)
        except re.error as e:
            parser.error(f'Bad "symbol" ignore regex: {e}')
        try:
            self.file = re.compile(file_re)
        except re.error as e:
            parser.error(f'Bad "file" ignore regex: {e}')

    def matches(self, symbol: str, file: str) -> bool:
        return self.symbol.search(symbol) and self.symbol.search(file)


SYMBOL_ELF_RE = re.compile(
#         num      value        size    type    bind    vis     ndx     name
#         1        2            3       4       5       6       7       8
    r'^\s*(\d+):\s+([\da-f]+)\s+(\d+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(.+)$'
    )
ASM_FUNC_HEADER_RE = re.compile(r'^\?(.+@@.+:)$')
#                            offset       instructions             cmd
#                            1            2                        3
ASM_LINE_RE = re.compile(r'^\s*([\dA-E]+):((?: [\dA-E][\dA-E])+)\s+(.+)$')


SymbolInFile = namedtuple('SymbolInFile', ['filename', 'symbol'])


class Symbol:
    def __init__(self, name: str):
        self.name = name
    def __eq__(self, other: object) -> bool:
        raise NotImplementedError()
    def data(self) -> str:
        raise NotImplementedError()


class ReadelfSymbol(Symbol):
    def __init__(self, num, value, size, type_, bind, vis, ndx, name):
        super().__init__(name)
        self.num = num
        self.value = value
        self.size = size
        self.type = type_
        self.bind = bind
        self.vis = vis
        self.ndx = ndx

    def data(self) -> str:
        return f'size={self.size}'

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, ReadelfSymbol)
        and self.name == other.name
        and self.size == other.size
    )

    def __repr__(self) -> str:
        return f'{self.name}:: {self.size}'


class DumpbinSymbol(Symbol):
    def __init__(self, name: str, asm_lines: List[str]):
        super().__init__(name)
        self.name = name
        self.asm = asm_lines

    def data(self) -> str:
        m = hashlib.sha1()
        m.update(self.asm.__repr__().encode())
        h = m.hexdigest()
        return f'asm hash={h}'

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, DumpbinSymbol)
            and self.name == other.name
            and self.asm == other.asm
        )

    def __repr__(self) -> str:
        return f'{self.name}:: {self.asm}'


class FileData:
    def __init__(self, filename: str, symbols: Sequence[Symbol]):
        self.filename = filename
        self.symbols = symbols
    def __repr__(self) -> str:
        return f'{self.filename}:: {self.symbols}'


class Collision:
    def __init__(self, funcname: str, entries: Sequence[SymbolInFile]):
        self.funcname = funcname
        self.entries = entries
    def __repr__(self) -> str:
        return f'{self.funcname}:: {self.entries}'


def main() -> None:
    args = parse_args()
    input_files = filter_input(args.inputfiles)
    symbols = [read_symbols(f) for f in input_files]
    collisions = find_collisions(symbols, args.ignore)
    if collisions:
        print('ODR violations found:')
        for c in collisions:
            print(collision_to_str(c))
        if args.Werror:
            exit(1)


def filter_input(inp: List[str]) -> List[str]:
    # NOTE: will filter out any -lm -lpthread and other system libs
    return [x for x in inp if not x.startswith('-')]


def read_symbols(filename: str) -> FileData:
    if platform.startswith("linux"):
        return read_symbols_readelf(filename)
    elif platform == "win32":
        return read_symbols_dumpbin(filename)
    elif platform == "darwin": # Mac
        pass
    raise RuntimeError(f'Unsupported platform: {platform}')


def read_symbols_readelf(filename: str) -> FileData:
    elf_full = subprocess.check_output(f'readelf -Ws {filename} | c++filt', shell=True).decode()
    elf = elf_full.splitlines()
    symbols = []
    for line in elf:
        m = re.match(SYMBOL_ELF_RE, line)
        if m:
            symbols.append(ReadelfSymbol(*(m.groups())))
    symbols = [x for x in symbols if is_interesting_elf_symbol(x)]
    if not symbols:
        print(f'ODR: ERROR: cannot parse any symbols from `readelf -Ws {filename}` call.')
        print(f'     output was:\n{elf_full}')
        raise RuntimeError('No symbols acquired from readelf')
    return FileData(filename, symbols)


def is_interesting_elf_symbol(s: ReadelfSymbol) -> bool:
    if s.type not in ['FUNC', 'OBJECT']:
        return False
    # static functions, anonymous namespace, etc. - everything that can safely
    # differ, because it is not being exported
    if s.bind == 'LOCAL':
        return False
    return True


def read_symbols_dumpbin(filename: str) -> FileData:
    db = subprocess.check_output(['dumpbin.exe', '/disasm:bytes', filename]).decode()
    db = db.splitlines()
    symbols = []
    asm_lines = []
    function_name = None
    for line in db:
        # print(f'>>> {line}')
        m = re.match(ASM_FUNC_HEADER_RE, line)
        if m:
            if function_name:
                # print(f'>>> asm ended!')
                symbols.append(DumpbinSymbol(function_name, asm_lines))
                asm_lines = []
            function_name = m.group(1)
            # print(f'>>> func: {function_name}')
            continue
        m = re.match(ASM_LINE_RE, line)
        if m:
            asm = m.group(2).strip()
            # print(f'>>> asm: {asm}')
            asm_lines.append(asm)
    if function_name:
        assert asm_lines
        # print(f'>>> asm ended!')
        symbols.append(DumpbinSymbol(function_name, asm_lines))
    return FileData(filename, symbols)


def find_collisions(filesdata: List[FileData], ignores: List[IgnorePair]) -> List[Collision]:
    known_definitions: Dict[str, List[SymbolInFile]] = dict()
    for fd in filesdata:
        for s in fd.symbols:
            if any(i.matches(s.name, fd.filename) for i in ignores):
                continue
            if s.name not in known_definitions:
                known_definitions[s.name] = []
            known_definitions[s.name].append(SymbolInFile(fd.filename, s))
    collisions = []
    for funcname, filesymbols in known_definitions.items():
        uniq = filesymbols[0].symbol
        if any(fs.symbol != uniq for fs in filesymbols):
            collisions.append(Collision(funcname, filesymbols))
    return collisions


def collision_to_str(c: Collision) -> str:
    size_strings = [f'  in file {f}: {s.data()}' for f,s in c.entries]
    ss = '\n'.join(size_strings)
    return f'multiple definitions of {c.funcname}:\n{ss}'


if __name__ == "__main__":
    main()
