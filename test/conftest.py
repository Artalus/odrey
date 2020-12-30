import os
import sys
from subprocess import check_call
import pytest

def flush():
    sys.stdout.flush()
    sys.stderr.flush()

@pytest.fixture
def clean_cmake(request):
    print(' >>> RUNNING CMAKE CONFIGURE <<<')
    flush()
    cwd = os.getcwd()
    check_call(['cmake', '-GNinja',
        '-S', 'test',
        '-B', 'build',
        f'-DODREY_SCRIPT_PATH={cwd}/odr.py',
        '-DODREY_ODREY_WRITE_JSON=ON',
        '-DODREY_WRITE_JSON=ON',
        ])
    flush()
    print(' >>> RUNNING CMAKE CLEAN <<<')
    flush()
    check_call(['cmake', '--build', 'build', '--target', 'clean'])
    flush()
    print(' >>> DONE <<<')
    flush()

def pytest_runtest_teardown(item):
    print('\n\n'+('v'*80), end='')
