import os
import sys
from .RepeatTimer import RepeatTimer


class ShellPrinter(RepeatTimer):
    def __init__(self, *printable_objs):
        RepeatTimer.__init__(self, interval=0.1)
        self.objs = printable_objs

    def execute_phase(self):
        if sys.platform.startswith('win'):
            os.system('cls')
        else:
            os.system('clear')
        for obj in self.objs:
            print(obj)

    def close_phase(self):
        del self.objs
