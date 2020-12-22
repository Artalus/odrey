#!/usr/bin/env python3
import re
import subprocess as sp

class Build:
    def __init__(self, target):
        print(' : running...')
        print('^'*80)
        p = sp.Popen(
            ['cmake', '--build', 'build', '--target', target],
            stdout=sp.PIPE, stderr=sp.PIPE,
        )
        self.out, err = tuple(s.decode() for s in p.communicate())
        p.wait()
        print('--- BUILD OUT:')
        print(self.out.rstrip().replace('\r',''))
        if err:
            print('--- BUILD ERR:')
            print(err)
        if p.returncode:
            raise RuntimeError(f'Build failed with code {p.returncode}')

    def expect(self, *args):
        regex = '\n'.join(args)
        assert re.search(regex, self.out) is not None

    def expect_not(self, *args):
        regex = '\n'.join(args)
        assert re.search(regex, self.out) is None

def symbol(f):
    return r'multiple definitions of '+f+'.*'
def source(f):
    return r'\s+in file .*'+f+'.*'

def test_simple():
    Build('simple-odr').expect(
        symbol('func'),
        source('foo.cpp'),
        source('bar.cpp'),
    )

def test_application():
    b = Build('application_and_shared')
    b.expect(
        symbol('colliding_func'),
        source('app.cpp'),
        source('application_and_shared-lib'),
    )
    b.expect(
        symbol('colliding_variable'),
        source('app.cpp'),
        source('application_and_shared-lib'),
    )
    b.expect(
        symbol('colliding_const'),
        source('app.cpp'),
        source('application_and_shared-lib'),
    )
    b.expect(
        symbol('colliding_inline'),
        source('app.cpp'),
        source('application_and_shared-lib'),
    )
    b.expect_not(
        symbol('local_.+_[12]'),
        source('app.cpp'),
        source('application_and_shared-lib'),
    )
