#!/usr/bin/env python3
import argparse
import re
import subprocess
from collections import namedtuple
from typing import List, Dict
 
 
def parse_args() -> argparse.Namespace:
   p = argparse.ArgumentParser()
   p.add_argument('inputfiles', nargs='+')
   p.add_argument('-Werror', action='store_true')
   return p.parse_args()
 
 
#                            num      value   size    type    bind    vis     ndx     name
#                            1        2       3       4       5       6       7       8
SYMBOL_RE = re.compile(r'^\s*(\d+):\s+(\d+)\s+(\d+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(.+)$')
 
 
Symbol = namedtuple('Symbol', ['num','value','size','type','bind','vis','ndx','name'])
SizeInFile = namedtuple('SizeData', ['filename','size'])
 
 
class FileData:
   def __init__(self, filename: str, symbols: List[Symbol]):
       self.filename = filename
       self.symbols = symbols
 
 
class Collision:
   def __init__(self, funcname: str, entries: List[SizeInFile]):
       self.funcname = funcname
       self.entries = entries
 
 
def main() -> None:
   args = parse_args()
   symbols = [read_symbols(f) for f in args.inputfiles]
   collisions = find_collisions(symbols)
   if collisions:
       print('ODR violations found:')
       for c in collisions:
           print(collision_to_str(c))
       if args.Werror:
           exit(1)
 
 
def read_symbols(filename: str) -> FileData:
   elf = subprocess.check_output(f'readelf -Ws {filename} | c++filt', shell=True).decode()
   elf = elf.splitlines()
   symbols = []
   for line in elf:
       m = re.match(SYMBOL_RE, line)
       if m:
           symbols.append(Symbol(*(m.groups())))
   functions = [s for s in symbols if s.type == 'FUNC']
   return FileData(filename, functions)
 
 
def find_collisions(filesdata: List[FileData]) -> List[Collision]:
   known_sizes: Dict[str, List[SizeInFile]] = dict()
   for fd in filesdata:
       for s in fd.symbols:
           if s.name not in known_sizes:
               known_sizes[s.name] = []
           known_sizes[s.name].append(SizeInFile(fd.filename, s.size))
   collisions = []
   for funcname, sizedatas in known_sizes.items():
       uniq = sizedatas[0].size
       if any(sd.size != uniq for sd in sizedatas):
           collisions.append(Collision(funcname, sizedatas))
   return collisions
 
 
def collision_to_str(c: Collision) -> str:
   size_strings = [f'  in file {f}: size={sz}' for f,sz in c.entries]
   ss = '\n'.join(size_strings)
   return f'multiple definitions of {c.funcname}:\n{ss}'
 
 
if __name__ == "__main__":
   main()
