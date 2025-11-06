# This file is placed in the Public Domain.


"write your own commands"


import importlib
import importlib.util
import inspect
import os
import sys


from .clients import Fleet
from .methods import parse


class Config:

    level = "warn"
    name = os.path.dirname(__file__).split(os.sep)[-1]
    version = 137


class Commands:

    cmds = {}
    names = {}

    @staticmethod
    def add(*args):
        for func in args:
            name = func.__name__
            Commands.cmds[name] = func
            Commands.names[name] = func.__module__.split(".")[-1]

    @staticmethod
    def get(cmd):
        return Commands.cmds.get(cmd, None)


def command(evt):
    parse(evt, evt.txt)
    func = Commands.get(evt.cmd)
    if func:
        func(evt)
        Fleet.display(evt)
    evt.ready()


def importer(name, pth):
    if not os.path.exists(pth):
        return
    spec = importlib.util.spec_from_file_location(name, pth)
    if not spec or not spec.loader:
        return
    mod = importlib.util.module_from_spec(spec)
    if not mod:
        return
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def modules(pkg):
    path = pkg.__path__[0]
    if not os.path.exists(path):
        return []
    return sorted([
                   x[:-3].split(".")[-1] for x in os.listdir(path)
                   if x.endswith(".py") and not x.startswith("__")
                  ])


def scan(module):
    for key, cmdz in inspect.getmembers(module, inspect.isfunction):
        if key.startswith("cb"):
            continue
        if 'event' in inspect.signature(cmdz).parameters:
            Commands.add(cmdz)


def scanner(pkg, names=[]):
    for modname in dir(pkg):
        if modname.startswith("__"):
            continue
        if names and modname not in names:
            continue
        nme = pkg.__name__ + "." + modname
        path = os.path.join(pkg.__path__[0], modname + ".py")
        mod = importer(nme, path)
        if mod:
            scan(mod)


def __dir__():
    return (
        'Comamnds',
        'command',
        'importer',
        'modules',
        'scan',
        'scanner',
        'table'
    )
