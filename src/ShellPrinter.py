import os
import sys
from .RepeatTimer import RepeatTimer
from typing import Iterable


def bar(bar_width, percent, char='#', blank_char=' ') -> str:
    percent %= 101
    char_width = round(bar_width * percent / 100)
    blank_width = bar_width - char_width
    return '%3d%% | %s%s |' % (
        percent,
        char * char_width,
        blank_char * blank_width
    )


class Printer(RepeatTimer):
    def __init__(self, printable_objs: Iterable, interval=0.1, show_usage=False):
        RepeatTimer.__init__(self, interval=interval)
        self.show_usage = show_usage
        self.objs = printable_objs
        self.bar_width = 30

    def execute_phase(self):
        self.clean_screen()
        if self.show_usage:
            print('\r' + self.get_cpu_usage())
            print('\r' + self.get_memory_usage())
        for obj in self.objs:
            print('\r' + str(obj))

    @staticmethod
    def clean_screen():
        print("\033[H\033[J", end='')

    def close_phase(self):
        del self.objs

    def set_show_usage(self, show_usage: bool):
        self.show_usage = show_usage

    def get_cpu_usage(self) -> str:
        pass

    def get_memory_usage(self) -> str:
        pass

    def bar(self, percent, char='#', blank_char=' ') -> str:
        return bar(self.bar_width, percent, char, blank_char)


class WindowsShellPrinter(Printer):
    def __init__(self, printable_objs: Iterable, interval=0.1, show_usage=False):
        Printer.__init__(self, printable_objs, interval=interval, show_usage=show_usage)

    def init_phase(self):
        os.system('cls')

    def get_cpu_usage(self):
        cmd = ''
        with os.popen(cmd, 'r') as f:
            pass

    def get_memory_usage(self):
        cmd = ''
        with os.popen(cmd, 'r') as f:
            pass


class LinuxShellPrinter(Printer):
    def __init__(self, printable_objs: Iterable, interval=0.1, show_usage=False):
        Printer.__init__(self, printable_objs, interval=interval, show_usage=show_usage)

    def init_phase(self):
        os.system('clear')

    def clean_screen(self):
        # os.system('clear')
        print("\033[H\033[J", end='')
        # print('\n' * 100)

    def get_cpu_usage(self) -> str:
        # cpu user nice system idle iowait ...
        # grep 'cpu ' /proc/stat | awk '{print ($2+$4) / ($2+$4+$5) * 100}'
        cmd = r"grep 'cpu ' /proc/stat | awk '{print ($2+$4) / ($2+$4+$5) * 100}' "
        try:
            with os.popen(cmd, 'r') as f:
                cpu_usage = f.readline()
            percent = round(float(cpu_usage))
        except Exception as E:
            return 'Fail to get Memory usage %s' % E.args[0]

        return self.bar(percent) + ' CPU'

    def get_memory_usage(self) -> str:
        # free -t -m | grep 'Mem\|Swap' | awk '{print $2} {print $3}'
        cmd = r"free -t -m | grep 'Mem\|Swap' | awk '{print $2} {print $3}'"
        try:
            with os.popen(cmd, 'r') as f:
                mem_total, mem_used, swap_total, swap_used = f.readlines()
            mem_total = round(float(mem_total))
            mem_used = round(float(mem_used))
            swap_total = round(float(swap_total))
            swap_used = round(float(swap_used))
        except Exception as E:
            return 'Fail to get Memory usage %s' % E.args[0]

        return '%s\n%s' % (
            self.bar(mem_used / mem_total * 100) + ' %dMb / %dMb Mem' % (mem_used, mem_total),
            self.bar(swap_used / swap_total * 100) + ' %dMb / %dMb Swap' % (swap_used, swap_total)
        )


class ShellPrinter(RepeatTimer):
    def __new__(cls, *args, **kwargs):
        if sys.platform.startswith('linux'):
            return LinuxShellPrinter(printable_objs=args, interval=0.2, show_usage=True)
        return WindowsShellPrinter(printable_objs=args, interval=0.2, show_usage=True)
