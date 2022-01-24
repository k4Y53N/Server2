from unit import Servo
from unit import Monitor
from time import sleep

if __name__ == '__main__':
    m = Monitor()
    s = Servo()
    try:
        s.start()
        m.start()
        m.set_row_string(0, 'Servo start')
        sleep(5)
        m.set_row_string(1, 'Servo change')
        s.set(0.8, 75)
        sleep(2)
        print('close')
        m.close()
        s.close()
    except KeyboardInterrupt:
        m.close()
        s.close()

