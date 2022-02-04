from threading import Thread
from time import time, sleep
from sys import platform
from socket import gethostbyname, getfqdn
import os
import re


def nowait(func):
    def wrap(*args, **kwargs):
        thread = Thread(target=func, args=args, kwargs=kwargs, daemon=True)
        thread.start()

    return wrap


def timeit(func):
    def wrap(*args, **kwargs):
        s = time()
        res = func(*args, **kwargs)
        print(f'func:{func.__name__}() take {time() - s} sec')
        return res

    return wrap


def sleep_timer(sleep_time: float = 0):

    def outside_wrap(func):
        def wrap(*args, **kwargs):
            start = time()
            res = func(*args, **kwargs)
            process_time = time() - start
            if process_time < sleep_time:
                sleep(sleep_time-process_time)
            return res

        return wrap

    return outside_wrap


def get_hostname() -> str:
    if platform.startswith('linux'):
        with os.popen('hostname -I') as f:
            hostnames = f.read()
        hostname = hostnames.split()[0]
        if len(hostname) > 0:
            return hostname

    return gethostbyname(getfqdn())


if __name__ == '__main__':
    print(get_hostname())
