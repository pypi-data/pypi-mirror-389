# This file is placed in the Public Domain.


"uptime"


import time


from tob.runtime import STARTTIME
from tob.utility import elapsed


def upt(event):
    event.reply(elapsed(time.time()-STARTTIME))
