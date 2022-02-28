import sys
from pathlib import Path

__CURRENT_DIR = Path.cwd()
if (__CURRENT_DIR / 'src').is_dir():
    sys.path.append(str(__CURRENT_DIR))
    print(sys.path)
else:
    sys.path.append(str(__CURRENT_DIR.parent))
    print(sys.path)

from src.ShellPrinter import LinuxShellPrinter
from time import sleep

if __name__ == '__main__':
    printer = LinuxShellPrinter((), interval=0.2, show_usage=True)
    try:
        printer.start()
        sleep(20)
    except Exception as E:
        print(E.args)
    finally:
        printer.close()
        printer.join()
