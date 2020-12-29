#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import re
import subprocess
import time

from sys import platform
from collections import namedtuple
from typing import *


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument('inputfiles', nargs='+')
    p.add_argument('-Werror', action='store_true')
    p.add_argument('--output-json')
    p.add_argument('--output-root', default='odrey')
    p.add_argument('--target')
    p.add_argument('--silent', action='store_true')
    return p.parse_args()


#                                num      value        size                    type    bind    vis     ndx     name
#                                1        2            3                       4       5       6       7       8
SYMBOL_ELF_RE = re.compile(r'^\s*(\d+):\s+([\da-f]+)\s+((?:0x)?(?:[\da-f]+))\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(.+)$')
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


class ReadelfSymbol(Symbol):
    def __init__(self, num, value, size, type, bind, vis, ndx, name):
        super().__init__(name)
        self.num = num
        self.value = value
        self.size = size
        self.type = type
        self.bind = bind
        self.vis = vis
        self.ndx = ndx

    def data(self) -> str:
        return f'size={self.size}'

    def __eq__(self, other):
        return self.name == other.name and self.size == other.size

    def __repr__(self):
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
    def __init__(self, funcname: str, demangled: Optional[str], entries: Sequence[SymbolInFile]):
        self.funcname = funcname
        self.demangled = demangled
        self.entries = entries
    def __repr__(self):
        return f'{self.funcname}:: {self.entries}'


def main() -> None:
    args = parse_args()
    input_files = filter_input(args.inputfiles)
    symbols = [read_symbols(f) for f in input_files]
    collisions = find_collisions(symbols)
    if collisions:
        print('ODR violations found' + ('' if args.silent else ':'))
        if not args.silent:
            for c in collisions:
                print(collision_to_str(c))
        if args.output_json:
            jfile = compose_output_filename(args.output_root, args.output_json)
            write_collisions_to_json(collisions, jfile, args.target)
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
    elf_full = subprocess.check_output(f'readelf -Ws {filename}', shell=True).decode()
    elf = elf_full.splitlines()
    symbols = []
    for line in elf:
        m = re.match(SYMBOL_ELF_RE, line)
        if m:
            symbols.append(ReadelfSymbol(*(m.groups())))
    symbols = [x for x in symbols if is_interesting_elf_symbol(x)]
    if not symbols:
        print(f'ODR: WARNING: cannot parse any symbols from `readelf -Ws {filename}` call.')
        print(f'     output was:\n{elf_full}')
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
            #TODO: something else than subprocess
            if platform.startswith('linux'):
                demangled = subprocess.check_output(['c++filt', funcname]).decode().strip()
            else:
                demangled = None
            collisions.append(Collision(funcname, demangled, filesymbols))
    return collisions


def collision_to_str(c: Collision) -> str:
    size_strings = [f'  in file {f}: {s.data()}' for f,s in c.entries]
    dmg = f'(aka {c.demangled})\n' if c.demangled else ''
    ss = '\n'.join(size_strings)
    return f'multiple definitions of {c.funcname}:\n{dmg}{ss}'


def compose_output_filename(odrey_root: str, filename: str) -> str:
    if platform == 'win32' and len(filename)>3 and filename[1]==':' and filename[2] in ('/', '\\'):
        filename = filename[3:]
    elif filename.startswith('/'):
        filename = filename[1:]
    return os.path.join(odrey_root, filename)


def write_collisions_to_json(collisions: Sequence[Collision], json_filename: str, target: str) -> None:
    dirs, _ = os.path.split(json_filename)
    os.makedirs(dirs, exist_ok=True)
    collisions_jsonlist = []
    for c in collisions:
        funcname = c.funcname
        entries_jsonlist = []
        out = "ODR: multiple definitions of %s:\n" % funcname
        for filename, symbol in c.entries:
            e = dict(filename=filename, data=symbol.data())
            entries_jsonlist.append(e)
        j = dict(name=funcname, entries=entries_jsonlist)
        collisions_jsonlist.append(j)
    out_json = dict(target=target, collisions=collisions_jsonlist, timestamp_seconds=int(time.time()))
    with open(json_filename, 'w') as f:
        json.dump(out_json, f, indent=4)



if __name__ == "__main__":
    main()
