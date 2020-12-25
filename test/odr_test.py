#!/usr/bin/env python3
import os
import re
import subprocess as sp
import sys

import pytest

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


def test_simple(clean_cmake):
    Build('simple-odr').expect(
        symbol('func'),
        source('foo.cpp'),
        source('bar.cpp'),
    )


# TODO: should be detectable, but requires something other than
# dumpbin /disasm
@pytest.mark.xfail(sys.platform.startswith('win32'),
    reason='implementation insufficient')
def test_application_and_shared_colliding_func(clean_cmake):
    b = Build('application_and_shared')
    b.expect(
        symbol('colliding_func'),
        source('app.cpp'),
        source('application_and_shared-lib'),
    )


# TODO: should be detectable, but requires something other than
# dumpbin /disasm
@pytest.mark.xfail(sys.platform.startswith('win32'),
    reason='implementation insufficient')
def test_application_and_shared_colliding_variables(clean_cmake):
    b = Build('application_and_shared')
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


# TODO: should be detectable, but requires something other than
# dumpbin /disasm
@pytest.mark.xfail(sys.platform.startswith('win32'),
    reason='implementation insufficient')
def test_application_and_shared_colliding_inlines(clean_cmake):
    b = Build('application_and_shared')
    b.expect(
        symbol('colliding_inline'),
        source('app.cpp'),
        source('application_and_shared-lib'),
    )


def test_application_and_shared_local_symbols(clean_cmake):
    b = Build('application_and_shared')
    b.expect_not(
        symbol('local_.+_[12]'),
        source('app.cpp'),
        source('application_and_shared-lib'),
    )

@pytest.mark.xfail(sys.platform.startswith('linux'),
    reason="gcc detects the bug itself")
# TODO: should be detectable on win32, but requires something other than
# dumpbin /disasm
@pytest.mark.xfail(sys.platform.startswith('win32'),
    reason='implementation insufficient')
def test_application_with_static_colliding_vars(clean_cmake):
    b = Build('application_and_static')
    b.expect(
        symbol('colliding_variable'),
        source('app.cpp'),
        source('application_and_static-lib'),
    )
    b.expect(
        symbol('colliding_const'),
        source('app.cpp'),
        source('application_and_static-lib'),
    )

# TODO: should be detectable, but requires something other than
# dumpbin /disasm
@pytest.mark.xfail(sys.platform.startswith('win32') and 'GITHUB_ACTIONS' in os.environ,
    reason='flaky test that passes locally but not on GHA')
def test_application_with_static_colliding_inline(clean_cmake):
    b = Build('application_and_static')
    b.expect(
        symbol('colliding_inline'),
        source('app.cpp'),
        source('application_and_static-lib'),
    )


# TODO: should be detectable, but requires something other than
# dumpbin /disasm
@pytest.mark.xfail(sys.platform.startswith('win32'),
    reason='implementation insufficient')
def test_application_with_static_local_symbols(clean_cmake):
    b = Build('application_and_static')
    b.expect_not(
        symbol('local_.+_[12]'),
        source('app.cpp'),
        source('application_and_static-lib'),
    )
