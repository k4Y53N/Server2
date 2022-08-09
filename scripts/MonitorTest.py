from time import sleep
from nanoServer.Monitor import Monitor

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
