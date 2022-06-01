import os
import sys
import threading
from shutil import get_terminal_size
from typing import Iterable
from .RepeatTimer import RepeatTimer


def bar(bar_width, percent, char='#', blank_char=' ') -> str:
    percent %= 101
    char_width = round(bar_width * percent / 100)
    blank_width = bar_width - char_width
    return '%3d%% | %s%s |' % (percent, char * char_width, blank_char * blank_width)


class Printer(RepeatTimer):
    def __init__(self, printable_objs: Iterable, interval=0.1, show_usage=False, show_all_thread=False):
        RepeatTimer.__init__(self, interval=interval, name='ShellPrinter')
        self.show_usage = show_usage
        self.show_all_thread = show_all_thread
        self.objs = printable_objs
        self.bar_width = 30
        self.padding_width = get_terminal_size()[0]

    def init_phase(self):
        pass

    def execute_phase(self):
        self.clean_screen()
        if self.show_usage:
            self.print(self.get_cpu_usage())
            self.print(self.get_memory_usage())
        for obj in self.objs:
            for s in str(obj).split('\n'):
                if s:
                    self.print(s)
        if self.show_all_thread:
            for index, t in enumerate(threading.enumerate()):
                self.print('Thread-%s: %s' % (index, t))

    def close_phase(self):
        del self.objs

    def print(self, s: str):
        print(s.ljust(self.padding_width))

    @staticmethod
    def clean_screen():
        print("\033[H\033[1J", end='')

    def set_show_usage(self, show_usage: bool):
        self.show_usage = show_usage

    def get_cpu_usage(self) -> str:
        pass

    def get_memory_usage(self) -> str:
        pass

    def bar(self, percent, char='#', blank_char=' ') -> str:
        return bar(self.bar_width, percent, char, blank_char)


class WindowsShellPrinter(Printer):
    def __init__(self, printable_objs: Iterable, interval=0.2, show_usage=False):
        Printer.__init__(self, printable_objs, interval=interval, show_usage=show_usage)

    def init_phase(self):
        os.system('cls')

    def get_cpu_usage(self):
        return ''

    def get_memory_usage(self):
        return ''


class LinuxShellPrinter(Printer):
    def __init__(self, printable_objs: Iterable, interval=0.2, show_usage=False):
        Printer.__init__(self, printable_objs, interval=interval, show_usage=show_usage)

    def init_phase(self):
        os.system('clear')

    def get_cpu_usage(self) -> str:
        # cpu user nice system idle iowait ...
        # grep 'cpu ' /proc/stat | awk '{print ($2+$4) / ($2+$4+$5) * 100}'
        cmd = r"grep 'cpu ' /proc/stat | awk '{print ($2+$4) / ($2+$4+$5) * 100}'"
        try:
            with os.popen(cmd, 'r') as f:
                cpu_usage = f.readline()
            percent = round(float(cpu_usage))
            return (self.bar(percent) + ' CPU').rstrip()
        except Exception:
            return 'Fail to get Memory usage %s'

    def get_memory_usage(self) -> str:
        # free -m | grep ':' | awk '{print $1, $2, $3}'
        cmd = "free -m | grep ':' | awk '{print $1, $2, $3}'"
        try:
            usage = ''
            with os.popen(cmd, 'r') as f:
                usages = [
                    [s for s in line.strip().split()]
                    for line in f.readlines()
                ]
            for name, total, used in usages:
                name = name[:-1]
                total = int(total)
                used = int(used)
                usage += self.bar(used / total * 100) + ' %dMB / %dMB %s\n' % (used, total, name)
        except Exception:
            return 'Fail to get Memory usage'

        return usage.rstrip()


class ShellPrinter:
    def __new__(cls, *args, **kwargs):
        if sys.platform.startswith('linux'):
            return LinuxShellPrinter(printable_objs=args, interval=0.2, show_usage=True)
        return WindowsShellPrinter(printable_objs=args, interval=0.2, show_usage=True)
