import os
import sys
from .RepeatTimer import RepeatTimer
from typing import Iterable


class Printer(RepeatTimer):
    def __init__(self, printable_objs: Iterable, interval=0.1, show_usage=False):
        RepeatTimer.__init__(self, interval=interval)
        self.show_usage = show_usage
        self.objs = printable_objs

    def execute_phase(self):
        self.clean_screen()
        if self.show_usage:
            print(self.get_cpu_usage())
            print(self.get_memory_usage())
        for obj in self.objs:
            print(obj)

    def close_phase(self):
        del self.objs

    def set_show_usage(self, show_usage: bool):
        self.show_usage = show_usage

    def clean_screen(self):
        pass

    def get_cpu_usage(self):
        pass

    def get_memory_usage(self):
        pass


class WindowsShellPrinter(Printer):
    def __init__(self, printable_objs: Iterable, interval=0.1, show_usage=False):
        Printer.__init__(self, printable_objs, interval=interval, show_usage=show_usage)

    def clean_screen(self):
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

    def clean_screen(self):
        os.system('clear')

    def get_cpu_usage(self):
        # cpu user nice system idle iowait ...
        # grep 'cpu ' /proc/stat | awk '{print ($2+$4) / ($2+$4+$5) * 100}'
        cmd = r"grep 'cpu ' /proc/stat | awk '{print ($2+$4) / ($2+$4+$5) * 100}' "
        with os.popen(cmd, 'r') as f:
            cpu_usage = f.readline()
        try:
            cpu_usage = str(round(float(cpu_usage), 2))
            return cpu_usage
        except ValueError as e:
            return '0.00%'

    def get_memory_usage(self):
        pass


class ShellPrinter(RepeatTimer):
    def __init__(self, *printable_objs):
        RepeatTimer.__init__(self, interval=0.1)
        self.objs = printable_objs

    def execute_phase(self):
        if sys.platform.startswith('win'):
            os.system('cls')
        else:
            print("\033[H\033[J", end="")
        for obj in self.objs:
            print(obj)

    def close_phase(self):
        del self.objs
