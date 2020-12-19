from subprocess import check_call

def pytest_sessionstart(session):
    print(' >>> RUNNING CMAKE CONFIGURE <<<')
    check_call(['cmake', '-S', '.', '-B', 'build', '-GNinja'])
    print(' >>> RUNNING CMAKE CLEAN <<<')
    check_call(['cmake', '--build', 'build', '--target', 'clean'])
    print(' >>> DONE <<<')
    # request.addfinalizer(configure_cmake)

def pytest_runtest_teardown(item):
    print('\n\n'+('v'*80), end='')
