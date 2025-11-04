# This file is placed in the Public Domain.


"write your own commands"


import inspect


from .brokers import Fleet
from .methods import parse
from .package import getmod, modules


class Commands:

    cmds = {}
    names = {}

    @staticmethod
    def add(*args) -> None:
        for func in args:
            name = func.__name__
            Commands.cmds[name] = func
            Commands.names[name] = func.__module__.split(".")[-1]

    @staticmethod
    def get(cmd):
        func = Commands.cmds.get(cmd, None)
        if not func:
            name = Commands.names.get(cmd, None)
            if name:
                module = getmod(name)
                if module:
                    scan(module)
            func =  Commands.cmds.get(cmd, None)
        return func


def command(evt):
    parse(evt, evt.txt)
    func = Commands.get(evt.cmd)
    if func:
        func(evt)
        Fleet.display(evt)
    evt.ready()


def scan(module):
    for key, cmdz in inspect.getmembers(module, inspect.isfunction):
        if key.startswith("cb"):
            continue
        if 'event' in inspect.signature(cmdz).parameters:
            Commands.add(cmdz)


def scanner(names=[]):
    res = []
    for nme in modules():
        if names and nme not in names:
            continue
        module = getmod(nme)
        if not module:
            continue
        scan(module)
        res.append(module)
    return res


def table():
    tbl = getmod("tbl")
    if tbl and "NAMES" in dir(tbl):
        Commands.names.update(tbl.NAMES)
    else:
        scanner()


def __dir__():
    return (
        'Comamnds',
        'command',
        'parse',
        'scan',
        'scanner',
        'table'
    )
