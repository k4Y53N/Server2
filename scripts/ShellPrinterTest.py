from nanoServer.ShellPrinter import LinuxShellPrinter
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
