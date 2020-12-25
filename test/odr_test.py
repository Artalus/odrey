#!/usr/bin/env python3
import os
import re
import subprocess as sp
import sys

import pytest


def flush():
    sys.stdout.flush()
    sys.stderr.flush()

class Build:
    target: str

    class Checker:
        def __init__(self, out):
            self.out = out

        def expect(self, *args):
            regex = '\n'.join(args)
            assert re.search(regex, self.out) is not None

        def expect_not(self, *args):
            regex = '\n'.join(args)
            assert re.search(regex, self.out) is None

    @pytest.fixture(scope='class', autouse=True)
    def build_output(self):
        assert self.target

        print('\n >>> RUNNING CMAKE CONFIGURE <<<')
        flush()
        sp.check_call(['cmake', '-S', 'test', '-B', 'build', '-GNinja'])
        flush()
        print(' >>> RUNNING CMAKE CLEAN <<<')
        flush()
        sp.check_call(['cmake', '--build', 'build', '--target', 'clean'])
        flush()
        print(' >>> RUNNING CMAKE BUILD <<<')
        p = sp.Popen(
            ['cmake', '--build', 'build', '--target', self.target],
            stdout=sp.PIPE, stderr=sp.PIPE,
        )
        out, err = tuple(s.decode() for s in p.communicate())
        p.wait()
        flush()
        print('>>> BUILD OUT <<<')
        print(out.rstrip().replace('\r',''))
        if err:
            print('>>> BUILD ERR <<<')
            print(err)
        if p.returncode:
            raise RuntimeError(f'Build failed with code {p.returncode}')
        yield Build.Checker(out)


def symbol(f):
    return r'multiple definitions of '+f+'.*'
def source(f):
    return r'\s+in file .*'+f+'.*'

@pytest.mark.usefixtures('build_output')
class TestSimpleOdr(Build):
    target = 'simple-odr'

    def test_simple(self, build_output):
        build_output.expect(
            symbol('func'),
            source('foo.cpp'),
            source('bar.cpp'),
        )


@pytest.mark.usefixtures('build_output')
class TestApplicationAndShared(Build):
    target = 'application_and_shared'

    # TODO: should be detectable, but requires something other than
    # dumpbin /disasm
    @pytest.mark.xfail(sys.platform.startswith('win32'),
        reason='implementation insufficient')
    def test_colliding_func(self, build_output):
        build_output.expect(
            symbol('colliding_func'),
            source('app.cpp'),
            source('application_and_shared-lib'),
        )


    # TODO: should be detectable, but requires something other than
    # dumpbin /disasm
    @pytest.mark.xfail(sys.platform.startswith('win32'),
        reason='implementation insufficient')
    def test_colliding_variables(self, build_output):
        build_output.expect(
            symbol('colliding_variable'),
            source('app.cpp'),
            source('application_and_shared-lib'),
        )
        build_output.expect(
            symbol('colliding_const'),
            source('app.cpp'),
            source('application_and_shared-lib'),
        )


    # TODO: should be detectable, but requires something other than
    # dumpbin /disasm
    @pytest.mark.xfail(sys.platform.startswith('win32'),
        reason='implementation insufficient')
    def test_colliding_inlines(self, build_output):
        build_output.expect(
            symbol('colliding_inline'),
            source('app.cpp'),
            source('application_and_shared-lib'),
        )


    def test_local_symbols(self, build_output):
        build_output.expect_not(
            symbol('local_.+_[12]'),
            source('app.cpp'),
            source('application_and_shared-lib'),
        )


@pytest.mark.usefixtures('build_output')
class TestApplicationAndStatic(Build):
    target = 'application_and_static'

    @pytest.mark.xfail(sys.platform.startswith('linux'),
        reason="gcc detects the bug itself")
    # TODO: should be detectable on win32, but requires something other than
    # dumpbin /disasm
    @pytest.mark.xfail(sys.platform.startswith('win32'),
        reason='implementation insufficient')
    def test_colliding_vars(self, build_output):
        build_output.expect(
            symbol('colliding_variable'),
            source('app.cpp'),
            source('application_and_static-lib'),
        )
        build_output.expect(
            symbol('colliding_const'),
            source('app.cpp'),
            source('application_and_static-lib'),
        )

    # TODO: should be detectable, but requires something other than
    # dumpbin /disasm
    @pytest.mark.xfail(sys.platform.startswith('win32') and 'GITHUB_ACTIONS' in os.environ,
        reason='flaky test that passes locally but not on GHA')
    def test_colliding_inline(self, build_output):
        build_output.expect(
            symbol('colliding_inline'),
            source('app.cpp'),
            source('application_and_static-lib'),
        )


    # TODO: should be detectable, but requires something other than
    # dumpbin /disasm
    @pytest.mark.xfail(sys.platform.startswith('win32'),
        reason='implementation insufficient')
    def test_local_symbols(self, build_output):
        build_output.expect_not(
            symbol('local_.+_[12]'),
            source('app.cpp'),
            source('application_and_static-lib'),
        )
