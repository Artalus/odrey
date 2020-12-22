import sys
import os
from subprocess import check_call

def flush():
    sys.stdout.flush()
    sys.stderr.flush()


def pytest_sessionstart(session):
    print(' >>> RUNNING CMAKE CONFIGURE <<<')
    flush()
    check_call(['cmake',
                '-S', os.path.dirname(__file__),
                '-B', os.path.join(os.path.dirname(__file__), 'build'),
                '-GNinja'])
    flush()
    print(' >>> RUNNING CMAKE CLEAN <<<')
    flush()
    check_call(['cmake', '--build', 'build', '--target', 'clean'])
    flush()
    print(' >>> DONE <<<')
    flush()
    # request.addfinalizer(configure_cmake)

def pytest_runtest_teardown(item):
    print('\n\n'+('v'*80), end='')
