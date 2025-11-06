# This file is placed in the Public Domain.


"runtime"


import logging 
import os
import pathlib
import sys
import time


from .command import modules
from .threads import launch


NAME = os.path.dirname(__file__).split(os.sep)[-1]
STARTTIME = time.time()


def check(txt):
    args = sys.argv[1:]
    for arg in args:
        if not arg.startswith("-"):
            continue
        for char in txt:
            if char in arg:
                return True
    return False


def daemon(verbose=False):
    pid = os.fork()
    if pid != 0:
        os._exit(0)
    os.setsid()
    pid2 = os.fork()
    if pid2 != 0:
        os._exit(0)
    if not verbose:
        with open('/dev/null', 'r', encoding="utf-8") as sis:
            os.dup2(sis.fileno(), sys.stdin.fileno())
        with open('/dev/null', 'a+', encoding="utf-8") as sos:
            os.dup2(sos.fileno(), sys.stdout.fileno())
        with open('/dev/null', 'a+', encoding="utf-8") as ses:
            os.dup2(ses.fileno(), sys.stderr.fileno())
    os.umask(0)
    os.chdir("/")
    os.nice(10)


def excepthook(*args):
    try:
       type, value, trace = args
    except ValueError:
       type = args[0][0]
       value = args[0][1]
    if type not in (KeyboardInterrupt, EOFError):
        logging.exception(value)
    os._exit(0)


def forever():
    while True:
        try:
            time.sleep(0.1)
        except (KeyboardInterrupt, EOFError):
            break


def inits(pkg, names):
    res = []
    for name in sorted(modules(pkg)):
        if name not in names:
            continue
        nme = pkg.__name__ + "." + name
        module = sys.modules.get(nme, None)
        if not module or "init" not in dir(module):
            continue
        thr = launch(module.init)
        res.append((module, thr))
    return res


def pidfile(filename):
    if os.path.exists(filename):
        os.unlink(filename)
    path2 = pathlib.Path(filename)
    path2.parent.mkdir(parents=True, exist_ok=True)
    with open(filename, "w", encoding="utf-8") as fds:
        fds.write(str(os.getpid()))


def privileges():
    import getpass
    import pwd
    pwnam2 = pwd.getpwnam(getpass.getuser())
    os.setgid(pwnam2.pw_gid)
    os.setuid(pwnam2.pw_uid)


def wrapped(func):
    try:
        func()
    except (KeyboardInterrupt, EOFError):
        pass


def wrap(func):
    import termios
    old = None
    try:
        old = termios.tcgetattr(sys.stdin.fileno())
    except termios.error:
        pass
    try:
        wrapped(func)
    finally:
        if old:
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old)


def __dir__():
    return (
        'STARTTIME',
        'boot',
        'check',
        'daemon',
        'forever',
        'inits',
        'level',
        'pidfile',
        'privileges',
        'wrap',
        'wrapped'
    )
