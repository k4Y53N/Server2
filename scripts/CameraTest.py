from nanoServer.Camera import Camera
from nanoServer.ShellPrinter import ShellPrinter
from time import sleep

if __name__ == '__main__':
    camera = Camera()
    printer = ShellPrinter(camera)
    try:
        camera.start()
        printer.start()
        sleep(5)
        camera.set_quality(500, 500)
        sleep(55)
        camera.close()
        printer.close()
    except Exception:
        pass
    finally:
        camera.close()
        printer.close()
        camera.join()
        printer.join()
