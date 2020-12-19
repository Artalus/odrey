#!/usr/bin/env python3
import re
import subprocess
from subprocess import check_call

class Build:
    def __init__(self, target):
        print(' : running...')
        print('^'*80)
        p = subprocess.Popen(
            ['cmake', '--build', 'build', '--target', target],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        self.out, err = tuple(s.decode() for s in p.communicate())
        p.wait()
        print('--- BUILD OUT:')
        print(self.out.rstrip().replace('\r',''))
        if err:
            print('--- BUILD ERR:')
            print(err)

    def expect(self, *args):
        regex = '\n'.join(args)
        assert re.search(regex, self.out) is not None

def function(f):
    return r'multiple definitions of '+f+'.*'
def source(f):
    return r'\s+in file .*'+f+'.*'

def test_simple():
    Build('simple-odr').expect(
        function('func'),
        source('foo.cpp'),
        source('bar.cpp'),
    )

def test_simple_inline():
    Build('simple-inline-main').expect(
        function('func'),
        source('foo.cpp'),
        source('bar.cpp'),
    )
