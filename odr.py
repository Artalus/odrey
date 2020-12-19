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
    return p.parse_args()


#                            num      value   size    type    bind    vis     ndx     name
#                            1        2       3       4       5       6       7       8
SYMBOL_ELF_RE = re.compile(r'^\s*(\d+):\s+(\d+)\s+(\d+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(.+)$')
ASM_FUNC_HEADER_RE = re.compile(r'^\?(.+@@.+:)$')
#                            offset       instructions             cmd
#                            1            2                        3
ASM_LINE_RE = re.compile(r'^\s*([\dA-E]+):((?: [\dA-E][\dA-E])+)\s+(.+)$')


SymbolInFile = namedtuple('SymbolInFile', ['filename', 'symbol'])

class Symbol:
    def __init__(self, name: str):
        self.name = name
    def __eq__(self, other) -> bool:
        raise NotImplementedError()
    def data(self) -> str:
        raise NotImplementedError()


class ElfSymbol(Symbol):
    def __init__(self, num, value, size, type, bind, vis, ndx, name):
        super().__init__(name)
        self.num = num
        self.value = value
        self.size = size
        self.type = type
        self.bind = bind
        self.vis = vis
        self.ndx = ndx
        self.name = name

    def data(self) -> str:
        return f'size={self.size}'

    def __eq__(self, other):
        return self.name == other.name and self.size == other.size

    def __repr__(self):
        return f'{self.name}:: {self.size}'


class PeSymbol(Symbol):
    def __init__(self, name: str, asm_lines: List[str]):
        super().__init__(name)
        self.name = name
        self.asm = asm_lines

    def data(self) -> str:
        m = hashlib.sha1()
        m.update(self.asm.__repr__().encode())
        h = m.hexdigest()
        return f'asm hash={h}'

    def __eq__(self, other):
        return self.name == other.name and self.asm == other.asm

    def __repr__(self):
        return f'{self.name}:: {self.asm}'


class FileData:
    def __init__(self, filename: str, symbols: Sequence[Symbol]):
        self.filename = filename
        self.symbols = symbols
    def __repr__(self):
        return f'{self.filename}:: {self.symbols}'


class Collision:
    def __init__(self, funcname: str, entries: Sequence[SymbolInFile]):
        self.funcname = funcname
        self.entries = entries
    def __repr__(self):
        return f'{self.funcname}:: {self.entries}'


def main() -> None:
    args = parse_args()
    symbols = [read_symbols(f) for f in args.inputfiles]
    # print(symbols)
    collisions = find_collisions(symbols)
    if collisions:
        print('ODR violations found:')
        for c in collisions:
            print(collision_to_str(c))
        if args.Werror:
            exit(1)


def read_symbols(filename: str) -> FileData:
    if platform in ("linux", "linux2"):
        return read_symbols_elf(filename)
    elif platform == "win32":
        return read_symbols_windows(filename)
    elif platform == "darwin":
        pass# OS X
    raise RuntimeError(f'Unsupported platform: {platform}')


def read_symbols_elf(filename: str) -> FileData:
    elf = subprocess.check_output(f'readelf -Ws {filename} | c++filt', shell=True).decode()
    elf = elf.splitlines()
    symbols = []
    for line in elf:
        m = re.match(SYMBOL_ELF_RE, line)
        if m:
            symbols.append(ElfSymbol(*(m.groups())))
    functions = [s for s in symbols if s.type == 'FUNC']
    return FileData(filename, functions)

def read_symbols_windows(filename: str) -> FileData:
    pe = subprocess.check_output(['dumpbin.exe', '/disasm:bytes', filename]).decode()
    pe = pe.splitlines()
    symbols = []
    asm_lines = []
    function_name = None
    for line in pe:
        # print(f'>>> {line}')
        m = re.match(ASM_FUNC_HEADER_RE, line)
        if m:
            if function_name:
                # print(f'>>> asm ended!')
                symbols.append(PeSymbol(function_name, asm_lines))
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
        symbols.append(PeSymbol(function_name, asm_lines))
    return FileData(filename, symbols)


def find_collisions(filesdata: List[FileData]) -> List[Collision]:
    known_definitions: Dict[str, List[SymbolInFile]] = dict()
    for fd in filesdata:
        for s in fd.symbols:
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
