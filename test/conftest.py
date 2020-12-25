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
    check_call(['cmake', '-S', 'test', '-B', 'build', '-GNinja'])
    flush()
    print(' >>> RUNNING CMAKE CLEAN <<<')
    flush()
    check_call(['cmake', '--build', 'build', '--target', 'clean'])
    flush()
    print(' >>> DONE <<<')
    flush()

def pytest_runtest_teardown(item):
    print('\n\n'+('v'*80), end='')
