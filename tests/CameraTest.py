import sys
from pathlib import Path

__CURRENT_DIR = Path.cwd()
if (__CURRENT_DIR / 'src').is_dir():
    sys.path.append(str(__CURRENT_DIR))
    print(sys.path)
else:
    sys.path.append(str(__CURRENT_DIR.parent))
    print(sys.path)
from src import Camera2
from src import ShellPrinter
from time import sleep

if __name__ == '__main__':
    camera = Camera2()
    printer = ShellPrinter(camera)
    try:
        camera.start()
        printer.start()
        sleep(100)
        camera.close()
        printer.close()
    except Exception:
        pass
    finally:
        camera.close()
        printer.close()
        camera.join()
        printer.join()
