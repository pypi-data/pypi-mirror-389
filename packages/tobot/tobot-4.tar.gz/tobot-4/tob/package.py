# This file is placed in the Public Domain.


"module management"


import importlib
import importlib.util
import logging
import os
import sys
import _thread


from .threads import launch
from .utility import md5sum


class Mods:

    dirs = {}
    md5s = {}

    def add(name, path):
        Mods.dirs[name] = path


def getmod(name):
    for nme, path in Mods.dirs.items():
        mname = nme + "." +  name
        module = sys.modules.get(mname, None)
        if module:
            return module
        pth = os.path.join(path, f"{name}.py")
        if Mods.md5s:
            if os.path.exists(pth) and name != "tbl":
                md5 = Mods.md5s.get(name, None)
                if md5sum(pth) != md5:
                    logging.info("md5 error %s", name)
        mod = importer(mname, pth)
        if mod:
            return mod


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


def inits(names, config):
    modz = []
    for name in modules():
        if name not in names:
            continue
        try:
            module = getmod(name)
            if module and "init" in dir(module):
                thr = launch(module.init, config)
                modz.append((module, thr))
        except Exception as ex:
            logging.exception(ex)
            _thread.interrupt_main()
    return modz


def modules():
    mods = []
    for name, path in Mods.dirs.items():
        if not os.path.exists(path):
            continue
        mods.extend([
            x[:-3].split(".")[-1] for x in os.listdir(path)
            if x.endswith(".py") and not x.startswith("__")
           ])
    return sorted(mods)


def sums(checksum):
    tbl = getmod("tbl")
    if not tbl:
        logging.info("no table")
        return
    if checksum and md5sum(tbl.__file__) != checksum:
        logging.info("table checksum error")
        return
    if "MD5" in dir(tbl):
        Mods.md5s.update(tbl.MD5)
    logging.info(checksum)


def __dir__():
    return (
        'Mods',
        'getmod',
        'importer',
        'inits',
        'modules',
        'sums'
    )
