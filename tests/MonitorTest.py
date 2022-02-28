import sys
from pathlib import Path

__CURRENT_DIR = Path.cwd()
if (__CURRENT_DIR / 'src').is_dir():
    sys.path.append(str(__CURRENT_DIR))
    print(sys.path)
else:
    sys.path.append(str(__CURRENT_DIR.parent))
    print(sys.path)
from time import sleep
from src.Monitor import Monitor

if __name__ == '__main__':

    m = Monitor()
    try:
        m.start()
        m.set_row_string(0, 'hello')
        sleep(2)
        m.set_row_string(1, 'python')
        sleep(20)
        m.close()
        m.join()
    except KeyboardInterrupt:
        m.close()
